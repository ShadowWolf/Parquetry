# Testing

The library does not read Parquet, so its tests rely on other tools to confirm
that its files are correct.

## Kinds of test

| Kind | What it checks | Project |
|---|---|---|
| Unit tests | Encodings, level assignment, Thrift output, statistics, and codecs against known byte sequences and reference implementations. | `Parquetry.Tests` |
| Generator tests | The code the source generator produces for a set of types, and the build errors it reports. | `Parquetry.Generators.Tests` |
| Reader tests | Files written by the library are read by pyarrow, Polars, DuckDB, and Spark. Values and schema are compared with what was written. | `Parquetry.Interop.Tests` |
| Same-output tests | Two paths that should give the same file do so, byte for byte: generated code and the runtime fallback, and the buffered and staged layouts. | `Parquetry.Tests` |
| Memory tests | A large write with a fixed budget stays under a measured ceiling. | `Parquetry.Tests` |
| AOT test | An application published with Native AOT writes a file, and the build has no trimming warnings. | `Parquetry.Aot.Tests` |
| Storage tests | The S3 and Azure destinations against emulators, and against live services when credentials are supplied. | `Parquetry.Cloud.Tests` |
| Benchmarks | Throughput and allocation, compared with `Parquet.Net` and `ParquetSharp`. | `Parquetry.Benchmarks` |

## Reader tests

Every feature that changes what goes into a file has reader tests. A test
writes a file, asks each reader to load it, and compares the result with the
input.

Statistics, the page index, and bloom filters need a further check, because an
error in them does not stop a file from loading. It makes a reader skip rows
that match a query. For these features, tests run filtered queries in Spark and
DuckDB and compare the rows returned with the rows expected. The test data
includes the cases most likely to go wrong: NaN, positive and negative zero,
empty strings, strings that differ in bytes above 127, and nulls.

## Two tiers

| Tier | Runs | Readers and services |
|---|---|---|
| Containers | On every pull request | pyarrow, Polars, DuckDB, Spark 3.5, the current Spark 4.x, an Azure emulator, an S3 emulator |
| Live | When credentials are supplied, on a schedule or started by hand | Databricks with Photon on and off, Snowflake, BigQuery, Redshift Spectrum, Azure Blob Storage, Amazon S3 |

A pull request can pass without the live tier. A release requires a recent
successful live run.

## Compressors

The Snappy and LZ4 compressors are written for this library, so they get extra
testing. Their output is decompressed with reference implementations and
compared with the input, over randomly generated data and over inputs built to
reach edge cases: empty input, incompressible data, long runs of one byte, and
matches at the limits of the format's offsets.

## Red testing

Each new or changed test must be seen to fail before it is accepted. The author
runs it against code without the change, or breaks the behavior on purpose, and
confirms that the test fails for the reason it was written to catch. The pull
request records how this was done. The rule is in `AGENTS.md`.

## Commands

Build and test commands will be added to `AGENTS.md` when the solution is
created.
