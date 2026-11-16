# Research programs

Several decision records say that the behavior of another library was "checked
by running it". The programs used for those checks are kept here so that the
checks can be repeated. They are not part of the library, are not built by the
solution, and are not held to its coding rules.

## Parquet.Net

`parquet-net-probe` writes one row for each of a set of .NET types with
Parquet.Net and prints the schema Parquet.Net wrote, the value read back, or
the error. It was run on 2026-11-14 with Parquet.Net 6.0.3 on .NET 10. Its
`byte` case is also quoted on the
[pyarrow parity](../architecture/pyarrow-parity.md) page.

```
dotnet run --project docs/research/parquet-net-probe
```

Its results are quoted in the decision records on
[required columns](../adr/0025-required-columns-from-nullable-annotations.md),
[enums](../adr/0026-enum-mapping.md),
[TimeSpan](../adr/0027-timespan-needs-an-explicit-representation.md),
[unsupported types](../adr/0028-unsupported-types-in-first-release.md), and
[timestamp precision](../adr/0029-timestamp-precision-loss.md).

## pyarrow

`pyarrow-timestamp-probe.py` writes two nanosecond timestamps with pyarrow
under several settings and prints what was stored or the error raised. One of
the two values is just before 1970, which shows the direction in which pyarrow
truncates. It was run on 2026-11-14 with pyarrow 26.0.1 and pandas 3.1.1.

```
uv run --no-project --with pyarrow==26.0.1 --with pandas==3.1.1 python docs/research/pyarrow-timestamp-probe.py
```

Its results are quoted in the decision record on
[timestamp precision](../adr/0029-timestamp-precision-loss.md).

The folder `pyarrow-parity` holds the program behind the
[pyarrow parity](../architecture/pyarrow-parity.md) page.

- `probe.py` writes small files with pyarrow for the cases that page compares
  and prints what pyarrow wrote: the schema, the encodings, the statistics
  fields, the page index, and pyarrow's default settings.
- `compact_thrift.py` decodes the raw footer, because pyarrow's API does not
  show every field, such as which statistics fields are present.
- `output.txt` is the output of the run on 2026-11-16 with pyarrow 26.0.1. The
  parity page can be checked against it without running anything.

```
uv run --no-project --with pyarrow==26.0.1 python docs/research/pyarrow-parity/probe.py
```

## Spark reading pyarrow's decimals

The folder `spark-decimal-check` holds a test that Spark reads decimals stored
the way pyarrow stores them, and an unsigned 8-bit column.

- `make_files.py` writes two files with pyarrow. Each has a decimal column at
  every precision from 1 to 38 and an unsigned 8-bit column. One file uses
  pyarrow's default storage, fixed-length bytes. The other uses INT32 and
  INT64 for small decimals.
- `check.py` reads both files with Spark, with the vectorized reader on and
  off, and compares every value with what was written.
- `results.txt` is the output from 2026-11-16 for Spark 3.5.7, 4.0.5, and
  4.1.4, run from the `apache/spark` container images.

```
mkdir work
uv run --no-project --with pyarrow==26.0.1 python docs/research/spark-decimal-check/make_files.py work
cp docs/research/spark-decimal-check/check.py work/
docker run --rm -v "$PWD/work":/work:ro apache/spark:3.5.7-java17-python3 \
  /opt/spark/bin/spark-submit --master "local[2]" /work/check.py /work
```

Its results are quoted in the decision records on
[decimal storage](../adr/0036-decimal-storage.md) and
[the byte annotation](../adr/0035-byte-annotation.md).

The programs write their output files next to where they run. Those files are
not kept.
