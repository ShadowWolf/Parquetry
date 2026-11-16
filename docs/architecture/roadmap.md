# Roadmap

Work is ordered so that each milestone produces something external readers can
check. Each milestone is one or more pull requests that follow the rules in
`AGENTS.md`.

| # | Scope | How it is checked |
|---|---|---|
| 0 | Working rules, license, README, pull request template, decision records, architecture pages. No library code. | Review by the project owner |
| 1 | Solution and project files, build settings, continuous integration, and the container setup for reader tests. | The reader test setup loads a known-good Parquet file |
| 2 | Pages and footer. Flat rows of required simple values, PLAIN encoding, no compression, writing to a stream, with a hand-written shredder. | pyarrow and DuckDB read the files |
| 3 | Nulls, text, dates, timestamps, decimals, the type rules, statistics, and the Spark version key. | Spark 3.5 and 4.x read the files. Filtered queries return the right rows. |
| 4 | Dictionary encoding. Snappy, LZ4_RAW, Gzip, and Brotli. The codec interface. | Every reader reads a file for each codec it supports. Spark has no Brotli codec, so Brotli is checked with the other readers. |
| 5 | Nested objects, lists, and maps, with hand-written shredders. | Readers return the same nested values that were written |
| 6 | The source generator with both ways of registering types, the runtime fallback, and the Native AOT test application. | Generated code produces files identical to those from the hand-written shredders of the nested types milestone |
| 7 | Memory budget, row groups, `NeedsFlush`, the high-level API, options, profiles, validation, and diagnostics. | Files with many row groups read correctly. A large write stays under a memory ceiling. |
| 8 | The staged layout and the temp-file destination. | Output is identical to the buffered layout |
| 9 | Page index. The `Modern` profile: data page version 2, delta encodings, BYTE_STREAM_SPLIT, and the Parquet types Spark cannot read. | The Java Parquet library reads the index. pyarrow reads `Modern` files. |
| 10 | Bloom filters. | Readers use the filters and return the right rows |
| 11 | Encryption. | pyarrow and Spark decrypt the files |
| 12 | `Parquetry.Azure`, `Parquetry.S3`, the dependency injection package, and the synchronous package. | Emulator tests pass. Spark reads files from storage. |
| 13 | Parallel encoding. Benchmarks against `Parquet.Net` and `ParquetSharp`. Live tests against Databricks, Snowflake, BigQuery, and Redshift Spectrum. | Benchmark report. Successful live runs. |
| Later | A Zstd compressor written for this library. Writing row groups with several writers and joining them into one file on the storage service, for files that are not encrypted. | |

The first release is made when milestone 13 is complete. The items marked
"Later" are not part of it.

## Status

Milestone 0, the documentation, is the current milestone. No library code
exists.

## What is needed to continue

- Answers to the open questions in the
  [architecture overview](README.md#open-questions) before the milestone each
  one affects. The question about target frameworks is needed first, because
  the project files depend on it.
- Accounts and credentials for Databricks and the cloud warehouses before the
  milestone that runs the live tests.
