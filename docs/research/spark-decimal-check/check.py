"""Reads the files from make_files.py with Spark and compares them with what was written.

Four parts: every value of flat columns, every value of nested columns,
filters on sorted columns with the number of rows Spark had to scan, and reads
with a requested type that differs from the file's. The first argument is the
folder that holds the files. Exits with status 1 if any comparison fails.
"""
import json
import re
import sys
from decimal import Decimal

from pyspark.sql import SparkSession

work = sys.argv[1]
expected = json.load(open(work + "/expected.json"))
spark = (SparkSession.builder.master("local[2]").appName("check")
         .config("spark.sql.adaptive.enabled", "false")
         .config("spark.ui.enabled", "false")
         .getOrCreate())
spark.sparkContext.setLogLevel("OFF")
print("RESULT Spark", spark.version)
failures = 0


def short(e):
    lines = [l.strip() for l in str(e).splitlines() if l.strip()]
    keep = [l for l in lines if "cannot be converted" in l or "Expected" in l or l.startswith("Caused by")]
    msg = " | ".join(keep[:2]) if keep else (lines[0] if lines else type(e).__name__)
    msg = re.sub(r"file:/work/[A-Za-z0-9_.]+", "<file>", msg)
    msg = re.sub(r"o[0-9]+\.", "", msg)
    return msg[:330]


def canon(v):
    if v is None:
        return None
    if isinstance(v, Decimal):
        return str(v.normalize() + 0)
    if isinstance(v, str):
        try:
            return str(Decimal(v).normalize() + 0)
        except Exception:
            return v
    if isinstance(v, int):
        return str(Decimal(v).normalize() + 0)
    if isinstance(v, (list, tuple)) and not hasattr(v, "asDict"):
        return [canon(x) for x in v]
    if isinstance(v, dict):
        return {k: canon(x) for k, x in v.items()}
    if hasattr(v, "asDict"):
        return {k: canon(x) for k, x in v.asDict().items()}
    return str(v)


def scan_rows(df):
    """Rows the Parquet scan produced, from the scan node's metric."""
    plan = df._jdf.queryExecution().executedPlan()
    leaves = plan.collectLeaves()
    total = 0
    for i in range(leaves.size()):
        m = leaves.apply(i).metrics()
        if m.contains("numOutputRows"):
            total += m.apply("numOutputRows").value()
    return total


# ---------- 1. flat files: every value, both readers ----------
for form in ("flba", "int"):
    for variant in ("dict", "plain", "fallback"):
        for vec in ("true", "false"):
            spark.conf.set("spark.sql.parquet.enableVectorizedReader", vec)
            label = "flat_%s_%s, vectorized %s" % (form, variant, vec)
            try:
                df = spark.read.parquet("%s/flat_%s_%s.parquet" % (work, form, variant))
                rows = sorted(df.collect(), key=lambda r: r["id"])
                exp = expected["flat"]
                problems = []
                names = [f.name for f in df.schema.fields]
                missing = [n for n in exp if n not in names]
                if missing:
                    problems.append("missing columns %s" % missing[:5])
                for f in df.schema.fields:
                    if f.name == "id":
                        continue
                    want = exp[f.name]
                    if f.dataType.simpleString() != want["type"]:
                        problems.append("%s read as %s, wanted %s" % (f.name, f.dataType.simpleString(), want["type"]))
                    got = [canon(r[f.name]) for r in rows]
                    wantv = [canon(x) for x in want["values"]]
                    if got != wantv:
                        bad = [(i, g, w) for i, (g, w) in enumerate(zip(got, wantv)) if g != w]
                        problems.append("%s: %d of %d values differ, first %s" % (f.name, len(bad), len(got), bad[:2]))
                if problems:
                    failures += 1
                    print("RESULT FAIL %s: %s" % (label, problems[:4]))
                else:
                    print("RESULT PASS %s: %d columns, %d rows" % (label, len(names), len(rows)))
            except Exception as e:
                failures += 1
                print("RESULT FAIL %s: %s" % (label, short(e)))

# ---------- 2. nested files ----------
for form in ("flba", "int"):
    for variant in ("dict", "plain"):
        for vec in ("true", "false"):
            spark.conf.set("spark.sql.parquet.enableVectorizedReader", vec)
            label = "nested_%s_%s, vectorized %s" % (form, variant, vec)
            try:
                df = spark.read.parquet("%s/nested_%s_%s.parquet" % (work, form, variant))
                rows = sorted(df.collect(), key=lambda r: r["id"])
                problems = []
                for f in df.schema.fields:
                    if f.name == "id":
                        continue
                    got = [canon(r[f.name]) for r in rows]
                    want = [canon(x) for x in expected["nested"][f.name]]
                    if got != want:
                        bad = [(i, g, w) for i, (g, w) in enumerate(zip(got, want)) if g != w]
                        problems.append("%s (%s): %d rows differ, first %s" % (f.name, f.dataType.simpleString(), len(bad), bad[:1]))
                types = {f.name: f.dataType.simpleString() for f in df.schema.fields if f.name in ("st", "list_u8")}
                if problems:
                    failures += 1
                    print("RESULT FAIL %s: %s" % (label, problems[:4]))
                else:
                    print("RESULT PASS %s: %d rows; %s" % (label, len(rows), types))
            except Exception as e:
                failures += 1
                print("RESULT FAIL %s: %s" % (label, short(e)))

# ---------- 3. filters on sorted columns ----------
sexp = expected["sorted"]
N = len(sexp["u8"]["values"])
for form in ("flba", "int"):
    for variant in ("dict", "plain"):
        path = "%s/sorted_%s_%s.parquet" % (work, form, variant)
        for vec in ("true", "false"):
            spark.conf.set("spark.sql.parquet.enableVectorizedReader", vec)
            label = "sorted_%s_%s, vectorized %s" % (form, variant, vec)
            problems = []
            scanned = {}
            try:
                for name in [k for k in sexp if k != "u8"]:
                    vals = [Decimal(v) for v in sexp[name]["values"]]
                    probes = {
                        "lt0": ("%s < 0" % name, lambda v: v < 0),
                        "eq_first": ("%s = %s" % (name, sexp[name]["values"][0]), lambda v, t=vals[0]: v == t),
                        "eq_mid_neg": ("%s = %s" % (name, sexp[name]["values"][N // 4]), lambda v, t=vals[N // 4]: v == t),
                        "eq_last": ("%s = %s" % (name, sexp[name]["values"][-1]), lambda v, t=vals[-1]: v == t),
                        "ge_3q": ("%s >= %s" % (name, sexp[name]["values"][3 * N // 4]), lambda v, t=vals[3 * N // 4]: v >= t),
                        "between": ("%s > %s AND %s <= %s" % (name, sexp[name]["values"][N // 3], name, sexp[name]["values"][2 * N // 3]),
                                    lambda v, lo=vals[N // 3], hi=vals[2 * N // 3]: lo < v <= hi),
                    }
                    for pname, (cond, fn) in probes.items():
                        want = sum(1 for v in vals if fn(v))
                        df = spark.read.parquet(path).filter(cond).select("id")
                        got = len(df.collect())
                        scanned[name + "." + pname] = scan_rows(df)
                        if got != want:
                            problems.append("%s: got %d rows, wanted %d" % (cond, got, want))
                for name in ("u8", "i16"):
                    for cond, fn in (("%s = 200" % name, lambda v: v == 200), ("%s < 10" % name, lambda v: v < 10), ("%s >= 250" % name, lambda v: v >= 250)):
                        want = sum(1 for v in sexp["u8"]["values"] if fn(v))
                        df = spark.read.parquet(path).filter(cond).select("id")
                        got = len(df.collect())
                        scanned[cond] = scan_rows(df)
                        if got != want:
                            problems.append("%s: got %d rows, wanted %d" % (cond, got, want))
                pick = {k: scanned[k] for k in ("s9.eq_mid_neg", "s18.lt0", "s38.eq_last", "u8 = 200", "i16 = 200", "u8 < 10", "i16 < 10")}
                if problems:
                    failures += 1
                    print("RESULT FAIL %s: %s" % (label, problems[:6]))
                else:
                    print("RESULT PASS %s: all filter counts right; rows scanned of %d: %s" % (label, N, pick))
            except Exception as e:
                failures += 1
                print("RESULT FAIL %s: %s" % (label, short(e)))

# ---------- 4. a requested schema that differs from the file's ----------
requests = [
    ("p5", "decimal(7,1)"), ("p5", "decimal(12,1)"), ("p5", "decimal(25,1)"), ("p5", "decimal(7,3)"),
    ("p9", "decimal(10,3)"), ("p9", "decimal(18,3)"), ("p9", "decimal(20,3)"), ("p9", "decimal(38,3)"),
    ("p12", "decimal(18,4)"), ("p12", "decimal(20,4)"),
    ("p18", "decimal(20,6)"), ("p18", "decimal(38,6)"), ("p18", "decimal(20,8)"),
    ("p20", "decimal(38,6)"),
    ("p9", "decimal(5,3)"), ("p20", "decimal(18,6)"),
    ("u8", "tinyint"), ("u8", "int"), ("u8", "bigint"),
]
for col, typ in requests:
    outcomes = {}
    for form in ("flba", "int"):
        for variant in ("dict", "plain"):
            for vec in ("true", "false"):
                spark.conf.set("spark.sql.parquet.enableVectorizedReader", vec)
                key = "%s/%s/vec=%s" % (form, variant, vec)
                try:
                    df = spark.read.schema("id long, %s %s" % (col, typ)).parquet("%s/flat_%s_%s.parquet" % (work, form, variant))
                    rows = sorted(df.collect(), key=lambda r: r["id"])
                    want = expected["flat"][col]["values"]
                    got = [r[col] for r in rows]
                    same = sum(1 for g, w in zip(got, want) if (g is None and w is None) or (g is not None and w is not None and Decimal(str(g)) == Decimal(w)))
                    nulls = sum(1 for g, w in zip(got, want) if g is None and w is not None)
                    if same == len(want):
                        outcomes[key] = "values equal"
                    else:
                        outcomes[key] = "WRONG: %d of %d equal, %d became null" % (same, len(want), nulls)
                except Exception as e:
                    outcomes[key] = "error " + short(e)
    distinct = sorted(set(outcomes.values()))
    if len(distinct) == 1:
        print("RESULT SCHEMA %s as %s: all 8 combinations: %s" % (col, typ, distinct[0]))
    else:
        print("RESULT SCHEMA %s as %s: DIFFERS" % (col, typ))
        for k in sorted(outcomes):
            print("RESULT SCHEMA    %s: %s" % (k, outcomes[k]))

for typ in ("tinyint", "smallint", "int", "bigint", "decimal(3,0)"):
    for col in ("u8", "i16"):
        outcomes = {}
        for variant in ("dict", "plain"):
            for vec in ("true", "false"):
                spark.conf.set("spark.sql.parquet.enableVectorizedReader", vec)
                key = "%s/vec=%s" % (variant, vec)
                try:
                    df = spark.read.schema("id long, %s %s" % (col, typ)).parquet("%s/sorted_flba_%s.parquet" % (work, variant))
                    rows = sorted(df.collect(), key=lambda r: r["id"])
                    want = expected["sorted"]["u8"]["values"]
                    got = [r[col] for r in rows]
                    same = sum(1 for g, w in zip(got, want) if g is not None and int(g) == w)
                    outcomes[key] = "values equal" if same == len(want) else "WRONG: %d of %d equal" % (same, len(want))
                except Exception as e:
                    outcomes[key] = "error " + short(e)
        distinct = sorted(set(outcomes.values()))
        if len(distinct) == 1:
            print("RESULT INTSCHEMA %s (values 0 to 255) as %s: all 4 combinations: %s" % (col, typ, distinct[0]))
        else:
            for k in sorted(outcomes):
                print("RESULT INTSCHEMA %s (values 0 to 255) as %s: %s: %s" % (col, typ, k, outcomes[k]))

print("RESULT failures:", failures)
spark.stop()
sys.exit(1 if failures else 0)
