# pyarrow is the reference for what is written to a file

Status: accepted
Date: 2026-11-16

## Context

Many choices in a Parquet writer have more than one valid answer: how a small
decimal is stored, what happens when a timestamp loses digits, how a list is
laid out, whether a page index is written. pyarrow is the Python library of
the Apache Arrow project, and its Parquet writer is one that many of this
library's users will already know.

Two decisions had already been made by checking pyarrow. A timestamp that does
not fit in microseconds raises an error unless the user allows truncation, and
when truncation is allowed the value moves toward 1970.

## Options considered

1. Decide each case on its own merits.
2. Treat pyarrow's default behavior as the reference, and depart from it only
   for a recorded reason.

## Decision

Option 2. The library writes what pyarrow writes by default, unless there is a
recorded reason not to.

- This covers everything that ends up in the file: how each type is stored,
  how nested data is laid out, which statistics and optional structures are
  written, and what happens to a value that does not fit.
- Default sizes, such as rows in a row group, start from pyarrow's values and
  are then set from benchmarks.
- The usual reason for a departure is that Spark cannot read what pyarrow
  writes. Reading by Spark without settings is also a goal.
- pyarrow's behavior is established by running it, not from memory or from
  documentation alone. The programs and their output are kept in
  `docs/research`.

pyarrow writes Arrow data, so each .NET type is compared with a stated Arrow
type. The list is on the parity page.

## Consequences

- Each new decision about written output starts with a pyarrow run.
- [pyarrow parity](../architecture/pyarrow-parity.md) lists every comparison
  made so far: where the library matches, where it differs on purpose and
  why, and where a difference is still to be decided.
- The first comparison, on 2026-11-16 against pyarrow 26.0.1, found that under
  the default profile each way the library stores a type or lays out nested
  data is one pyarrow itself writes, by default or with an option, and reads
  back. No Parquetry file exists yet, so this is not the same as pyarrow
  having read one. The reader tests will confirm it.
- That comparison also found differences that had no decision behind them. The
  parity page lists the ones that are still open.
- pyarrow's defaults change between its versions. The parity page records the
  version checked, and the comparison should be run again before each release
  of this library.
