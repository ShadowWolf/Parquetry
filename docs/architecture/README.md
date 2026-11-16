# Architecture overview

Parquetry writes .NET objects to Parquet files. This page describes the parts
of the library and how data moves through them. Each part has its own page,
linked below. The reasons for the design are in the
[decision records](../adr/README.md).

No library code exists yet. These pages describe the intended design, and code
sketches in them show the shape of an interface and not its final form.

If Parquet's terms are new to you, read
[Parquet format notes](parquet-format-notes.md) first.

## Terms

| Term | Meaning |
|---|---|
| Row group | A run of rows stored together. A file is a series of row groups. |
| Column chunk | The stored data of one column within one row group. |
| Page | A piece of a column chunk, holding a few thousand values. Pages are the unit that is encoded and compressed. |
| Footer | The metadata at the end of the file: the schema and the position of every column chunk. |
| Page index | Optional metadata that records the value range and position of every page. |
| Bloom filter | Optional metadata that lets a reader rule out a column chunk when looking for one value. |
| Core | The main package, `Parquetry`. |
| Destination | Where the file's bytes go: a stream, an S3 object, an Azure blob. |
| Layout | The part of core that decides when page bytes are sent to the destination and in what arrangement. |
| Profile | A named set of defaults chosen so that a particular group of readers can read the file. |

## Packages

| Package | Contents |
|---|---|
| `Parquetry` | Schema, row shredding, encodings, codecs, file format, layouts, stream and temp-file destinations, options and profiles, diagnostics. Includes the source generator. No dependencies. |
| `Parquetry.Azure` | A destination for Azure Blob Storage that uploads data as blocks while a row group is still open. |
| `Parquetry.S3` | A destination for Amazon S3 that uses multipart upload with parallel parts. |
| `Parquetry.Extensions.DependencyInjection` | Service registration, configuration binding, named options, writer factory. |
| `Parquetry.Sync` | Synchronous wrappers over the async API. |

## How a row becomes bytes in a file

1. Shred. Code produced by the source generator reads one row and appends each
   value to a buffer for its column, along with two small numbers that record
   nesting and nulls. This step does not allocate.
2. Encode and compress. When a column's buffer holds a page worth of values,
   the column writer encodes and compresses them into memory owned by the
   layout. Steps 1 and 2 happen inside the writer's synchronous `Write` method
   and do no I/O.
3. Place. The layout decides where the page bytes go. The buffered layout
   keeps them until the row group is complete. The staged layout sends them to
   storage at the next flush, without waiting for the row group to close.
4. Commit. When a row group closes, the layout reports where each column's
   bytes ended up, and core writes that row group's bloom filters. At the end
   of the file, core writes the page index and the footer.

`Write` does no I/O. I/O happens when the caller flushes or completes the
writer, and the high-level `WriteAsync` methods flush on the caller's behalf.
Disposing a writer without calling `CompleteAsync` aborts the file. The
methods are described in [Public API](public-api.md).

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
docs/research/                     programs used to check how other libraries behave
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

This is the planned layout. Only the documentation files exist so far.

## Open questions

### Decisions still open

Each of these gets a decision record when it is made.

| Question | Where it matters |
|---|---|
| Should the target frameworks change? .NET 8 reached end of support on 2026-11-10, and .NET 11 was released the same day. | [Target frameworks](../adr/0002-target-frameworks.md) |
| Should the library use the Zstandard and Gzip encoders that .NET 11 adds, and is a Zstd compressor written for this library still needed? | [Encoding and compression](encoding-and-compression.md) |
| What does the writer do when page index and footer data, which a flush cannot free, approach the memory budget? | [Memory](memory.md) |
| When several writers share a budget, which one is asked to flush? | [Memory](memory.md) |
| How does a destination charge the memory it holds to the budget? | [Memory](memory.md) |
| Where does parallel encoding run, given that `Write` is synchronous? | [Memory](memory.md) |
| After a value error, should the writer undo the partial row so the caller can continue? Today the write ends. | [Public API](public-api.md) |
| What state is the writer in after a flush or completion fails or is cancelled, and can it be retried? | [Layouts and destinations](layouts-and-destinations.md) |
| How does a user leave a property out of the file, and can a user supply their own conversion for a type? | [Schema and type mapping](schema-and-type-mapping.md) |
| Does a string that is not valid text raise an error, or is the invalid part replaced? | [Shredding and the source generator](shredding-and-source-generator.md) |
| Which ordering is declared for floating-point statistics under each profile: the original one or IEEE 754 total order? | [File format writing](file-format-writing.md) |
| What exact value is written for the Spark version key? | [File format writing](file-format-writing.md) |
| What are the default page size, row group size, dictionary size limit, and memory budget? These will be set from benchmarks. | [Memory](memory.md) |
| For the `Modern` profile: the default codec, whether it writes the Spark version key, how it picks an encoding for a column, and how it annotates `byte`. | [Options and profiles](options-and-profiles.md) |
| Is a `Databricks` profile needed? Live tests against Databricks will show. | [Options and profiles](options-and-profiles.md) |
| Who is named as copyright holder in `LICENSE`? It currently names Bryan Wolf. | `LICENSE` |

### Details left until the feature is built

These are smaller points. Each is settled in the pull request that builds the
feature.

| Detail | Where it matters |
|---|---|
| The names of the attributes that choose a representation, rename a column, or set decimal precision. | [Schema and type mapping](schema-and-type-mapping.md) |
| Which members and collection types are written: fields, init-only properties, interfaces such as `IReadOnlyList<T>`. | [Schema and type mapping](schema-and-type-mapping.md) |
| The text format for a `TimeSpan`, and whether TIME is offered as a choice for it. | [Schema and type mapping](schema-and-type-mapping.md) |
| How an enum written as text is annotated, and how `[Flags]` combinations and unnamed numbers are written. | [Schema and type mapping](schema-and-type-mapping.md) |
| Which setting wins when a column is configured both by an attribute and in options, and how options name nested and renamed columns. | [Options and profiles](options-and-profiles.md) |
| How compatibility messages are reported, how further profiles are registered, and how a codec is registered. | [Options and profiles](options-and-profiles.md) |
| The interface through which a user supplies encryption keys. | [File format writing](file-format-writing.md) |
| Whether the writer closes a stream the caller gave it. | [Layouts and destinations](layouts-and-destinations.md) |
| The exact signatures of the methods that create a writer. | [Public API](public-api.md) |
