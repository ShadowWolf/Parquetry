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

The author of the change chose the details below while building it. They
were not put to the project owner as separate questions.

- There are three containers. The Python container holds pyarrow, Polars,
  and DuckDB. The other two hold Spark 3.5 and the current Spark 4.x. Each
  image is built from a Dockerfile under
  `tests/Parquetry.Interop.Tests/Containers`.
- Every container runs the same small HTTP server, written with Python's
  standard library. The comment at the top of `reader_server.py` in that
  folder describes the requests and responses.
- A test sends the file's bytes in the request. No folder is shared between
  the test machine and the containers, so file permissions and the way Docker
  shares folders on each operating system do not matter.
- The response lists each column with the reader's own name for its type and
  with a name that is the same for every reader, such as `int64`. Each value
  is sent as text, because JSON numbers cannot hold every 64-bit integer, NaN,
  or negative zero.
- The response also says whether a column can hold nulls, for a reader that
  reports it. Of these readers only pyarrow does. Spark marks every column it
  reads from a file as able to hold nulls, whatever the file says.
- A reader that cannot read a file is answered with status 422 and the
  reader's message. Only an error of a type that the reader's own library
  raises counts. Any other failure is answered with status 500, and the C#
  side raises it as an error of the test setup. A test that expects a reader
  to reject a file therefore does not pass because the setup broke. One of
  the setup's own tests checks this on every run.
- The Python container also writes a small known-good file on request. The
  tests of the setup use it.
- The container files name exact versions. On 2026-11-18 they were pyarrow
  26.0.1, Polars 2.1.0, DuckDB 2.0.0, Python 3.14.10, Spark 3.5.9, and Spark
  4.3.0. Dependabot proposes newer ones, as the decision on
  [formatting, links, and dependency updates](0042-formatting-links-and-dependency-updates.md)
  describes, so the container files are the place to look for the versions
  in use.
- The list of defaults given to the project owner on 2026-11-17 named Spark
  3.5.7 and 4.1.4, the versions the earlier checks in
  `docs/research/spark-decimal-check` used. The decision on which readers
  verify the output says Spark 3.5 and the current 4.x release. On 2026-11-18
  the newest releases were 3.5.9 and 4.3.0, so those were used.
- Spark runs with one worker thread. With one thread it reads a test file in
  a single task and returns the rows in file order, which the comparison
  relies on.
- A container's port is published only on the loopback address of the test
  machine, so other machines cannot send files to a reader.
- A container that does not answer its health check within three minutes
  fails the test run with the container's output in the message.

## Consequences

- A reader test is an ordinary xUnit test that runs once for each reader. On
  an Arm64 Mac with the images already built, the eleven tests of the setup
  take about 10 seconds.
- Reader tests need Docker. A contributor without it can still build
  everything and run the unit tests.
- The first run downloads the base images and builds the three reader
  images. The images are kept afterwards so that the next run is fast. They
  take about 3 GB of disk space. An image's tag is a hash of the container
  files, so a change to those files leaves the older images behind until
  someone removes them with `docker rmi`.
- Testcontainers starts one small container of its own. It removes the reader
  containers if the test run is killed before it can stop them.
- A whole file travels in one request. That suits test files of a few
  megabytes. A test with a very large file needs another way to hand it over.
- A type the tests have not used yet has no common name. Its column comes
  back marked as unknown, and a test that expects a known type fails on that.
  "Adding a type" on the [Testing](../architecture/testing.md) page lists
  what to change.
- Rows are compared in order. Spark keeps file order for a file it reads in
  one task. In the measurement in `docs/research/spark-row-order`, Spark with
  one thread read an 88 MB file in one task. A test with a larger file, or
  one that changes how Spark is started, cannot assume the order.
- pyarrow, Polars, and DuckDB share one process. If one of them crashes in
  native code, the server stops, and the later tests for all three fail with
  an error that says the container did not answer.
- The server reads a whole file. The tests that run filtered queries, which
  the Testing page describes for statistics, the page index, and bloom
  filters, need a request for queries. It is added with the first of those
  features.
- Spark reads with its default settings. The two settings on its command
  line turn off its web interface and set the one worker thread, and neither
  changes how a file is read. This matches the goal that files are readable
  without reader settings.
- The Testcontainers package is a dependency of the test project only. The
  core package still has none.
