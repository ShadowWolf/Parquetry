# A byte column is annotated as an unsigned 8-bit integer

Status: accepted
Date: 2026-11-16

## Context

A Parquet column can carry an annotation that tells readers how to interpret
the stored values, for example that an INT32 holds an unsigned 8-bit number.
`byte` is unsigned in .NET.

Most unsigned types make the user choose how they are stored, under the
decision on
[types that need an explicit representation](0017-types-that-need-an-explicit-representation.md).
`byte` was exempted there because it is so common, so it needs a default. The
default first chosen for it was INT32 annotated as a signed 16-bit integer.

The comparison with pyarrow, which is this library's
[reference for what is written](0031-pyarrow-as-reference.md), showed that
other writers do it differently:

| Writer | How a byte is stored | How this is known |
|---|---|---|
| pyarrow 26.0.1 | INT32 with an unsigned 8-bit annotation | `docs/research/pyarrow-parity/output.txt` |
| Parquet.Net 6.0.3 | The same | Run with `docs/research/parquet-net-probe` |
| ParquetSharp | The same | Its source code, read on 2026-11-14 |

Spark was tested with a pyarrow-written unsigned 8-bit column, on versions
3.3.3, 3.4.4, 3.5.7, 4.0.5, and 4.1.4. Two things were found:

- Spark reads the column as `smallint`, a 16-bit integer, with every value
  correct. That is the same type it reads from the signed 16-bit form.
- Spark does not use the column's statistics to skip data. A query for
  `u8 = 200` scanned all 6,000 rows of the test file. The same values in a
  signed 16-bit column needed 500 rows or fewer. The results were right in
  both cases. Only the skipping is lost.

The test is in `docs/research/spark-decimal-check`.

## Options considered

1. Keep the signed 16-bit annotation. Spark can skip data on the column.
   Readers that understand unsigned annotations see a 16-bit signed column.
2. Write the unsigned 8-bit annotation, as pyarrow does. Readers see the true
   type. Spark reads every row of the column when filtering on it.

## Decision

Option 2. A `byte` column is INT32 with an unsigned 8-bit annotation, in every
profile.

The project owner chose this before the test showed that Spark stops skipping
data on such a column. That cost is listed as a point for the owner to
confirm, in the
[architecture overview](../architecture/README.md#open-questions).

## Consequences

- The library matches pyarrow and the other .NET libraries for the most common
  unsigned type.
- Readers that understand unsigned annotations, such as pyarrow, see the true
  type and range.
- A filter on a `byte` column is slower in Spark than it would be with the
  signed form, because Spark reads every row group. The answer is still
  right.
- An `enum` whose underlying type is `byte` is stored the same way and has the
  same cost.
- `byte` differs from `ushort`, `uint`, and `ulong` only in having a default.
  Those types still need an explicit choice. One of their choices is the
  unsigned annotation, which has the same filter cost in Spark.
- A `byte` column produces no compatibility message, the notice the writer
  gives for a setting that a reader of the profile handles badly. Choosing the
  unsigned annotation for a wider type does produce one, although Spark
  treats both the same way. The difference is that `byte` is a default the
  user did not choose, and a message on every `byte` column would be shown to
  nearly every user.
- When Spark writes such a column into a Delta table, it becomes `smallint`.
  Delta has no unsigned types.
- Databricks has not been tested. The tests against a live Databricks
  workspace, described in
  [Testing](../architecture/testing.md), must include a `byte` column and a
  filter on it. If Databricks fails to read the column, this decision is
  reopened.
