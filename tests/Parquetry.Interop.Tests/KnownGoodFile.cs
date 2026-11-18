using Parquetry.Interop.Tests.Readers;

namespace Parquetry.Interop.Tests;

/// <summary>
/// The contents of the known-good file. pyarrow writes the file in its
/// container, in the function <c>known_good_file</c> of
/// Containers/python_readers.py. The values here must match the values
/// there.
/// </summary>
public static class KnownGoodFile
{
    /// <summary>The name the pyarrow container serves the file under.</summary>
    public const string Name = "known-good.parquet";

    /// <summary>The columns of the file.</summary>
    public static readonly (string Name, ColumnKind Kind)[] Columns =
    [
        ("id", ColumnKind.Int64),
        ("flag", ColumnKind.Bool),
        ("count", ColumnKind.Int32),
        ("ratio", ColumnKind.Float64),
        ("name", ColumnKind.String),
    ];

    /// <summary>
    /// The rows of the file. They include a null in every column that allows
    /// one, the smallest and largest 32-bit integers, NaN, negative zero, an
    /// empty string, and text with characters of two, three, and four bytes
    /// in UTF-8.
    /// </summary>
    public static readonly object?[][] Rows =
    [
        [1L, true, 10, 1.5, "alpha"],
        [2L, false, null, double.NaN, ""],
        [3L, null, int.MinValue, null, "Zoë 東京 \U0001f40e"],
        [4L, true, int.MaxValue, -0.0, null],
    ];
}
