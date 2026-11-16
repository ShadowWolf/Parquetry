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
| 4 | Dictionary encoding. Snappy, LZ4_RAW, Gzip, and Brotli. The codec interface. | Every reader reads a file for each codec |
| 5 | Nested objects, lists, and maps, with hand-written shredders. | Readers return the same nested values that were written |
| 6 | The source generator with both ways of registering types, the runtime fallback, and the Native AOT test application. | Generated code produces files identical to those from milestone 5 |
| 7 | Memory budget, row groups, `NeedsFlush`, the high-level API, options, profiles, validation, and diagnostics. | Files with many row groups read correctly. A large write stays under a memory ceiling. |
| 8 | The staged layout and the temp-file destination. | Output is identical to the buffered layout |
| 9 | Page index. The `Modern` profile: data page version 2, delta encodings, BYTE_STREAM_SPLIT, and the Parquet types Spark cannot read. | The Java Parquet tools validate the index. pyarrow reads `Modern` files. |
| 10 | Bloom filters. | Readers use the filters and return the right rows |
| 11 | Encryption. | pyarrow and Spark decrypt the files |
| 12 | `Parquetry.Azure`, `Parquetry.S3`, the dependency injection package, and the synchronous package. | Emulator tests pass. Spark reads files from storage. |
| 13 | Parallel encoding. Benchmarks against `Parquet.Net` and `ParquetSharp`. Live tests against Databricks, Snowflake, BigQuery, and Redshift Spectrum. | Benchmark report. Successful live runs. |
| Later | A Zstd compressor written for this library. Joining row groups from several writers on the storage service. | |

## Status

Milestone 0 is written and awaiting review. No library code exists.

## What is needed to continue

- A GitHub repository. Pull requests and continuous integration depend on it.
- Answers to the open questions in the
  [architecture overview](README.md#open-questions) before the milestone each
  one affects. The type mapping questions are needed for milestone 3.
- Accounts and credentials for Databricks and the cloud warehouses before
  milestone 13.
