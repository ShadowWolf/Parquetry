# Research programs

Several decision records say that the behavior of another library was "checked
by running it". The programs used for those checks are kept here so that the
checks can be repeated. They are not part of the library, are not built by the
solution, and are not held to its coding rules.

## Parquet.Net

`parquet-net-probe` writes one row for each of a set of .NET types with
Parquet.Net and prints the schema Parquet.Net wrote, the value read back, or
the error. It was run on 2026-11-14 with Parquet.Net 6.0.3 on .NET 10.

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
uv run --no-project --with pyarrow --with pandas python docs/research/pyarrow-timestamp-probe.py
```

Its results are quoted in the decision record on
[timestamp precision](../adr/0029-timestamp-precision-loss.md).

Both programs write their output files next to where they run. Those files are
not kept.
