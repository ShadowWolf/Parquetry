# The library writes Parquet and does not read it

Status: accepted
Date: 2026-11-14

## Context

A Parquet library can write files, read them, or both. A reader roughly doubles
the work and the public API. The purpose of this library is fast writing with
bounded memory.

## Options considered

1. Write only, with the output checked by external readers.
2. Write only, plus a small reader inside the test projects for round-trip
   checks.
3. A public reader as well as a writer.

## Decision

The library only writes. Tests check the output by reading it with Apache
Spark, pyarrow, Polars, and DuckDB.

## Consequences

- Checking against independent readers tests what users need, which is that
  other tools can read the files. A reader written by the same team could
  share the writer's misunderstandings of the format.
- The compression code only needs compressors. Decompression in tests uses
  reference implementations as test-only dependencies.
- Tests that read output need containers with those tools, which makes them
  slower than plain unit tests.
- Users who need to read Parquet in .NET use another library.
