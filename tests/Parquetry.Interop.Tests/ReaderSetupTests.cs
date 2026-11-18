using Parquetry.Interop.Tests.Readers;
using Xunit;

namespace Parquetry.Interop.Tests;

/// <summary>
/// Checks the reader containers themselves, using a file that pyarrow wrote.
/// These tests are about the test setup and not about the library. Every
/// other reader test relies on what they show.
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

        // The error has to be about the file. Every reader's message for a
        // file without its footer mentions the footer, the magic bytes at
        // the end of a Parquet file, or their value, PAR1. An error from the
        // reader's library about something else, such as a missing module,
        // would not.
        Assert.Matches("(?i)footer|magic|PAR1", result.Error);
    }

    /// <summary>
    /// A column of a type the setup has no common name for comes back
    /// marked as unknown, with a value, and not as an error. The file has a
    /// date column and a column of timestamps with a time zone.
    /// </summary>
    [Theory]
    [MemberData(nameof(ReaderNames.All), MemberType = typeof(ReaderNames))]
    public async Task Reader_returns_an_unknown_type_as_unknown(string reader)
    {
        var cancellationToken = TestContext.Current.CancellationToken;
        var file = await readers.GetFileAsync("unknown-types.parquet", cancellationToken);

        var result = await readers.ReadAsync(reader, file, cancellationToken);

        Assert.NotNull(result.Table);
        Assert.Equal(["day", "at"], result.Table.Columns.Select(column => column.Name));
        Assert.All(result.Table.Columns, column => Assert.Equal(ColumnKind.Unknown, column.Kind));
        var row = Assert.Single(result.Table.Rows);
        Assert.All(row, value => Assert.False(string.IsNullOrWhiteSpace(value as string)));
    }

    /// <summary>
    /// A failure in the reader container's own code is raised as an error of
    /// the test setup. It is not returned as a reader's error, which would
    /// let a test that expects a reader to reject a file pass because the
    /// setup broke.
    /// </summary>
    [Fact]
    public async Task Fault_in_the_setup_is_not_reported_as_a_reader_error()
    {
        var cancellationToken = TestContext.Current.CancellationToken;
        var file = await readers.GetFileAsync(KnownGoodFile.Name, cancellationToken);

        var error = await Assert.ThrowsAsync<InvalidOperationException>(
            () => readers.ReadAsync(ReaderNames.SetupFault, file, cancellationToken));

        Assert.Contains("answered 500", error.Message, StringComparison.Ordinal);
    }
}
