"""Compares the size of a decimal column stored as fixed-length bytes and as an
integer, and prints the statistics pyarrow writes for a fixed-length decimal.

Run from any directory. It writes one file, t.parquet, to the current directory.
"""
import decimal
import os
import random
import sys

import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compact_thrift import read_footer  # noqa: E402

random.seed(1)
N = 1_000_000
D = decimal.Decimal
def size(arr, **opt):
    pq.write_table(pa.table({"v": arr}), "t.parquet", **opt)
    md = pq.ParquetFile("t.parquet").metadata
    return sum(md.row_group(i).column(0).total_compressed_size for i in range(md.num_row_groups))
cases = {
  "decimal(9,2), random over the full range": (pa.decimal128(9,2), [D(random.randint(-10**9+1, 10**9-1)).scaleb(-2) for _ in range(N)]),
  "decimal(9,2), amounts 0.00 to 999.99": (pa.decimal128(9,2), [D(random.randint(0, 99999)).scaleb(-2) for _ in range(N)]),
  "decimal(18,2), random over the full range": (pa.decimal128(18,2), [D(random.randint(-10**18+1, 10**18-1)).scaleb(-2) for _ in range(N)]),
  "decimal(18,2), amounts 0.00 to 99999.99": (pa.decimal128(18,2), [D(random.randint(0, 9999999)).scaleb(-2) for _ in range(N)]),
  "decimal(18,0), increasing by 1 (an id)": (pa.decimal128(18,0), [D(10**12 + i) for i in range(N)]),
  "decimal(12,2), amounts 0.00 to 99999.99": (pa.decimal128(12,2), [D(random.randint(0, 9999999)).scaleb(-2) for _ in range(N)]),
  "decimal(10,2), amounts 0.00 to 99999.99": (pa.decimal128(10,2), [D(random.randint(0, 9999999)).scaleb(-2) for _ in range(N)]),
}
print("pyarrow", pa.__version__, "| bytes in the column chunk(s), 1,000,000 values")
for label, (t, vals) in cases.items():
    arr = pa.array(vals, t)
    row = [label]
    for name, opt in (("default (dictionary, Snappy)", {}),
                      ("PLAIN, Snappy", {"use_dictionary": False}),
                      ("PLAIN, no compression", {"use_dictionary": False, "compression": "none"})):
        b = size(arr, **opt); i = size(arr, store_decimal_as_integer=True, **opt)
        row.append(f"{name}: bytes form {b:,} / integer form {i:,}{'  <-- integer smaller' if i < b else ''}")
    b = size(arr, use_dictionary=False, compression="zstd")
    i = size(arr, store_decimal_as_integer=True, use_dictionary=False, column_encoding={"v": "DELTA_BINARY_PACKED"}, compression="zstd")
    row.append(f"zstd, bytes form PLAIN {b:,} / integer form DELTA_BINARY_PACKED {i:,}{'  <-- integer smaller' if i < b else ''}")
    print("\n  ".join(row))
# statistics fields pyarrow writes for a fixed-length decimal
pq.write_table(pa.table({"v": pa.array([D("-1.50"), D("2.25"), None], pa.decimal128(9,2))}), "t.parquet")
buf, footer = read_footer("t.parquet")
names = {1: "max (older)", 2: "min (older)", 3: "null_count", 5: "max_value", 6: "min_value", 7: "is_max_value_exact", 8: "is_min_value_exact"}
st = footer[4][0][1][0][3].get(12, {})
print("fixed-length decimal(9,2) statistics fields:", [names.get(k, k) for k in sorted(st)], "min_value bytes", st[6].hex(), "max_value bytes", st[5].hex())
print("column_orders:", footer.get(7))
os.remove("t.parquet")
