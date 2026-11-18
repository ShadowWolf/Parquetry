namespace Parquetry.Interop.Tests.Readers;

/// <summary>
/// The type of a column as a reader reported it, under a name that is the
/// same for every reader. The reader containers assign it. The names are
/// listed in Containers/reader_server.py.
/// </summary>
public enum ColumnKind
{
    /// <summary>A type the reader container has no common name for.</summary>
    Unknown,

    /// <summary>True or false.</summary>
    Bool,

    /// <summary>A signed 32-bit integer.</summary>
    Int32,

    /// <summary>A signed 64-bit integer.</summary>
    Int64,

    /// <summary>A 64-bit floating-point number.</summary>
    Float64,

    /// <summary>Text.</summary>
    String,
}
