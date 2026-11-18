"""The reader container for Spark. The same script runs in each Spark image.

Spark reads with its default settings, apart from turning off its web
interface. A test that needs a Spark setting changed says so itself.
"""
from pyspark.sql import SparkSession

from reader_server import serve

SPARK_KINDS = {
    "boolean": "bool",
    "int": "int32",
    "bigint": "int64",
    "double": "float64",
    "string": "string",
}

spark = SparkSession.builder.appName("parquetry-reader").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")


def read_spark(path):
    frame = spark.read.parquet("file://" + path)
    columns = [
        (
            field.name,
            field.dataType.simpleString(),
            SPARK_KINDS.get(field.dataType.simpleString(), "unknown"),
        )
        for field in frame.schema.fields
    ]
    # The test files are small enough that Spark reads each in one task, so
    # the rows come back in file order.
    return columns, [tuple(row) for row in frame.collect()]


if __name__ == "__main__":
    # One query before the server starts, so that /health answers only when
    # Spark can run a job.
    spark.range(1).collect()
    serve(readers={"spark": read_spark}, versions={"spark": spark.version})
