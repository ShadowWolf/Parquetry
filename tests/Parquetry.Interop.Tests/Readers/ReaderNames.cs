using Xunit;

namespace Parquetry.Interop.Tests.Readers;

/// <summary>
/// The names a test uses to say which reader gets a file.
/// <see cref="ReaderContainers"/> turns each name into a container and an
/// address in it. The two Spark names go to different containers, and
/// inside each container the reader is called <c>spark</c>.
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
    /// Not a reader. The Python container answers a file sent to this name
    /// the way it answers when its own code fails. One test uses it to check
    /// that such a failure is not taken for a reader rejecting the file.
    /// </summary>
    public const string SetupFault = "setup-fault";

    /// <summary>
    /// Every reader, as data for a test that runs once per reader.
    /// </summary>
    public static TheoryData<string> All => [PyArrow, Polars, DuckDb, Spark35, Spark4];
}
