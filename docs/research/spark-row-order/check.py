"""Reads the two test files with Spark and reports, for each, how many tasks
Spark used and whether the rows came back in file order.

Run with spark-submit, with the folder that holds the files as the argument.
"""
import sys

from pyspark.sql import SparkSession

folder = sys.argv[1]
spark = SparkSession.builder.getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

for name in ("small.parquet", "big.parquet"):
    frame = spark.read.parquet("file://" + folder + "/" + name)
    ids = [row[0] for row in frame.select("id").collect()]
    print(
        "RESULT",
        "spark", spark.version,
        "master", spark.sparkContext.master,
        "file", name,
        "tasks", frame.rdd.getNumPartitions(),
        "rows", len(ids),
        "in file order", ids == sorted(ids),
    )
