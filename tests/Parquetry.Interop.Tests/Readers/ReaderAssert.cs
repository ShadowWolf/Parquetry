using System.Globalization;
using Xunit;

namespace Parquetry.Interop.Tests.Readers;

/// <summary>
/// Comparisons between what was written to a file and what a reader saw.
/// </summary>
public static class ReaderAssert
{
    /// <summary>
    /// Checks that a reader returned a table with the expected columns and
    /// rows, in order.
    /// </summary>
    /// <param name="expectedColumns">The name and kind of each column.</param>
    /// <param name="expectedRows">The rows, with values of the .NET types described on <see cref="ReaderTable"/>.</param>
    /// <param name="result">What the reader returned.</param>
    public static void TableEquals(
        IReadOnlyList<(string Name, ColumnKind Kind)> expectedColumns,
        IReadOnlyList<IReadOnlyList<object?>> expectedRows,
        ReadResult result)
    {
        if (result.Table is not { } table)
        {
            Assert.Fail($"The reader could not read the file: {result.Error}");
            return;
        }

        Assert.Equal(
            expectedColumns.Select(column => $"{column.Name}: {column.Kind}"),
            table.Columns.Select(column => $"{column.Name}: {column.Kind}"));

        Assert.Equal(expectedRows.Count, table.Rows.Count);
        for (var row = 0; row < expectedRows.Count; row++)
        {
            for (var column = 0; column < expectedColumns.Count; column++)
            {
                var expected = expectedRows[row][column];
                var actual = table.Rows[row][column];
                if (!ValueEquals(expected, actual))
                {
                    Assert.Fail(
                        $"Row {row}, column '{expectedColumns[column].Name}': expected {Describe(expected)}, " +
                        $"and the reader returned {Describe(actual)}.");
                }
            }
        }
    }

    /// <summary>
    /// Compares two values the way a file comparison needs. Any NaN equals
    /// any other NaN, and positive zero does not equal negative zero.
    /// </summary>
    private static bool ValueEquals(object? expected, object? actual)
    {
        if (expected is double left && actual is double right)
        {
            return (double.IsNaN(left) && double.IsNaN(right))
                || BitConverter.DoubleToInt64Bits(left) == BitConverter.DoubleToInt64Bits(right);
        }

        return Equals(expected, actual);
    }

    private static string Describe(object? value) => value switch
    {
        null => "null",
        string text => $"\"{text}\"",
        // The default text for negative zero is "-0", which is easy to misread.
        double number when number == 0 => double.IsNegative(number) ? "-0.0 (Double)" : "0.0 (Double)",
        IFormattable number => $"{number.ToString(null, CultureInfo.InvariantCulture)} ({value.GetType().Name})",
        _ => $"{value} ({value.GetType().Name})",
    };
}
