"""Writes the files that Spark is asked to read, using pyarrow's default settings."""
import decimal
import json
import sys

import pyarrow as pa
import pyarrow.parquet as pq

out = sys.argv[1]
decimal.getcontext().prec = 60
columns = {}
expected = {}
for precision in range(1, 39):
    scale = precision // 3
    largest = decimal.Decimal(10 ** precision - 1).scaleb(-scale)
    values = [largest, -largest, decimal.Decimal(0).scaleb(-scale), decimal.Decimal(1).scaleb(-scale), None]
    name = f"p{precision}"
    columns[name] = pa.array(values, type=pa.decimal128(precision, scale))
    expected[name] = {"precision": precision, "scale": scale,
                      "values": [None if v is None else format(v, "f") for v in values]}
columns["u8"] = pa.array([0, 200, 255, 7, None], type=pa.uint8())
expected["u8"] = {"values": ["0", "200", "255", "7", None]}
table = pa.table(columns)
pq.write_table(table, f"{out}/decimals_default.parquet")
pq.write_table(table, f"{out}/decimals_as_integers.parquet", store_decimal_as_integer=True)
json.dump(expected, open(f"{out}/expected.json", "w"))
schema = pq.ParquetFile(f"{out}/decimals_default.parquet").schema
print("pyarrow", pa.__version__)
print("default file:", ", ".join(f"p{i + 1}={schema.column(i).physical_type}({schema.column(i).length})" for i in (0, 8, 17, 28, 37)),
      "| u8:", schema.column(38).logical_type)
