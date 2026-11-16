# A byte column is annotated as an unsigned 8-bit integer

Status: accepted
Date: 2026-11-16

## Context

`byte` is unsigned in .NET. The decision on
[types that need an explicit representation](0017-types-that-need-an-explicit-representation.md)
exempted it from having to choose a form, because it is so common. That
record stored it as INT32 annotated as a signed 16-bit integer under the
default profile, on the grounds that the default profile writes no unsigned
annotations.

The comparison with pyarrow showed that this is the one place where that rule
buys nothing:

| Writer | How a byte is stored |
|---|---|
| pyarrow 26.0.1 | INT32 with an unsigned 8-bit annotation. Checked by running it. |
| Parquet.Net 6.0.3 | The same. Checked by running it. |
| ParquetSharp | The same, according to its source code. |

Spark reads the unsigned 8-bit form as a 16-bit integer. That was read in
Spark's source earlier and has now been tested: Spark 3.5.7, 4.0.5, and 4.1.4
each read a pyarrow-written unsigned 8-bit column as `smallint`, with the
values intact. A 16-bit integer is also what Spark reads from the signed form.

## Options considered

1. Keep the signed 16-bit annotation.
2. Write the unsigned 8-bit annotation, as pyarrow does.

## Decision

Option 2. A `byte` column is INT32 with an unsigned 8-bit annotation, in every
profile.

## Consequences

- The library matches pyarrow and the other .NET libraries for the most common
  unsigned type.
- Readers that understand unsigned annotations, such as pyarrow, see the true
  type and range. Before this change they would have seen a signed 16-bit
  column.
- `byte` is the one unsigned type the default profile writes with an unsigned
  annotation. `ushort`, `uint`, and `ulong` still need an explicit choice,
  because Spark reads them as a wider type than the user declared and the user
  should decide what readers see.
- A `byte` column produces no compatibility message.
- Databricks has not been tested. The live test against Databricks includes a
  `byte` column.
