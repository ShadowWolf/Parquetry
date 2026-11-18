using System.Globalization;
using System.Net;
using System.Net.Http.Headers;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using DotNet.Testcontainers.Builders;
using DotNet.Testcontainers.Containers;
using Parquetry.Interop.Tests.Readers;
using Xunit;

// Makes xUnit create one ReaderContainers for the whole test project and
// hand it to every test class that asks for it in its constructor. This is
// what starts the containers once per test run and not once per test.
[assembly: AssemblyFixture(typeof(ReaderContainers))]

namespace Parquetry.Interop.Tests.Readers;

/// <summary>
/// Starts the reader containers once for the whole test run and sends files
/// to them. There are three containers: the Python container, which holds
/// pyarrow, Polars, and DuckDB, one for Spark 3.5, and one for the current
/// Spark 4.x. Each runs the HTTP server in Containers/reader_server.py.
/// </summary>
/// <remarks>
/// The images are built from the Dockerfiles in the Containers folder, which
/// the build copies beside the test assembly. An image's tag is a hash of
/// the files in that folder, so two checkouts with different files never
/// share an image. Images are not deleted after a run, so that Docker reuses
/// their layers the next time.
/// </remarks>
public sealed class ReaderContainers : IAsyncLifetime
{
    private const int ContainerPort = 8080;

    /// <summary>
    /// How long a container may take to answer its health check. Starting
    /// Spark takes a few seconds. The limit is far above that so that a slow
    /// machine passes, and it exists so that a container that never becomes
    /// ready fails the run and does not hang it.
    /// </summary>
    private static readonly TimeSpan StartTimeout = TimeSpan.FromMinutes(3);

    private static readonly string ContainersDirectory = Path.Combine(AppContext.BaseDirectory, "Containers");

    private readonly HttpClient _http = new();
    private readonly List<IContainer> _containers = [];
    private readonly Dictionary<string, (IContainer Container, Uri Url)> _readers = [];
    private Uri? _pythonBaseUrl;

    /// <summary>
    /// Builds the images and starts the containers. A container counts as
    /// started when its health check answers.
    /// </summary>
    public async ValueTask InitializeAsync()
    {
        var tag = HashOfContainerFiles();
        var python = StartAsync("python/Dockerfile", $"parquetry-reader-python:{tag}");
        var spark35 = StartAsync("spark-3.5/Dockerfile", $"parquetry-reader-spark-3.5:{tag}");
        var spark4 = StartAsync("spark-4/Dockerfile", $"parquetry-reader-spark-4:{tag}");

        // Each start is awaited even if another has failed, so that every
        // container that did start is recorded and gets stopped.
        try
        {
            await Task.WhenAll(python, spark35, spark4);
        }
        finally
        {
            foreach (var start in new[] { python, spark35, spark4 })
            {
                if (start.IsCompletedSuccessfully)
                {
                    _containers.Add(start.Result);
                }
            }
        }

        _pythonBaseUrl = BaseUrl(python.Result);
        foreach (var name in new[] { ReaderNames.PyArrow, ReaderNames.Polars, ReaderNames.DuckDb, ReaderNames.SetupFault })
        {
            _readers[name] = (python.Result, new Uri(_pythonBaseUrl, "read/" + name));
        }

        _readers[ReaderNames.Spark35] = (spark35.Result, new Uri(BaseUrl(spark35.Result), "read/spark"));
        _readers[ReaderNames.Spark4] = (spark4.Result, new Uri(BaseUrl(spark4.Result), "read/spark"));
    }

    /// <summary>
    /// Stops and removes the containers.
    /// </summary>
    public async ValueTask DisposeAsync()
    {
        foreach (var container in _containers)
        {
            await container.DisposeAsync();
        }

        _http.Dispose();
    }

    /// <summary>
    /// Gets a file that pyarrow writes in the Python container, by name.
    /// </summary>
    public async Task<byte[]> GetFileAsync(string name, CancellationToken cancellationToken)
    {
        using var response = await _http.GetAsync(new Uri(_pythonBaseUrl!, "files/" + name), cancellationToken);
        var body = await response.Content.ReadAsByteArrayAsync(cancellationToken);
        if (response.StatusCode != HttpStatusCode.OK)
        {
            throw new InvalidOperationException(
                $"The Python container answered {(int)response.StatusCode} for the file '{name}': {Encoding.UTF8.GetString(body)}");
        }

        return body;
    }

    /// <summary>
    /// Sends a file to a reader and returns what the reader saw, or the
    /// reader's error if it could not read the file.
    /// </summary>
    /// <exception cref="InvalidOperationException">
    /// The reader container failed or did not answer. That is a fault in the
    /// test setup, or a reader that crashed, and it is never returned as a
    /// reader's error.
    /// </exception>
    public async Task<ReadResult> ReadAsync(string reader, ReadOnlyMemory<byte> file, CancellationToken cancellationToken)
    {
        var (container, url) = _readers[reader];
        using var content = new ReadOnlyMemoryContent(file);
        content.Headers.ContentType = new MediaTypeHeaderValue("application/octet-stream");

        HttpResponseMessage response;
        try
        {
            response = await _http.PostAsync(url, content, cancellationToken);
        }
        catch (HttpRequestException error)
        {
            // A reader that crashes in native code takes the server down with
            // it, and the request ends without an answer.
            throw new InvalidOperationException(
                $"The container for the reader '{reader}' did not answer. The reader may have crashed on this file. " +
                $"The container's output: {await OutputOf(container)}",
                error);
        }

        using (response)
        {
            var body = await response.Content.ReadAsStringAsync(cancellationToken);
            switch ((int)response.StatusCode)
            {
                case 200:
                    using (var document = JsonDocument.Parse(body))
                    {
                        return new ReadResult(ParseTable(document.RootElement), null);
                    }

                case 422:
                    using (var document = JsonDocument.Parse(body))
                    {
                        return new ReadResult(null, document.RootElement.GetProperty("error").GetString());
                    }

                default:
                    throw new InvalidOperationException(
                        $"The container for the reader '{reader}' answered {(int)response.StatusCode}: {body}");
            }
        }
    }

    private static async Task<IContainer> StartAsync(string dockerfile, string imageName)
    {
        var image = new ImageFromDockerfileBuilder()
            .WithDockerfileDirectory(ContainersDirectory)
            .WithDockerfile(dockerfile)
            .WithName(imageName)
            .WithCleanUp(false)
            .Build();
        await image.CreateAsync();

        var container = new ContainerBuilder(image)
            .WithPortBinding(ContainerPort, assignRandomHostPort: true)
            // Publishes the port on this machine's loopback address only. By
            // default Docker publishes it on every network interface, which
            // would let other machines send files to the reader.
            .WithCreateParameterModifier(parameters =>
            {
                var bindings = parameters.HostConfig?.PortBindings?.Values.SelectMany(list => list).ToList() ?? [];
                if (bindings.Count == 0)
                {
                    // Without this, a change in Testcontainers that moved the
                    // bindings elsewhere would publish the port on every
                    // interface again and nothing would show it.
                    throw new InvalidOperationException("The container has no port binding to restrict to the loopback address.");
                }

                foreach (var binding in bindings)
                {
                    binding.HostIP = "127.0.0.1";
                }
            })
            .WithWaitStrategy(Wait.ForUnixContainer().UntilHttpRequestIsSucceeded(
                request => request.ForPort(ContainerPort).ForPath("/health"),
                wait => wait.WithTimeout(StartTimeout)))
            .Build();
        try
        {
            await container.StartAsync();
        }
        catch (Exception error)
        {
            var output = await OutputOf(container);
            await container.DisposeAsync();
            throw new InvalidOperationException(
                $"The reader container built from Containers/{dockerfile} did not become ready within {StartTimeout.TotalMinutes} minutes. " +
                $"Its output: {output}",
                error);
        }

        return container;
    }

    /// <summary>
    /// Returns what a container has written to its output, for an error
    /// message. If the output cannot be read, says so and does not throw.
    /// </summary>
    private static async Task<string> OutputOf(IContainer container)
    {
        try
        {
            var (stdout, stderr) = await container.GetLogsAsync();
            var output = (stdout + stderr).Trim();
            return output.Length == 0 ? "(none)" : output;
        }
        catch (Exception error)
        {
            return $"(could not be read: {error.Message})";
        }
    }

    /// <summary>
    /// A short hash of the name and contents of every file in the Containers
    /// folder, used as the tag of the images built from it.
    /// </summary>
    private static string HashOfContainerFiles()
    {
        using var hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
        foreach (var path in Directory.EnumerateFiles(ContainersDirectory, "*", SearchOption.AllDirectories).Order(StringComparer.Ordinal))
        {
            var name = Path.GetRelativePath(ContainersDirectory, path).Replace('\\', '/');
            hash.AppendData(Encoding.UTF8.GetBytes(name + "\n"));
            hash.AppendData(File.ReadAllBytes(path));
        }

        return Convert.ToHexStringLower(hash.GetHashAndReset())[..12];
    }

    private static Uri BaseUrl(IContainer container) =>
        new UriBuilder("http", container.Hostname, container.GetMappedPublicPort(ContainerPort)).Uri;

    private static ReaderTable ParseTable(JsonElement root)
    {
        var columns = root.GetProperty("columns").EnumerateArray()
            .Select(column => new ReaderColumn(
                column.GetProperty("name").GetString()!,
                ParseKind(column.GetProperty("kind").GetString()!),
                column.GetProperty("nativeType").GetString()!,
                column.GetProperty("nullable").ValueKind switch
                {
                    JsonValueKind.True => true,
                    JsonValueKind.False => false,
                    _ => null,
                }))
            .ToArray();

        var rows = root.GetProperty("rows").EnumerateArray()
            .Select(row => (IReadOnlyList<object?>)row.EnumerateArray()
                .Select((value, index) => ParseValue(value, columns[index].Kind))
                .ToArray())
            .ToArray();

        return new ReaderTable(columns, rows);
    }

    private static ColumnKind ParseKind(string kind) => kind switch
    {
        "bool" => ColumnKind.Bool,
        "int32" => ColumnKind.Int32,
        "int64" => ColumnKind.Int64,
        "float64" => ColumnKind.Float64,
        "string" => ColumnKind.String,
        _ => ColumnKind.Unknown,
    };

    /// <summary>
    /// Turns one value from the container's response into a .NET value. The
    /// container sends every value as null or a string. The forms are listed
    /// in Containers/reader_server.py.
    /// </summary>
    private static object? ParseValue(JsonElement value, ColumnKind kind)
    {
        if (value.ValueKind == JsonValueKind.Null)
        {
            return null;
        }

        var text = value.GetString()!;
        return kind switch
        {
            ColumnKind.Bool => text switch
            {
                "true" => true,
                "false" => false,
                _ => throw new FormatException($"'{text}' is not a bool value."),
            },
            ColumnKind.Int32 => int.Parse(text, CultureInfo.InvariantCulture),
            ColumnKind.Int64 => long.Parse(text, CultureInfo.InvariantCulture),
            ColumnKind.Float64 => text switch
            {
                "nan" => double.NaN,
                "inf" => double.PositiveInfinity,
                "-inf" => double.NegativeInfinity,
                _ => double.Parse(text, NumberStyles.Float, CultureInfo.InvariantCulture),
            },
            _ => text,
        };
    }
}
