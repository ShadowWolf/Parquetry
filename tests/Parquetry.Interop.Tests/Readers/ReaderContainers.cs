using System.Globalization;
using System.Net;
using System.Net.Http.Headers;
using System.Text.Json;
using DotNet.Testcontainers.Builders;
using DotNet.Testcontainers.Containers;
using Xunit;

namespace Parquetry.Interop.Tests.Readers;

/// <summary>
/// Starts the reader containers once for the whole test run and sends files
/// to them. There are three containers: one for pyarrow, Polars, and DuckDB,
/// one for Spark 3.5, and one for the current Spark 4.x. Each runs the HTTP
/// server in Containers/reader_server.py.
/// </summary>
/// <remarks>
/// The images are built from the Dockerfiles in the Containers folder, which
/// the build copies beside the test assembly. They keep fixed names and are
/// not deleted after a run, so that Docker reuses their layers the next time.
/// </remarks>
public sealed class ReaderContainers : IAsyncLifetime
{
    private const int ContainerPort = 8080;

    private static readonly string ContainersDirectory = Path.Combine(AppContext.BaseDirectory, "Containers");

    private readonly HttpClient _http = new();
    private readonly List<IContainer> _containers = [];
    private readonly Dictionary<string, Uri> _readUrls = [];
    private Uri? _pythonBaseUrl;

    /// <summary>
    /// Builds the images and starts the containers. A container counts as
    /// started when its health check answers.
    /// </summary>
    public async ValueTask InitializeAsync()
    {
        var python = StartAsync("python.Dockerfile", "parquetry-reader-python");
        var spark35 = StartAsync("spark-3.5.Dockerfile", "parquetry-reader-spark-3.5");
        var spark4 = StartAsync("spark-4.Dockerfile", "parquetry-reader-spark-4");

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
        _readUrls[ReaderNames.PyArrow] = new Uri(_pythonBaseUrl, "read/pyarrow");
        _readUrls[ReaderNames.Polars] = new Uri(_pythonBaseUrl, "read/polars");
        _readUrls[ReaderNames.DuckDb] = new Uri(_pythonBaseUrl, "read/duckdb");
        _readUrls[ReaderNames.Spark35] = new Uri(BaseUrl(spark35.Result), "read/spark");
        _readUrls[ReaderNames.Spark4] = new Uri(BaseUrl(spark4.Result), "read/spark");
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
    /// Gets a file that the pyarrow container writes, by name.
    /// </summary>
    public async Task<byte[]> GetFileAsync(string name, CancellationToken cancellationToken)
    {
        using var response = await _http.GetAsync(new Uri(_pythonBaseUrl!, "files/" + name), cancellationToken);
        var body = await response.Content.ReadAsByteArrayAsync(cancellationToken);
        if (response.StatusCode != HttpStatusCode.OK)
        {
            throw new InvalidOperationException(
                $"The pyarrow container answered {(int)response.StatusCode} for the file '{name}': {System.Text.Encoding.UTF8.GetString(body)}");
        }

        return body;
    }

    /// <summary>
    /// Sends a file to a reader and returns what the reader saw, or the
    /// reader's error if it could not read the file.
    /// </summary>
    /// <exception cref="InvalidOperationException">
    /// The reader container itself failed. That is a fault in the test setup
    /// and says nothing about the file.
    /// </exception>
    public async Task<ReadResult> ReadAsync(string reader, ReadOnlyMemory<byte> file, CancellationToken cancellationToken)
    {
        using var content = new ReadOnlyMemoryContent(file);
        content.Headers.ContentType = new MediaTypeHeaderValue("application/octet-stream");

        using var response = await _http.PostAsync(_readUrls[reader], content, cancellationToken);
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

    private static async Task<IContainer> StartAsync(string dockerfile, string imageName)
    {
        var image = new ImageFromDockerfileBuilder()
            .WithDockerfileDirectory(ContainersDirectory)
            .WithDockerfile(dockerfile)
            .WithName(imageName + ":local")
            .WithCleanUp(false)
            .Build();
        await image.CreateAsync();

        var container = new ContainerBuilder(image)
            .WithPortBinding(ContainerPort, assignRandomHostPort: true)
            .WithWaitStrategy(Wait.ForUnixContainer().UntilHttpRequestIsSucceeded(
                request => request.ForPort(ContainerPort).ForPath("/health")))
            .Build();
        try
        {
            await container.StartAsync();
        }
        catch
        {
            await container.DisposeAsync();
            throw;
        }

        return container;
    }

    private static Uri BaseUrl(IContainer container) =>
        new UriBuilder("http", container.Hostname, container.GetMappedPublicPort(ContainerPort)).Uri;

    private static ReaderTable ParseTable(JsonElement root)
    {
        var columns = root.GetProperty("columns").EnumerateArray()
            .Select(column => new ReaderColumn(
                column.GetProperty("name").GetString()!,
                ParseKind(column.GetProperty("kind").GetString()!),
                column.GetProperty("nativeType").GetString()!))
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
