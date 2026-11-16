# Research programs

Several decision records say that the behavior of another library was "checked
by running it". The programs used for those checks are kept here so that the
checks can be repeated. They are not part of the library, are not built by the
solution, and are not held to its coding rules.

## Parquet.Net

`parquet-net-probe` writes one row for each of a set of .NET types with
Parquet.Net and prints the schema Parquet.Net wrote, the value read back, or
the error. It was run on 2026-11-14 with Parquet.Net 6.0.3 on .NET 10. Its
`byte` case is quoted in the decision record on
[the byte annotation](../adr/0035-byte-annotation.md), and its enum case on
the [pyarrow parity](../architecture/pyarrow-parity.md) page.

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

## Spark reading pyarrow's decimals and unsigned bytes

The folder `spark-decimal-check` holds a test that Spark reads decimals stored
the way pyarrow stores them, and unsigned 8-bit columns.

- `make_files.py` writes the test files with pyarrow. Each table is written
  with decimals as fixed-length bytes, pyarrow's default, and again with small
  decimals as INT32 and INT64.
- `check.py` reads the files with Spark and compares them with what was
  written. It has four parts: every value of flat columns, every value of
  nested columns, filters on sorted columns with the number of rows Spark had
  to scan, and reads that ask for a type different from the file's. It exits
  with status 1 if a comparison fails.
- `run.sh` runs both for Spark 3.3.3, 3.4.4, 3.5.7, 4.0.5, and 4.1.4, using
  the `apache/spark` container images. It needs `uv` and Docker.
- `results` holds the output from 2026-11-16: `files.txt` shows what pyarrow
  wrote, and there is one file per Spark version.

```
sh docs/research/spark-decimal-check/run.sh
```

The lines in the results that start with `RESULT SCHEMA` and `RESULT
INTSCHEMA` report reads with a mismatched type. Errors and wrong values are
expected there. They show how Spark behaves, and they do not count as
failures.

Its results are quoted in the decision records on
[decimal storage](../adr/0036-decimal-storage.md) and
[the byte annotation](../adr/0035-byte-annotation.md), and on the
[Spark and Databricks compatibility](../architecture/spark-and-databricks-compatibility.md)
page.

## Size of decimal columns

`pyarrow-parity/decimal_size.py` writes 1,000,000 decimal values with pyarrow
in each storage form, under several encodings and codecs, and prints the size
of the column. It also prints the statistics pyarrow writes for a fixed-length
decimal. Its output from 2026-11-16 is saved as `decimal_size_output.txt`.

```
uv run --no-project --with pyarrow==26.0.1 python docs/research/pyarrow-parity/decimal_size.py
```

## Output files

The pyarrow programs write small Parquet files to the folder they are run
from and overwrite or remove them. `run.sh` writes its test files to a temp
folder. None of these files is kept in the repository.
