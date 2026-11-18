# Testing

The library does not read Parquet, so its tests rely on other tools to confirm
that its files are correct.

## Kinds of test

| Kind | What it checks | Project |
|---|---|---|
| Unit tests | Encodings, level assignment, Thrift output, statistics, and codecs against known byte sequences and reference implementations. | `Parquetry.Tests` |
| Generator tests | The code the source generator produces for a set of types, and the build errors it reports. | `Parquetry.Generators.Tests` |
| Reader tests | Files written by the library are read by pyarrow, Polars, DuckDB, and Spark. Values and schema are compared with what was written. | `Parquetry.Interop.Tests` |
| Same-output tests | Two paths that should give the same file do so, byte for byte: generated code and the runtime fallback, and the buffered and staged layouts. The layout comparison fixes the page size and uses a budget that never closes a row group early. | `Parquetry.Tests` |
| Memory tests | A large write with a fixed budget stays under a measured ceiling. | `Parquetry.Tests` |
| AOT test | An application published with Native AOT writes a file, and the build has no trimming warnings. | `Parquetry.Aot.Tests` |
| Storage tests | The S3 and Azure destinations against emulators, and against live services when credentials are supplied. | `Parquetry.Cloud.Tests` |
| Benchmarks | Throughput and allocation, compared with `Parquet.Net` and `ParquetSharp`. | `Parquetry.Benchmarks` |

`Parquetry.Tests` and `Parquetry.Interop.Tests` exist. Each other project is
added by the milestone that first needs it.

## Reader tests

Every feature that changes what goes into a file has reader tests. A test
writes a file, asks each reader to load it, and compares the result with the
input.

Statistics, the page index, and bloom filters need a further check, because an
error in them does not stop a file from loading. It makes a reader skip rows
that match a query. For these features, tests run filtered queries in Spark and
DuckDB and compare the rows returned with the rows expected. The test data
includes the cases most likely to go wrong: NaN, a page whose values are all
NaN, positive and negative zero, empty strings, strings that differ in bytes
above 127, and nulls.

A correct result proves nothing if the reader never looked at the structure
under test. Each of these tests therefore also shows that the reader used it,
either from the reader's own metrics or by writing a deliberately wrong filter
or index and confirming that rows go missing. Which readers use each structure
by default has not been checked yet.

### How a test reaches a reader

The readers run in three containers: one for pyarrow, Polars, and DuckDB, one
for Spark 3.5, and one for the current Spark 4.x. The containers start once
for the whole test run and are stopped when it ends. Each runs a small HTTP
server. A test sends a file's bytes to a reader and gets back the columns and
rows the reader saw, and the test compares them with what it wrote. A test
that takes a reader's name runs once for each of the five readers.

| Part | Where it is |
|---|---|
| The Dockerfiles, the server, and the Python code that calls each reader | `tests/Parquetry.Interop.Tests/Containers` |
| The requests the server accepts and the form of its answers | The comment at the top of `reader_server.py` in that folder |
| The C# code that starts the containers and sends files | `tests/Parquetry.Interop.Tests/Readers` |
| The versions of pyarrow, Polars, and DuckDB | `requirements.txt` in the containers folder |
| The versions of Spark and Python | The first line of each Dockerfile |

A reader's answer is one of two things: a table, or the reader's error
message when it could not read the file. If the server itself fails, the test
fails with an error from the test setup, so a test that expects a reader to
reject a file cannot pass because the setup broke.

The server knows a column's type by a name that is the same for every
reader, such as `int64`. The list of names is in `reader_server.py`. It holds
only the types the tests have used so far, and a feature that writes a new
type adds to it.

The library writes no files yet. Until it does, the tests in
`ReaderSetupTests.cs` check the setup itself with a small file that pyarrow
writes in its container. Every reader must return the values that were
written, and every reader must report an error when the file is cut short.

The reasons for this design are in the decision record
[reader tests send files to reader containers that stay running](../adr/0039-reader-containers-that-stay-running.md).

## Two tiers

| Tier | Runs | Readers and services |
|---|---|---|
| Containers | On every pull request | pyarrow, Polars, DuckDB, Spark 3.5, the current Spark 4.x, an Azure emulator, an S3 emulator. The emulators are added with the storage packages. |
| Live | When credentials are supplied, on a schedule or started by hand | Databricks with Photon on and off, Snowflake, BigQuery, Redshift Spectrum, Azure Blob Storage, Amazon S3 |

A pull request can pass without the live tier. A release requires a recent
successful live run.

## Continuous integration

The workflow in `.github/workflows/ci.yml` runs for every pull request and
for every push to `main`.

| Job | What it does | Runs on |
|---|---|---|
| Unit tests | Builds the solution and runs `Parquetry.Tests` with .NET 10. | Linux and Windows on x64, macOS on Arm64 |
| Unit tests on the .NET 11 runtime | Runs the same `net10.0` test build on the .NET 11 runtime. | Linux |
| Reader tests | Runs `Parquetry.Interop.Tests`. | Linux, the only hosted runner that can run the reader containers |
| Formatting | Fails if a C# file does not follow `.editorconfig`. | Linux |
| Links in documents | Fails if a relative link in a Markdown file is broken. | Linux |

The library targets .NET 10, and an application on .NET 11 can use it. The
second job covers that case. One unit test reads the environment variable
`PARQUETRY_EXPECTED_RUNTIME_MAJOR`, which each job sets, and fails if the
tests ran on a different version of the runtime. It is skipped when the
variable is not set. The decision record is
[unit tests run on three operating systems and on the .NET 11 runtime](../adr/0040-ci-systems-and-runtimes.md).

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

The build and test commands are in `AGENTS.md`, under "Build and test
commands".
