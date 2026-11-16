"""Prints what pyarrow writes for the cases Parquetry has decided, and for some
neighboring cases that help explain them.

Run from any directory. It writes one small file, probe.parquet, to the current
directory and overwrites it for each case.
"""
import datetime as dt
import decimal
import inspect
import os
import sys
import uuid

import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compact_thrift import read_footer, read_struct  # noqa: E402

PATH = "probe.parquet"
print("pyarrow", pa.__version__)


def section(title):
    print(f"\n== {title} ==")


def first_line(error):
    return f"ERROR {type(error).__name__}: {str(error).splitlines()[0]}"


def schema_lines(path):
    schema = pq.ParquetFile(path).schema
    lines = []
    for i in range(len(schema)):
        c = schema.column(i)
        width = f"({c.length})" if c.physical_type == "FIXED_LEN_BYTE_ARRAY" else ""
        lines.append(f"{c.path}: {c.physical_type}{width} logical={c.logical_type}"
                     f" converted={c.converted_type}"
                     f" max_def={c.max_definition_level} max_rep={c.max_repetition_level}")
    return lines


def write(label, table, **options):
    try:
        pq.write_table(table, PATH, **options)
    except Exception as e:
        print(f"{label}: {first_line(e)}")
        return False
    for line in schema_lines(PATH):
        print(f"{label}: {line}")
    return True


def column(label, arrow_type, values=None, **options):
    try:
        array = pa.array(values if values is not None else [None], type=arrow_type)
    except Exception as e:
        print(f"{label}: building the array failed: {first_line(e)}")
        return False
    return write(label, pa.table({"v": array}), **options)


section("writer defaults (arguments of ParquetWriter)")
for name, p in inspect.signature(pq.ParquetWriter.__init__).parameters.items():
    if name in ("self", "where", "schema", "writer_engine_version", "options", "filesystem"):
        continue
    if p.default is not inspect.Parameter.empty:
        print(f"{name} = {p.default!r}")

section("integers")
for t in (pa.int8(), pa.int16(), pa.int32(), pa.int64(), pa.uint8(), pa.uint16(), pa.uint32(), pa.uint64()):
    column(str(t), t, [1])

section("floats, bool, text, bytes")
for t in (pa.float16(), pa.float32(), pa.float64(), pa.bool_(), pa.string(), pa.binary(), pa.binary(16)):
    column(str(t), t)

section("uuid")
text = "00112233-4455-6677-8899-aabbccddeeff"
if column("uuid", pa.uuid(), [uuid.UUID(text).bytes]):
    stored = open(PATH, "rb").read()
    print("uuid: the bytes are stored in the order of the text digits:", bytes.fromhex(text.replace("-", "")) in stored)

section("dates, times, lengths of time")
for t in (pa.date32(), pa.time64("us"), pa.time64("ns"), pa.duration("us"), pa.duration("ns")):
    column(str(t), t)
column("month_day_nano_interval", pa.month_day_nano_interval())

section("timestamps: the unit and time zone of the Arrow type decide what is written")
for t in (pa.timestamp("s", tz="UTC"), pa.timestamp("ms", tz="UTC"), pa.timestamp("us", tz="UTC"),
          pa.timestamp("ns", tz="UTC"), pa.timestamp("us"), pa.timestamp("ns"),
          pa.timestamp("us", tz="Europe/Berlin")):
    column(str(t), t)
print("a Python datetime with no time zone becomes:", pa.array([dt.datetime(2024, 5, 6)]).type)
print("a Python datetime in UTC becomes:", pa.array([dt.datetime(2024, 5, 6, tzinfo=dt.timezone.utc)]).type)
plus_two = dt.datetime(2024, 5, 6, 12, tzinfo=dt.timezone(dt.timedelta(hours=2)))
print("a Python datetime at +02:00 becomes:", pa.array([plus_two]).type)
pq.write_table(pa.table({"v": pa.array([plus_two])}), PATH, store_schema=False)
print("12:00 at +02:00, read back without the Arrow schema:", pq.read_table(PATH).column("v").to_pylist())
year_one = dt.datetime(1, 1, 1, tzinfo=dt.timezone.utc)
column("year 1 as microseconds", pa.timestamp("us", tz="UTC"), [year_one])
column("year 1 as nanoseconds", pa.timestamp("ns", tz="UTC"), [year_one])

section("decimals: storage by precision")
for label, options in (("default", {}), ("store_decimal_as_integer=True", {"store_decimal_as_integer": True})):
    widths = {}
    for precision in range(1, 39):
        pq.write_table(pa.table({"v": pa.array([None], pa.decimal128(precision, 0))}), PATH, **options)
        c = pq.ParquetFile(PATH).schema.column(0)
        key = f"{c.physical_type}({c.length})" if c.physical_type == "FIXED_LEN_BYTE_ARRAY" else c.physical_type
        widths.setdefault(key, []).append(precision)
    for key, precisions in widths.items():
        print(f"{label}: precision {precisions[0]} to {precisions[-1]} -> {key}")
column("decimal256(50,2)", pa.decimal256(50, 2))
print("a Python Decimal('1.50') becomes:", pa.array([decimal.Decimal("1.50")]).type)

section("decimals: values that do not fit")
column("1.234 into decimal(5,2)", pa.decimal128(5, 2), [decimal.Decimal("1.234")])
column("12345.6 into decimal(5,2)", pa.decimal128(5, 2), [decimal.Decimal("12345.6")])
wide = pa.array([decimal.Decimal("12345.67")], pa.decimal128(7, 2))
for safe in (True, False):
    try:
        narrow = wide.cast(pa.decimal128(5, 2), safe=safe)
        pq.write_table(pa.table({"v": narrow}), PATH)
        print(f"cast 12345.67 from (7,2) to (5,2), safe={safe}: written; read back {pq.read_table(PATH).column('v').to_pylist()}")
    except Exception as e:
        print(f"cast 12345.67 from (7,2) to (5,2), safe={safe}: {first_line(e)}")

section("dictionary of text, which is Arrow's nearest type to an enum")
column("dictionary<string>", pa.dictionary(pa.int32(), pa.string()), ["a", "b", "a"])

section("required columns and nulls")
required = pa.schema([pa.field("v", pa.string(), nullable=False)])
write("non-nullable field", pa.table({"v": pa.array(["a"])}, schema=required))
try:
    pa.table({"v": pa.array(["a", None])}).cast(required)
    print("casting a column with a null to non-nullable: no error")
except Exception as e:
    print(f"casting a column with a null to non-nullable: {first_line(e)}")
unchecked = pa.Table.from_arrays([pa.array(["a", None])], schema=required)
write("writing a non-nullable column that holds a null", unchecked)

section("nested types")
column("list<int32>, nullable elements", pa.list_(pa.int32()), [[1, None]])
column("list<int32 not null>", pa.list_(pa.field("item", pa.int32(), nullable=False)), [[1]])
column("list with use_compliant_nested_type=False", pa.list_(pa.int32()), [[1]], use_compliant_nested_type=False)
column("map<string,int32>", pa.map_(pa.string(), pa.int32()), [[("a", 1)]])
column("struct", pa.struct([("a", pa.int32()), ("b", pa.string())]), [{"a": 1, "b": "x"}])
column("struct with no fields", pa.struct([]), [{}])

section("a file written with default settings: footer and first pages")
STATISTICS_FIELDS = {1: "max (older)", 2: "min (older)", 3: "null_count", 4: "distinct_count",
                     5: "max_value", 6: "min_value", 7: "is_max_value_exact", 8: "is_min_value_exact",
                     9: "nan_count"}
PAGE_TYPES = {0: "data page version 1", 2: "dictionary page", 3: "data page version 2"}
rows = 300_000
table = pa.table({
    "int64": pa.array(range(rows), type=pa.int64()),
    "text": pa.array([f"k{i % 50}" for i in range(rows)]),
    "double": pa.array([float("nan") if i % 7 == 0 else float(i) for i in range(rows)]),
    "bool": pa.array([i % 2 == 0 for i in range(rows)]),
    "uint8": pa.array([i % 200 for i in range(rows)], type=pa.uint8()),
})
pq.write_table(table, PATH)
buf, footer = read_footer(PATH)
print("created_by:", footer.get(6))
print("version field in the footer:", footer[1], "| pyarrow reports format_version", pq.ParquetFile(PATH).metadata.format_version)
print("key-value metadata keys:", [kv[1] for kv in footer.get(5, [])])
print("column_orders present:", 7 in footer)
group = pq.ParquetFile(PATH).metadata.row_group(0)
for index, chunk in enumerate(footer[4][0][1]):
    meta = chunk[3]
    info = group.column(index)
    name = b".".join(meta[3]).decode()
    data_page, _ = read_struct(buf, meta[9])
    present = [STATISTICS_FIELDS[k] for k in sorted(meta.get(12, {}))]
    print(f"{name}: compression={info.compression} encodings={info.encodings}"
          f" dictionary page={info.has_dictionary_page}")
    print(f"{name}: first data page is {PAGE_TYPES[data_page[1]]}")
    print(f"{name}: statistics fields written: {present}")
    print(f"{name}: page index written: column index={info.has_column_index} offset index={info.has_offset_index}")
    print(f"{name}: bloom filter written: {14 in meta}")

section("floating-point statistics")
cases = (
    ("some NaN among numbers", [float("nan"), 1.0, 5.0]),
    ("every value NaN", [float("nan")] * 3),
    ("only +0.0", [0.0] * 3),
    ("only -0.0", [-0.0] * 3),
    ("+0.0 and 5.0", [0.0, 5.0]),
    ("-5.0 and -0.0", [-5.0, -0.0]),
)
for label, values in cases:
    pq.write_table(pa.table({"v": pa.array(values)}), PATH)
    st = pq.ParquetFile(PATH).metadata.row_group(0).column(0).statistics
    if st.has_min_max:
        print(f"{label}: min={st.min!r} max={st.max!r}")
    else:
        print(f"{label}: no min or max written")

section("page index, when turned on with write_page_index=True")
long_text = ["a" * 200 + f"{i:06d}" for i in range(rows)]
one_nan_page = [float("nan")] * 100_000 + [float(i) for i in range(200_000)]
table = pa.table({
    "int64": pa.array(range(rows), type=pa.int64()),
    "long_text": pa.array(long_text),
    "one_all_nan_page": pa.array(one_nan_page),
})
pq.write_table(table, PATH, write_page_index=True, use_dictionary=False)
buf, footer = read_footer(PATH)
group = pq.ParquetFile(PATH).metadata.row_group(0)
for index, chunk in enumerate(footer[4][0][1]):
    name = b".".join(chunk[3][3]).decode()
    info = group.column(index)
    print(f"{name}: column index={info.has_column_index} offset index={info.has_offset_index}")
    if 6 in chunk:
        column_index, _ = read_struct(buf, chunk[6])
        print(f"{name}: column index has nan_counts: {8 in column_index};"
              f" length of the first page's min and max: {len(column_index[2][0])} and {len(column_index[3][0])} bytes")
    stats = chunk[3].get(12, {})
    if 5 in stats:
        print(f"{name}: length of the chunk's max_value and min_value: {len(stats[5])} and {len(stats[6])} bytes")

section("default sizes")
pq.write_table(pa.table({"v": pa.array(range(2_500_000), type=pa.int32())}), PATH)
md = pq.ParquetFile(PATH).metadata
print("2,500,000 rows -> rows per row group:", [md.row_group(i).num_rows for i in range(md.num_row_groups)])
pq.write_table(pa.table({"v": pa.array(range(rows), type=pa.int64())}), PATH,
               write_page_index=True, use_dictionary=False, compression="none")
buf, footer = read_footer(PATH)
offset_index, _ = read_struct(buf, footer[4][0][1][0][4])
pages = offset_index[1]
print(f"300,000 int64 values, no dictionary, no compression -> {len(pages)} pages;"
      f" rows in the first page: {pages[1][3] - pages[0][3]}; bytes in the first page: {pages[0][2]}")
strings = pa.array(["x" * 1000] * 5000)
pq.write_table(pa.table({"v": strings}), PATH, write_page_index=True, use_dictionary=False, compression="none")
buf, footer = read_footer(PATH)
offset_index, _ = read_struct(buf, footer[4][0][1][0][4])
pages = offset_index[1]
print(f"5,000 strings of 1,000 bytes -> {len(pages)} pages; bytes in the first page: {pages[0][2]}")

section("what pyarrow reads back when the Arrow schema is not in the file")
table = pa.table({
    "duration_us": pa.array([1], pa.duration("us")),
    "dictionary_of_text": pa.array(["a"]).dictionary_encode(),
    "timestamp_berlin": pa.array([dt.datetime(2024, 5, 6)], pa.timestamp("us", tz="Europe/Berlin")),
    "timestamp_utc": pa.array([dt.datetime(2024, 5, 6, tzinfo=dt.timezone.utc)]),
    "uuid": pa.array([uuid.UUID(text).bytes], pa.uuid()),
    "uint8": pa.array([200], pa.uint8()),
    "time_us": pa.array([dt.time(1, 2, 3)]),
    "decimal": pa.array([None], pa.decimal128(9, 2)),
})
for store in (True, False):
    pq.write_table(table, PATH, store_schema=store)
    types = {f.name: str(f.type) for f in pq.read_table(PATH).schema}
    print(f"store_schema={store}: {types}")
wide = pa.table({f"c{i}": pa.array([1]) for i in range(500)})
pq.write_table(wide, PATH)
with_schema = pq.ParquetFile(PATH).metadata.serialized_size
pq.write_table(wide, PATH, store_schema=False)
without_schema = pq.ParquetFile(PATH).metadata.serialized_size
print(f"footer of a file with 500 int64 columns: {with_schema} bytes with the Arrow schema, {without_schema} bytes without")

section("text that is not valid UTF-8")
column("a Python string holding half of a two-unit character", pa.string(), ["\ud800"])
try:
    pa.array([b"\xff\xfe"]).cast(pa.string())
    print("casting the bytes ff fe to string: no error")
except Exception as e:
    print(f"casting the bytes ff fe to string: {first_line(e)}")
unchecked = pa.Array.from_buffers(pa.string(), 1, pa.array([b"\xff\xfe"]).buffers())
write("writing a string array that holds the bytes ff fe, built without a check", pa.table({"v": unchecked}))

section("column names")
write("a name with a space and a comma", pa.table({"a b,c": pa.array([1])}))
write("two names that differ only by case", pa.table({"A": pa.array([1]), "a": pa.array([2])}))

section("forms Parquetry writes that are not pyarrow's default: written by pyarrow with options, then read back")
forms = {
    "decimal(9,2) as INT32, which is an option in Parquetry too": (pa.table({"v": pa.array([decimal.Decimal("1.50")], pa.decimal128(9, 2))}), {"store_decimal_as_integer": True}),
    "Guid as 16 fixed-length bytes with no annotation": (pa.table({"v": pa.array([uuid.UUID(text).bytes], pa.binary(16))}), {}),
    "TimeSpan as a 64-bit count": (pa.table({"v": pa.array([90_000_000], pa.int64())}), {}),
    "page index on": (pa.table({"v": pa.array([1, 2, 3])}), {"write_page_index": True}),
    "list with required elements": (pa.table({"v": pa.array([[1]], pa.list_(pa.field("element", pa.int32(), nullable=False)))}), {}),
}
for label, (table, options) in forms.items():
    pq.write_table(table, PATH, store_schema=False, **options)
    back = pq.read_table(PATH)
    print(f"{label}: read back as {back.schema.field('v').type} {back.column('v').to_pylist()}")
with_key = pa.table({"v": pa.array([dt.date(1500, 1, 1)])}).replace_schema_metadata({"org.apache.spark.version": "3.5.0"})
pq.write_table(with_key, PATH)
back = pq.read_table(PATH)
print("a file with the key org.apache.spark.version and a date in 1500: read back", back.column("v").to_pylist())

os.remove(PATH)
