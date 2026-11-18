using Parquetry.Interop.Tests.Readers;

namespace Parquetry.Interop.Tests;

/// <summary>
/// The contents of the known-good file. pyarrow writes the file in the
/// Python container, in the function <c>known_good_file</c> of
/// Containers/python_readers.py. The values here are a second copy of the
/// values there. If the two differ, the test
/// <c>Reader_returns_what_pyarrow_wrote</c> fails.
/// </summary>
public static class KnownGoodFile
{
    /// <summary>The name the Python container serves the file under.</summary>
    public const string Name = "known-good.parquet";

    /// <summary>
    /// The columns of the file. <c>id</c> is declared as not holding nulls.
    /// </summary>
    public static readonly ExpectedColumn[] Columns =
    [
        new("id", ColumnKind.Int64, Nullable: false),
        new("flag", ColumnKind.Bool, Nullable: true),
        new("count", ColumnKind.Int32, Nullable: true),
        new("ratio", ColumnKind.Float64, Nullable: true),
        new("name", ColumnKind.String, Nullable: true),
    ];

    /// <summary>
    /// The rows of the file. They hold the values that a careless setup
    /// would get wrong: a null in every column that allows one, a 64-bit
    /// integer that a JSON number cannot hold exactly, the smallest and
    /// largest 32-bit and 64-bit integers, NaN, negative zero, both
    /// infinities, an empty string, a string with a line break, and text
    /// with characters of two, three, and four bytes in UTF-8.
    /// </summary>
    public static readonly object?[][] Rows =
    [
        [1L, true, 10, 1.5, "alpha"],
        [2L, false, null, double.NaN, ""],
        [3L, null, int.MinValue, null, "Zoë 東京 \U0001f40e"],
        [9007199254740993L, true, int.MaxValue, -0.0, null],
        [long.MinValue, false, 0, double.PositiveInfinity, "two\nlines"],
        [long.MaxValue, null, -1, double.NegativeInfinity, "beta"],
    ];
}
