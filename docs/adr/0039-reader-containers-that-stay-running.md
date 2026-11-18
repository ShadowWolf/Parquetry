# Reader tests send files to reader containers that stay running

Status: accepted
Date: 2026-11-18

## Context

The library does not read Parquet, so its reader tests give each file to
pyarrow, Polars, DuckDB, and Spark and compare what they return with what was
written. The decision on
[which readers verify the output](0011-verified-readers-and-test-tiers.md)
says these readers run in containers on every pull request. It does not say
how a test, which is C# code run by xUnit, gets a file to a reader and gets
the result back.

Two things shape the answer. The readers are Python libraries and Spark, so
they cannot be called from the test process. Spark also takes several seconds
to start, which is too slow to repeat for every test.

## Options considered

1. Each reader container starts once per test run and stays running. Tests
   send it requests over HTTP. The comparison is done in C#.
2. Each test starts a container for each reader with `docker run`. This needs
   no extra package, but Spark starts again for every test.
3. A script outside the tests writes every file, runs each reader once over
   the folder, and compares the values in Python. The expected values then
   live in Python, and a failure is not reported as a failed xUnit test.

## Decision

Option 1. The project owner chose it on 2026-11-17, with the test project
taking the Testcontainers package to start and stop the containers.

The details below were settled while building it:

- There are three containers: one for pyarrow, Polars, and DuckDB, one for
  Spark 3.5, and one for the current Spark 4.x. Each image is built from a
  Dockerfile in `tests/Parquetry.Interop.Tests/Containers`.
- Every container runs the same small HTTP server, written with Python's
  standard library. `reader_server.py` in that folder describes the requests
  and responses.
- A test sends the file's bytes in the request. No folder is shared between
  the test machine and the containers, so file permissions and the way Docker
  shares folders on each operating system do not matter.
- The response lists each column with the reader's own name for its type and
  with a name that is the same for every reader, such as `int64`. Each value
  is sent as text, because JSON numbers cannot hold every 64-bit integer, NaN,
  or negative zero.
- A reader that cannot read a file is answered with status 422 and the
  reader's message. A failure in the server itself is answered with status
  500, and the test setup raises it as an error. A test that expects a reader
  to reject a file therefore cannot pass because the setup broke.
- The pyarrow container also writes a small known-good file on request. The
  tests of the setup use it, because the library writes no files yet.
- The versions are fixed: pyarrow 26.0.1, Polars 2.1.0, DuckDB 2.0.0, Spark
  3.5.9, and Spark 4.3.0. Spark 4.3.0 was the newest 4.x release on
  2026-11-18. The earlier checks of Spark, in
  `docs/research/spark-decimal-check`, went up to 4.1.4.

## Consequences

- A reader test is an ordinary xUnit test that runs once for each reader. On
  the machine it was built on, the ten tests of the setup take about 11
  seconds once the images exist.
- Reader tests need Docker. A contributor without it can still build
  everything and run the unit tests.
- The first run downloads the base images and builds the three reader
  images. The images are kept afterwards so that the next run is fast. They
  take about 3 GB of disk space.
- Testcontainers starts one small container of its own. It removes the reader
  containers if the test run is killed before it can stop them.
- A whole file travels in one request. That suits test files of a few
  megabytes. A test with a very large file needs another way to hand it over.
- A type the tests have not used yet has no common name. Adding one means
  adding it to the list in `reader_server.py`, to the table of each reader,
  and to the `ColumnKind` type in the test project.
- The server reads a whole file. The tests that run filtered queries, which
  the [Testing](../architecture/testing.md) page describes for statistics,
  the page index, and bloom filters, need a request for queries. It is added
  with the first of those features.
- Spark reads with its default settings, apart from turning off its web
  interface. This matches the goal that files are readable without reader
  settings.
- The Testcontainers package is a dependency of the test project only. The
  core package still has none.
