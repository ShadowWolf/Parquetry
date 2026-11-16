# Architecture overview

Parquetry writes .NET objects to Parquet files. This page describes the parts
of the library and how data moves through them. Each part has its own page,
linked below. The reasons for the design are in the
[decision records](../adr/README.md).

No library code exists yet. These pages describe the intended design, and code
sketches in them show the shape of an interface and not its final form.

## Packages

| Package | Contents |
|---|---|
| `Parquetry` | Schema, row shredding, encodings, codecs, file format, layouts, stream and temp-file destinations, options and profiles, diagnostics. Includes the source generator. No dependencies. |
| `Parquetry.Azure` | A destination for Azure Blob Storage that stages blocks per column. |
| `Parquetry.S3` | A destination for Amazon S3 that uses multipart upload with parallel parts. |
| `Parquetry.Extensions.DependencyInjection` | Service registration, configuration binding, named profiles, writer factory. |
| `Parquetry.Sync` | Synchronous wrappers over the async API. |

## How a row becomes bytes in a file

1. Shred. Code produced by the source generator reads one row and appends each
   value to a buffer for its column, along with two small numbers that record
   nesting and nulls. This step does not allocate.
2. Encode and compress. When a column's buffer holds a page worth of values,
   the column writer encodes and compresses them into memory owned by the
   layout. This happens inside the `Write` call and does no I/O.
3. Place. The layout decides where the page bytes go. The buffered layout
   keeps them until the row group is complete. The staged layout sends them to
   storage as they are finished.
4. Commit. When a row group closes, the layout reports where each column's
   bytes ended up. Core works out the positions and, at the end of the file,
   writes the page index, bloom filters, and footer.

All I/O happens in `FlushAsync` and `CompleteAsync`. Disposing a writer without
calling `CompleteAsync` aborts the file.

## Pages in this section

| Page | Covers |
|---|---|
| [Parquet format notes](parquet-format-notes.md) | The parts of the file format the design depends on, and storage service limits. |
| [Schema and type mapping](schema-and-type-mapping.md) | How .NET types map to Parquet types. |
| [Shredding and the source generator](shredding-and-source-generator.md) | How rows are split into columns, and what the generator produces. |
| [Encoding and compression](encoding-and-compression.md) | Value encodings and codecs. |
| [File format writing](file-format-writing.md) | Pages, footer, statistics, page index, bloom filters, encryption. |
| [Layouts and destinations](layouts-and-destinations.md) | Where page bytes go and how files are committed. |
| [Memory](memory.md) | The memory budget and buffer ownership. |
| [Options and profiles](options-and-profiles.md) | Configuration, profiles, and validation. |
| [Public API](public-api.md) | The writer, dependency injection, and the synchronous package. |
| [Spark and Databricks compatibility](spark-and-databricks-compatibility.md) | What Spark and Databricks can read, from research. |
| [Testing](testing.md) | How the output is verified. |
| [Roadmap](roadmap.md) | The order of work. |

## Repository layout

```
AGENTS.md  CLAUDE.md  LICENSE  README.md
.github/                           pull request template, workflows
docs/adr/                          decision records
docs/architecture/                 these pages
src/Parquetry/
  Schema/  Shredding/  Encoding/  Compression/  Format/
  Layout/  IO/  Memory/  Options/  Encryption/  Diagnostics/
src/Parquetry.Generators/
src/Parquetry.Azure/
src/Parquetry.S3/
src/Parquetry.Extensions.DependencyInjection/
src/Parquetry.Sync/
tests/Parquetry.Tests/             unit tests
tests/Parquetry.Generators.Tests/  checks on generated code
tests/Parquetry.Interop.Tests/     pyarrow, Polars, DuckDB, Spark in containers
tests/Parquetry.Aot.Tests/         an app published with Native AOT
tests/Parquetry.Cloud.Tests/       storage emulators and live services
benchmarks/Parquetry.Benchmarks/
```

Only the documentation files exist today.

## Open questions

These have not been decided. Each will get a decision record when it is.

| Question | Where it matters |
|---|---|
| How does a user leave a property out of the file, and can a user supply their own conversion for a type? | [Schema and type mapping](schema-and-type-mapping.md) |
| What exact value is written for the Spark version key? | [File format writing](file-format-writing.md) |
| What are the default page size, row group size, and memory budget? These will be set from benchmarks. | [Memory](memory.md) |
| Who is named as copyright holder in `LICENSE`? It currently names Bryan Wolf. | `LICENSE` |
