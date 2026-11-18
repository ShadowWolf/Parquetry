using Xunit;

namespace Parquetry.Interop.Tests.Readers;

/// <summary>
/// The names of the readers that the tests can send a file to.
/// </summary>
public static class ReaderNames
{
    /// <summary>pyarrow, the library this project uses as its reference.</summary>
    public const string PyArrow = "pyarrow";

    /// <summary>Polars, using its own Parquet reader.</summary>
    public const string Polars = "polars";

    /// <summary>DuckDB.</summary>
    public const string DuckDb = "duckdb";

    /// <summary>Spark 3.5.</summary>
    public const string Spark35 = "spark-3.5";

    /// <summary>The current Spark 4.x release.</summary>
    public const string Spark4 = "spark-4";

    /// <summary>
    /// Every reader, as data for a test that runs once per reader.
    /// </summary>
    public static TheoryData<string> All => [PyArrow, Polars, DuckDb, Spark35, Spark4];
}
