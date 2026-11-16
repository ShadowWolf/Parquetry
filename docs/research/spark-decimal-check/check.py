"""Reads the pyarrow-written files with Spark and compares every value with what was written."""
import json
import sys
from decimal import Decimal

from pyspark.sql import SparkSession
from pyspark.sql.types import DecimalType, ShortType

work = sys.argv[1]
expected = json.load(open(f"{work}/expected.json"))
spark = SparkSession.builder.master("local[2]").appName("check").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")
print("RESULT Spark", spark.version)
failures = 0
for file in ("decimals_default.parquet", "decimals_as_integers.parquet"):
    for vectorized in ("true", "false"):
        spark.conf.set("spark.sql.parquet.enableVectorizedReader", vectorized)
        label = f"{file}, vectorized reader {vectorized}"
        try:
            df = spark.read.parquet(f"{work}/{file}")
            rows = df.collect()
            problems = []
            for field in df.schema.fields:
                want = expected[field.name]
                if field.name == "u8":
                    if not isinstance(field.dataType, ShortType):
                        problems.append(f"u8 read as {field.dataType.simpleString()}")
                else:
                    t = field.dataType
                    if not (isinstance(t, DecimalType) and t.precision == want["precision"] and t.scale == want["scale"]):
                        problems.append(f"{field.name} read as {t.simpleString()}")
                got = [None if r[field.name] is None else Decimal(str(r[field.name])) for r in rows]
                wanted = [None if v is None else Decimal(v) for v in want["values"]]
                if got != wanted:
                    problems.append(f"{field.name} values {got} != {wanted}")
            if problems:
                failures += 1
                print(f"RESULT FAIL {label}: {problems[:3]}")
            else:
                print(f"RESULT PASS {label}: {len(df.schema.fields)} columns, {len(rows)} rows, all values equal")
        except Exception as e:
            failures += 1
            print(f"RESULT FAIL {label}: {type(e).__name__}: {str(e).splitlines()[0][:300]}")
print("RESULT u8 type:", spark.read.parquet(f"{work}/decimals_default.parquet").schema["u8"].dataType.simpleString())
print("RESULT failures:", failures)
spark.stop()
