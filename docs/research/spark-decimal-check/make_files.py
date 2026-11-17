"""Writes the Parquet files that check.py asks Spark to read.

Every file is written by pyarrow. Each table is written twice: once with
pyarrow's default decimal storage, fixed-length bytes, and once with
store_decimal_as_integer. The first argument is the folder to write into.
"""
import decimal
import json
import random
import sys

import pyarrow as pa
import pyarrow.parquet as pq

out = sys.argv[1]
decimal.getcontext().prec = 80
random.seed(20261116)
N = 6000
D = decimal.Decimal


def dec(unscaled, scale):
    return D(unscaled).scaleb(-scale)


def text(v):
    return None if v is None else format(v, "f")


def values_for(precision, scale, n, nulls=True):
    top = 10 ** precision - 1
    edges = [top, -top, 0, 1, -1]
    for bits in (7, 8, 15, 16, 23, 24, 31, 32, 39, 40, 47, 48, 55, 56, 63, 64, 71, 72, 95, 96, 119, 120):
        for u in (2 ** bits - 1, 2 ** bits, 2 ** bits + 1):
            if u <= top:
                edges += [u, -u]
    vals = []
    for i in range(n):
        if i < len(edges):
            vals.append(dec(edges[i], scale))
        elif nulls and random.random() < 0.1:
            vals.append(None)
        else:
            # mix of full-range and small values so every byte position varies
            if random.random() < 0.5:
                vals.append(dec(random.randint(-top, top), scale))
            else:
                digits = random.randint(1, precision)
                small = 10 ** digits - 1
                vals.append(dec(random.randint(-small, small), scale))
    return vals


expected = {}

# ---------- flat file ----------
fields, arrays, exp = [], [], {}
fields.append(pa.field("id", pa.int64(), nullable=False))
arrays.append(pa.array(range(N), pa.int64()))
for p in range(1, 39):
    s = p // 3
    v = values_for(p, s, N)
    fields.append(pa.field(f"p{p}", pa.decimal128(p, s)))
    arrays.append(pa.array(v, pa.decimal128(p, s)))
    exp[f"p{p}"] = {"type": f"decimal({p},{s})", "values": [text(x) for x in v]}
for p in (2, 5, 9, 10, 18, 19, 20, 38):
    s = p // 2
    v = values_for(p, s, N, nulls=False)
    fields.append(pa.field(f"req_p{p}", pa.decimal128(p, s), nullable=False))
    arrays.append(pa.array(v, pa.decimal128(p, s)))
    exp[f"req_p{p}"] = {"type": f"decimal({p},{s})", "values": [text(x) for x in v]}
u8 = [None if i % 11 == 3 else i % 256 for i in range(N)]
fields.append(pa.field("u8", pa.uint8()))
arrays.append(pa.array(u8, pa.uint8()))
exp["u8"] = {"type": "smallint", "values": [None if x is None else str(x) for x in u8]}
u8r = [(i * 7) % 256 for i in range(N)]
fields.append(pa.field("u8_req", pa.uint8(), nullable=False))
arrays.append(pa.array(u8r, pa.uint8()))
exp["u8_req"] = {"type": "smallint", "values": [str(x) for x in u8r]}
flat = pa.Table.from_arrays(arrays, schema=pa.schema(fields))
expected["flat"] = exp

common = dict(row_group_size=1500, data_page_size=2048, write_batch_size=100)
variants = {
    "dict": dict(use_dictionary=True),
    "plain": dict(use_dictionary=False),
    "fallback": dict(use_dictionary=True, dictionary_pagesize_limit=1024),
}
forms = {"flba": {}, "int": {"store_decimal_as_integer": True}}
report = []
for form, fopt in forms.items():
    for variant, vopt in variants.items():
        path = f"{out}/flat_{form}_{variant}.parquet"
        pq.write_table(flat, path, **common, **fopt, **vopt)
        md = pq.ParquetFile(path).metadata
        sch = pq.ParquetFile(path).schema
        encs = set()
        pages = 0
        for g in range(md.num_row_groups):
            for c in range(md.num_columns):
                encs.add(tuple(sorted(md.row_group(g).column(c).encodings)))
        phys = {sch.column(i).name: (sch.column(i).physical_type, sch.column(i).length) for i in (1, 9, 18, 20, 38)}
        report.append(f"flat_{form}_{variant}: row groups={md.num_row_groups} encodings={sorted(encs)} types={phys}")

# ---------- nested file ----------
M = 2000
nfields, narrays, nexp = [pa.field("id", pa.int64(), nullable=False)], [pa.array(range(M), pa.int64())], {}
for p in (4, 9, 18, 20, 38):
    s = p // 3
    t = pa.list_(pa.decimal128(p, s))
    pool = values_for(p, s, 4 * M)
    lists = []
    k = 0
    for i in range(M):
        if i % 13 == 5:
            lists.append(None)
        else:
            ln = i % 4
            lists.append(pool[k:k + ln])
            k += ln
    nfields.append(pa.field(f"list_p{p}", t))
    narrays.append(pa.array(lists, t))
    nexp[f"list_p{p}"] = [None if l is None else [text(x) for x in l] for l in lists]
st = pa.struct([("a", pa.decimal128(9, 2)), ("b", pa.decimal128(18, 4)), ("c", pa.decimal128(38, 10)), ("u", pa.uint8())])
a, b, c = values_for(9, 2, M), values_for(18, 4, M), values_for(38, 10, M)
structs = [None if i % 17 == 2 else {"a": a[i], "b": b[i], "c": c[i], "u": i % 256} for i in range(M)]
nfields.append(pa.field("st", st))
narrays.append(pa.array(structs, st))
nexp["st"] = [None if x is None else {"a": text(x["a"]), "b": text(x["b"]), "c": text(x["c"]), "u": str(x["u"])} for x in structs]
mt = pa.map_(pa.string(), pa.decimal128(12, 3))
mv = values_for(12, 3, 2 * M)
maps = [None if i % 19 == 4 else [(f"k{j}", mv[2 * i + j]) for j in range(i % 3)] for i in range(M)]
nfields.append(pa.field("mp", mt))
narrays.append(pa.array(maps, mt))
nexp["mp"] = [None if m is None else {k: text(v) for k, v in m} for m in maps]
lu = pa.list_(pa.uint8())
lus = [None if i % 23 == 1 else [(i + j) % 256 if j != 2 else None for j in range(i % 5)] for i in range(M)]
nfields.append(pa.field("list_u8", lu))
narrays.append(pa.array(lus, lu))
nexp["list_u8"] = [None if l is None else [None if x is None else str(x) for x in l] for l in lus]
nested = pa.Table.from_arrays(narrays, schema=pa.schema(nfields))
expected["nested"] = nexp
for form, fopt in forms.items():
    for variant in ("dict", "plain"):
        path = f"{out}/nested_{form}_{variant}.parquet"
        pq.write_table(nested, path, row_group_size=700, data_page_size=2048, write_batch_size=100, **fopt, **variants[variant])
        report.append(f"nested_{form}_{variant}: row groups={pq.ParquetFile(path).metadata.num_row_groups}")

# ---------- sorted file for filters ----------
sfields, sarrays, sexp = [pa.field("id", pa.int64(), nullable=False)], [pa.array(range(N), pa.int64())], {}
for p in (2, 4, 9, 15, 18, 25, 38):
    s = p // 3
    top = 10 ** p - 1
    # ascending from the most negative to the most positive value
    v = [dec(-top + (2 * top * i) // (N - 1), s) for i in range(N)]
    sfields.append(pa.field(f"s{p}", pa.decimal128(p, s)))
    sarrays.append(pa.array(v, pa.decimal128(p, s)))
    sexp[f"s{p}"] = {"scale": s, "values": [text(x) for x in v]}
su8 = [(i * 256) // N for i in range(N)]
sfields.append(pa.field("u8", pa.uint8()))
sarrays.append(pa.array(su8, pa.uint8()))
sfields.append(pa.field("i16", pa.int16()))
sarrays.append(pa.array(su8, pa.int16()))
sexp["u8"] = {"values": su8}
sorted_table = pa.Table.from_arrays(sarrays, schema=pa.schema(sfields))
expected["sorted"] = sexp
for form, fopt in forms.items():
    for variant in ("dict", "plain"):
        path = f"{out}/sorted_{form}_{variant}.parquet"
        pq.write_table(sorted_table, path, row_group_size=500, data_page_size=1024, write_batch_size=50,
                       write_page_index=True, **fopt, **variants[variant])
        md = pq.ParquetFile(path).metadata
        st0 = md.row_group(0).column(3).statistics
        st11 = md.row_group(md.num_row_groups - 1).column(3).statistics
        report.append(f"sorted_{form}_{variant}: row groups={md.num_row_groups} s9 stats rg0 min={st0.min} max={st0.max} last min={st11.min} max={st11.max}")

json.dump(expected, open(f"{out}/expected.json", "w"))
print("pyarrow", pa.__version__)
print("\n".join(report))
