using Parquetry.Interop.Tests.Readers;
using Xunit;

[assembly: AssemblyFixture(typeof(ReaderContainers))]

namespace Parquetry.Interop.Tests;

/// <summary>
/// Shows that the reader containers work, using a file that pyarrow wrote.
/// The library writes no files yet, so these tests are about the test setup
/// and not about the library.
/// </summary>
public class ReaderSetupTests(ReaderContainers readers)
{
    /// <summary>
    /// Every reader loads the known-good file and returns the columns and
    /// values that were written.
    /// </summary>
    [Theory]
    [MemberData(nameof(ReaderNames.All), MemberType = typeof(ReaderNames))]
    public async Task Reader_returns_what_pyarrow_wrote(string reader)
    {
        var cancellationToken = TestContext.Current.CancellationToken;
        var file = await readers.GetFileAsync(KnownGoodFile.Name, cancellationToken);

        var result = await readers.ReadAsync(reader, file, cancellationToken);

        ReaderAssert.TableEquals(KnownGoodFile.Columns, KnownGoodFile.Rows, result);
    }

    /// <summary>
    /// A reader that cannot read a file reports an error. Without this, a
    /// test of a broken file could pass because the setup returned an empty
    /// table. The file here is the known-good file with its second half,
    /// which holds the footer, cut off.
    /// </summary>
    [Theory]
    [MemberData(nameof(ReaderNames.All), MemberType = typeof(ReaderNames))]
    public async Task Reader_reports_an_error_for_a_truncated_file(string reader)
    {
        var cancellationToken = TestContext.Current.CancellationToken;
        var file = await readers.GetFileAsync(KnownGoodFile.Name, cancellationToken);
        var truncated = file.AsMemory(0, file.Length / 2);

        var result = await readers.ReadAsync(reader, truncated, cancellationToken);

        Assert.Null(result.Table);
        Assert.False(string.IsNullOrWhiteSpace(result.Error));
    }
}
