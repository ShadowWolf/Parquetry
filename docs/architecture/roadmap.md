# Roadmap

Work is ordered so that each milestone produces something external readers can
check. Each milestone is one or more pull requests that follow the rules in
`AGENTS.md`. Other documents, commit messages, pull requests, and issues refer
to a milestone by its name, not its number.

| # | Name | Scope | How it is checked |
|---|---|---|---|
| 0 | Documentation | Working rules, license, README, pull request template, decision records, architecture pages. No library code. | Review by the project owner |
| 1 | Solution and CI | Solution and project files, build settings, continuous integration, and the container setup for reader tests. | The reader test setup loads a known-good Parquet file |
| 2 | Flat files | Pages and footer. Flat rows of required simple values, PLAIN encoding, no compression, writing to a stream, with a hand-written shredder. | pyarrow and DuckDB read the files |
| 3 | Types and statistics | Nulls, text, dates, timestamps, decimals, the type rules, statistics, and the Spark version key. | Spark 3.5 and 4.x read the files. Filtered queries return the right rows. |
| 4 | Encodings and compression | Dictionary encoding. Snappy, LZ4_RAW, Gzip, and Brotli. The codec interface. | Every reader reads a file for each codec it supports. Spark has no Brotli codec, so Brotli is checked with the other readers. |
| 5 | Nested data | Nested objects, lists, and maps, with hand-written shredders. | Readers return the same nested values that were written |
| 6 | Source generator | The source generator with both ways of registering types, the runtime fallback, and the Native AOT test application. | Generated code produces files identical to those from the hand-written shredders of the Nested data milestone |
| 7 | Memory and public API | Memory budget, row groups, `NeedsFlush`, the high-level API, options, profiles, validation, and diagnostics. | Files with many row groups read correctly. A large write stays under a memory ceiling. |
| 8 | Staged layout | The staged layout and the temp-file destination. | Output is identical to the buffered layout |
| 9 | Page index and Modern profile | Page index. The `Modern` profile: data page version 2, delta encodings, BYTE_STREAM_SPLIT, and the Parquet types Spark cannot read. | The Java Parquet library reads the index. pyarrow reads `Modern` files. |
| 10 | Bloom filters | Bloom filters. | Readers use the filters and return the right rows |
| 11 | Encryption | Encryption. | pyarrow and Spark decrypt the files |
| 12 | Storage and integration packages | `Parquetry.Azure`, `Parquetry.S3`, the dependency injection package, and the synchronous package. | Emulator tests pass. Spark reads files from storage. |
| 13 | Performance and live tests | Parallel encoding. Benchmarks against `Parquet.Net` and `ParquetSharp`. Live tests against Databricks, Snowflake, BigQuery, and Redshift Spectrum. | Benchmark report. Successful live runs. |
| | Later | Zstd: a compressor written for this library, or the encoder built into .NET 11 if the library targets .NET 11 by then. Writing row groups with several writers and joining them into one file on the storage service, for files that are not encrypted. Possibly Arrow's schema in the file's metadata. Whether to add it, and whether it would be written by default, is not decided. | |

The first release is made when the Performance and live tests milestone is
complete. The items marked "Later" are not part of it.

## Status

Documentation is the current milestone. No library code exists.

## What is needed to continue

- Answers to the open questions in the
  [architecture overview](README.md#open-questions) before the milestone each
  one affects.
- Accounts and credentials for Databricks and the cloud warehouses before the
  Performance and live tests milestone.
