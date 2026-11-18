"""The reader container for Spark. The same script runs in each Spark image.

Spark reads with its default settings. The only settings changed are the two
on the command line in the Dockerfile, which turn off Spark's web interface
and run it with one worker thread. Neither changes how a file is read. No
request can change a Spark setting. A test that needs one changed has to add
a request for it first.
"""
from py4j.protocol import Py4JJavaError
from pyspark.errors import PySparkException
from pyspark.sql import SparkSession

from reader_server import serve

SPARK_KINDS = {
    "boolean": "bool",
    "int": "int32",
    "bigint": "int64",
    "double": "float64",
    "string": "string",
}

# The exceptions that reach Python when Spark cannot read a file.
SPARK_ERRORS = (Py4JJavaError, PySparkException)

spark = SparkSession.builder.appName("parquetry-reader").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")


def read_spark(path):
    frame = spark.read.parquet("file://" + path)
    # Spark marks every column it reads from a file as nullable, whatever the
    # file says, so it does not tell the test whether a column is required.
    columns = [
        (
            field.name,
            field.dataType.simpleString(),
            SPARK_KINDS.get(field.dataType.simpleString(), "unknown"),
            None,
        )
        for field in frame.schema.fields
    ]
    # Spark returns rows in file order only when it reads the file in one
    # task. See "Row order" in docs/architecture/testing.md.
    return columns, [tuple(row) for row in frame.collect()]


if __name__ == "__main__":
    # One query before the server starts, so that /health answers only when
    # Spark can run a job.
    spark.range(1).collect()
    serve(readers={"spark": (read_spark, SPARK_ERRORS)}, versions={"spark": spark.version})
