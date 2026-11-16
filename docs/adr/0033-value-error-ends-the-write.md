# A value that cannot be written ends the write

Status: accepted
Date: 2026-11-16

## Context

`Write` raises an error when a value cannot be stored as the schema requires:
a null in a required column, a decimal that does not fit its precision and
scale, or a timestamp that would lose precision. The error is raised partway
through a row, after some columns have already received their values for that
row. The columns are then out of step with each other.

## Options considered

1. The writer cannot continue after the error. The caller disposes it, and the
   file is aborted.
2. The writer undoes the partial row, so that the caller can skip the row and
   continue.

## Decision

Option 1. A value error ends the write.

## Consequences

- One bad value in a long write loses the file. A caller who expects bad data
  checks or cleans rows before writing them.
- `Write` does not need to record where each column stood at the start of
  every row, which keeps the per-row path short.
- A file is never completed with rows silently left out.
- After the error, every method on the writer except `DisposeAsync` raises an
  error. Disposing aborts the destination.
- The error names the column and describes the value's problem, so the caller
  can find the row.
