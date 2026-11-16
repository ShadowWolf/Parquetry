"""Prints what pyarrow writes for each case that Parquetry has a decision about."""
import datetime as dt
import decimal
import inspect
import math
import uuid

import pyarrow as pa
import pyarrow.parquet as pq

print("pyarrow", pa.__version__)
PATH = "parity.parquet"


def schema_lines(path):
    s = pq.ParquetFile(path).schema
    out = []
    for i in range(len(s)):
        c = s.column(i)
        out.append(f"{c.path}: {c.physical_type}"
                   f"{'(' + str(c.length) + ')' if c.physical_type == 'FIXED_LEN_BYTE_ARRAY' else ''}"
                   f" logical={c.logical_type} converted={c.converted_type}"
                   f" max_def={c.max_definition_level} max_rep={c.max_repetition_level}")
    return out


def show(label, table, **kw):
    try:
        pq.write_table(table, PATH, **kw)
    except Exception as e:
        print(f"{label}: ERROR {type(e).__name__}: {str(e).splitlines()[0]}")
        return
    for line in schema_lines(PATH):
        print(f"{label}: {line}")


def one(label, typ, values=None, **kw):
    try:
        arr = pa.array(values if values is not None else [None], type=typ)
    except Exception as e:
        print(f"{label}: ERROR building array {type(e).__name__}: {str(e).splitlines()[0]}")
        return
    show(label, pa.table({"v": arr}), **kw)


print("\n== write_table defaults ==")
sig = inspect.signature(pq.ParquetWriter.__init__)
for name, p in sig.parameters.items():
    if name in ("self", "where", "schema", "writer_engine_version", "options", "filesystem"):
        continue
    if p.default is not inspect.Parameter.empty:
        print(f"{name} = {p.default!r}")
print("write_table row_group_size default =", inspect.signature(pq.write_table).parameters["row_group_size"].default)

print("\n== integers ==")
for t in (pa.int8(), pa.int16(), pa.int32(), pa.int64(), pa.uint8(), pa.uint16(), pa.uint32(), pa.uint64()):
    one(str(t), t, [1])

print("\n== floats, bool, text, bytes ==")
for t in (pa.float16(), pa.float32(), pa.float64(), pa.bool_(), pa.string(), pa.binary(), pa.binary(16)):
    one(str(t), t)

print("\n== uuid ==")
try:
    one("uuid extension", pa.uuid(), [uuid.UUID("00112233-4455-6677-8899-aabbccddeeff").bytes])
    raw = open(PATH, "rb").read()
    print("uuid bytes stored in text order:", bytes.fromhex("00112233445566778899aabbccddeeff") in raw)
except Exception as e:
    print("uuid: ERROR", type(e).__name__, e)

print("\n== dates and times ==")
for t in (pa.date32(), pa.date64(), pa.time32("ms"), pa.time64("us"), pa.time64("ns"), pa.duration("us"), pa.duration("ns")):
    one(str(t), t)
try:
    one("month_day_nano_interval", pa.month_day_nano_interval())
except Exception as e:
    print("interval: ERROR", type(e).__name__, e)

print("\n== timestamps ==")
for t in (pa.timestamp("s", tz="UTC"), pa.timestamp("ms", tz="UTC"), pa.timestamp("us", tz="UTC"), pa.timestamp("ns", tz="UTC"),
          pa.timestamp("us"), pa.timestamp("ns"), pa.timestamp("us", tz="Europe/Berlin")):
    one(str(t), t)
print("python naive datetime infers:", pa.array([dt.datetime(2024, 5, 6)]).type)
print("python aware datetime infers:", pa.array([dt.datetime(2024, 5, 6, tzinfo=dt.timezone.utc)]).type)
print("python aware +02:00 datetime infers:", pa.array([dt.datetime(2024, 5, 6, tzinfo=dt.timezone(dt.timedelta(hours=2)))]).type)
one("timestamp year 1 as us", pa.timestamp("us", tz="UTC"), [dt.datetime(1, 1, 1, tzinfo=dt.timezone.utc)])
one("timestamp year 1 as ns", pa.timestamp("ns", tz="UTC"), [dt.datetime(1, 1, 1, tzinfo=dt.timezone.utc)])

print("\n== decimals ==")
for p_, s_ in ((9, 2), (18, 2), (38, 18)):
    one(f"decimal128({p_},{s_}) default", pa.decimal128(p_, s_))
    one(f"decimal128({p_},{s_}) store_decimal_as_integer", pa.decimal128(p_, s_), store_decimal_as_integer=True)
one("decimal256(50,2)", pa.decimal256(50, 2))
print("python Decimal infers:", pa.array([decimal.Decimal("1.50")]).type)
one("decimal value with too many places for (5,2)", pa.decimal128(5, 2), [decimal.Decimal("1.234")])
one("decimal value too large for (5,2)", pa.decimal128(5, 2), [decimal.Decimal("12345.6")])

print("\n== enum-like and nulls ==")
one("dictionary<string>", pa.dictionary(pa.int32(), pa.string()), ["a", "b", "a"])
show("non-nullable field", pa.table({"v": pa.array(["a"])}, schema=pa.schema([pa.field("v", pa.string(), nullable=False)])))
try:
    t = pa.table({"v": pa.array(["a", None])}).cast(pa.schema([pa.field("v", pa.string(), nullable=False)]))
    show("null in non-nullable field", t)
except Exception as e:
    print(f"null in non-nullable field: ERROR at cast {type(e).__name__}: {str(e).splitlines()[0]}")
try:
    t = pa.Table.from_arrays([pa.array(["a", None])], schema=pa.schema([pa.field("v", pa.string(), nullable=False)]))
    show("null in non-nullable field (from_arrays, no validation)", t)
    print("   read back:", pq.read_table(PATH).column("v").to_pylist())
except Exception as e:
    print(f"null in non-nullable field (from_arrays): ERROR {type(e).__name__}: {str(e).splitlines()[0]}")

print("\n== nested ==")
one("list<int32> nullable elements", pa.list_(pa.int32()), [[1, None]])
one("list<int32 not null>", pa.list_(pa.field("item", pa.int32(), nullable=False)), [[1]])
one("list, use_compliant_nested_type=False", pa.list_(pa.int32()), [[1]], use_compliant_nested_type=False)
one("map<string,int32>", pa.map_(pa.string(), pa.int32()), [[("a", 1)]])
one("struct", pa.struct([("a", pa.int32()), ("b", pa.string())]), [{"a": 1, "b": "x"}])
one("empty struct", pa.struct([]), [{}])
print(pq.ParquetFile(PATH).schema if False else "", end="")

print("\n== file-level defaults ==")
n = 300_000
tbl = pa.table({
    "i": pa.array(range(n), type=pa.int64()),
    "s": pa.array([f"k{i % 50}" for i in range(n)]),
    "f": pa.array([float("nan") if i % 7 == 0 else i * 1.0 for i in range(n)]),
    "allnan": pa.array([float("nan")] * n),
    "z": pa.array([0.0, -0.0] * (n // 2)),
})
pq.write_table(tbl, PATH)
pf = pq.ParquetFile(PATH)
md = pf.metadata
print("created_by:", md.created_by)
print("format_version:", md.format_version)
print("num_row_groups:", md.num_row_groups, "rows:", md.num_rows)
print("key-value metadata keys:", list((md.metadata or {}).keys()))
rg = md.row_group(0)
for j in range(rg.num_columns):
    c = rg.column(j)
    st = c.statistics
    print(f"column {c.path_in_schema}: compression={c.compression} encodings={c.encodings}"
          f" has_dictionary_page={c.has_dictionary_page} has_column_index={c.has_column_index}"
          f" has_offset_index={c.has_offset_index}"
          f" bloom_filter_offset={getattr(c, 'bloom_filter_offset', 'n/a')}")
    if st is not None:
        print(f"    stats: has_min_max={st.has_min_max} min={st.min if st.has_min_max else None} max={st.max if st.has_min_max else None}"
              f" null_count={st.null_count} distinct={st.distinct_count if st.has_distinct_count else None}")
    else:
        print("    stats: none")
print("data page versions: see data_page_version default above")

pq.write_table(tbl, PATH, write_page_index=True)
c = pq.ParquetFile(PATH).metadata.row_group(0).column(3)
print("with write_page_index=True, allnan column: has_column_index=", c.has_column_index, "has_offset_index=", c.has_offset_index)
c = pq.ParquetFile(PATH).metadata.row_group(0).column(2)
print("with write_page_index=True, f column: has_column_index=", c.has_column_index)

print("\n== text that is not valid ==")
try:
    one("lone surrogate string", pa.string(), ["\ud800"])
except Exception as e:
    print("lone surrogate string: ERROR", type(e).__name__, str(e).splitlines()[0])

print("\n== column names ==")
show("name with space and punctuation", pa.table({"a b,c": pa.array([1])}))
show("names differing by case", pa.table({"A": pa.array([1]), "a": pa.array([2])}))
