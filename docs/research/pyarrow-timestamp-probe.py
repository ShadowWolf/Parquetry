import datetime as dt
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd

print("pyarrow", pa.__version__, "pandas", pd.__version__)

# Nanosecond values with a non-zero sub-microsecond part.
# One after 1970 and one before, to see which way the cut goes.
after = pd.Timestamp("2024-05-06 07:08:09.123456789", tz="UTC").value
before = pd.Timestamp("1969-12-31 23:59:59.999999900", tz="UTC").value
t = pa.table({"ts": pa.array([after, before], type=pa.timestamp("ns", tz="UTC"))})
print("input:", t.column("ts").to_pylist(), [after, before])

def attempt(label, **kw):
    path = "out.parquet"
    try:
        pq.write_table(t, path, **kw)
    except Exception as e:
        print(f"{label}: ERROR {type(e).__name__}: {e}")
        return
    f = pq.ParquetFile(path)
    col = f.schema.column(0)
    back = f.read().column("ts")
    print(f"{label}: wrote {col.physical_type} {col.logical_type}; raw values {back.cast(pa.int64()).to_pylist()}")

attempt("default (no arguments)")
attempt("version=2.4", version="2.4")
attempt("version=1.0", version="1.0")
attempt("coerce_timestamps=us", coerce_timestamps="us")
attempt("coerce_timestamps=us, allow_truncated_timestamps", coerce_timestamps="us", allow_truncated_timestamps=True)
attempt("version=2.4, coerce_timestamps=us", version="2.4", coerce_timestamps="us")

# Explicit Arrow cast, outside the Parquet writer.
try:
    t.column("ts").cast(pa.timestamp("us", tz="UTC"))
    print("cast ns->us (safe): ok")
except Exception as e:
    print(f"cast ns->us (safe): ERROR {type(e).__name__}: {e}")
print("cast ns->us (unsafe):", t.column("ts").cast(pa.timestamp("us", tz="UTC"), safe=False).cast(pa.int64()).to_pylist())

# pandas default path
df = pd.DataFrame({"ts": pd.to_datetime([after, before], utc=True)})
print("pandas dtype:", df["ts"].dtype)
try:
    df.to_parquet("pd.parquet")
    f = pq.ParquetFile("pd.parquet")
    print("pandas to_parquet default:", f.schema.column(0).logical_type, f.read().column("ts").cast(pa.int64()).to_pylist())
except Exception as e:
    print(f"pandas to_parquet default: ERROR {type(e).__name__}: {e}")

# Python datetime has microsecond precision, so pyarrow infers timestamp[us].
print("python datetime infers:", pa.array([dt.datetime(2024, 5, 6, tzinfo=dt.timezone.utc)]).type)
