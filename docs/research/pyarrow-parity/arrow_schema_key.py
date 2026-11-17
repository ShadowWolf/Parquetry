"""Prints what pyarrow stores under the ARROW:schema key of a Parquet file.

Run from any directory. It writes nothing to disk.
"""
import base64
import io

import pyarrow as pa
import pyarrow.parquet as pq

table = pa.table(
    {
        "length_of_time": pa.array([1], pa.duration("us")),
        "number": pa.array([1], pa.int64()),
    }
)
buffer = io.BytesIO()
pq.write_table(table, buffer)
value = pq.read_metadata(io.BytesIO(buffer.getvalue())).metadata[b"ARROW:schema"]

print(f"pyarrow {pa.__version__}")
print(f"the stored value: {len(value)} bytes, starting {value[:16]!r}")

decoded = base64.b64decode(value, validate=True)
print(f"decoded from base64: {len(decoded)} bytes, starting {decoded[:8].hex()}")

schema = pa.ipc.read_schema(pa.BufferReader(decoded))
print("read as a schema message of Arrow's IPC format:")
for field in schema:
    print(f"  {field.name}: {field.type}")
