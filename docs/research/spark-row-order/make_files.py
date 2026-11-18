"""Writes the two test files for the Spark row order check with pyarrow.

    python make_files.py <folder>

small.parquet has 1,000 rows in one row group. big.parquet has 3,000,000
rows in 12 row groups and is about 88 MB. In both, the id column counts up
from 0, so a reader that returns ids in ascending order has kept the file's
row order.
"""
import os
import sys

import pyarrow as pa
import pyarrow.parquet as pq

folder = sys.argv[1]

small = pa.table({"id": pa.array(range(1000), pa.int64())})
pq.write_table(small, os.path.join(folder, "small.parquet"))

rows = 3_000_000
big = pa.table(
    {
        "id": pa.array(range(rows), pa.int64()),
        # Random text, so that the file is large enough for Spark to split.
        "pad": pa.array([os.urandom(8).hex() for _ in range(rows)]),
    }
)
pq.write_table(big, os.path.join(folder, "big.parquet"), row_group_size=250_000, compression="none")

for name in ("small.parquet", "big.parquet"):
    path = os.path.join(folder, name)
    metadata = pq.ParquetFile(path).metadata
    print("FILE", name, os.path.getsize(path), "bytes,", metadata.num_row_groups, "row groups")
