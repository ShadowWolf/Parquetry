# A value that cannot be written ends the write

Status: accepted
Date: 2026-11-16

## Context

The writer's `Write` method raises an error when a value cannot be stored as
the schema requires. The cases documented so far are:

- A null in a required column.
- A decimal that does not fit its precision and scale.
- A `DateTime` of kind `Unspecified` when no policy is set for such values.
- A `DateTime`, `DateTimeOffset`, `TimeOnly`, or `TimeSpan` that would lose
  digits when truncation has not been allowed.
- A timestamp outside the range a nanosecond column can hold.

The error is raised partway through a row, after some columns have already
received their values for that row. The columns then do not all hold the same
number of rows.

## Options considered

1. The writer cannot continue after the error. The caller disposes it, and the
   file is aborted.
2. The writer undoes the partial row, so that the caller can skip the row and
   continue.

## Decision

Option 1. A value error ends the write. This applies to every case listed
above and to any value error added later.

## Consequences

- One bad value in a long write loses the file. A caller who expects bad data
  checks or cleans rows before writing them.
- `Write` does not need to record where each column stood at the start of
  every row, which keeps the per-row path short.
- After the error, every method on the writer except `DisposeAsync` raises an
  error. Disposing aborts the destination. What an abort leaves behind for
  each kind of destination is described in
  [Layouts and destinations](../architecture/layouts-and-destinations.md).
- The error names the column and describes what is wrong with the value. With
  the low-level `Write` method, the row at fault is the one the caller just
  passed. Whether the error also reports the row's position, for callers who
  pass a whole sequence, is a detail to settle when the API is built.
- A limit that raises an error during a write ends it in the same way. The row
  group limit of an encrypted file is one, and a used-up reserved share of the
  memory budget is another. What happens when a staged destination runs out
  of segments is still an open question.
