# The default profile is the one all verified readers accept

Status: accepted
Date: 2026-11-14

## Context

A user who sets no options should get a file that works wherever they send it.
The readers the project verifies against are Apache Spark (including
Databricks), pyarrow, Polars, DuckDB, and cloud warehouses. Spark is the
strictest of these, and Databricks adds limits of its own through Delta Lake.

Research on 2026-11-14 checked Spark's source code for versions 3.3 through
4.x, the Delta protocol, and Databricks documentation. The findings are in
[Spark and Databricks compatibility](../architecture/spark-and-databricks-compatibility.md).

## Options considered

1. Default to settings every verified reader accepts. Newer features are
   chosen through the `Modern` profile.
2. Default to newer format features, with a Spark profile for those who need
   it.
3. No default. The user must pick a profile.

## Decision

Option 1. The default profile, `Compatible`, writes:

- Data page version 1.
- PLAIN and dictionary encodings.
- Snappy compression.
- Timestamps as 64-bit microseconds, adjusted to UTC.
- Lists in the standard three-level layout.
- Statistics in the current `min_value` and `max_value` fields, and also in
  the older `min` and `max` fields for the column types where pyarrow writes
  both.

Data page version 1 with PLAIN and dictionary encodings is what Spark and
pyarrow write by default, so it is the combination every reader has been used
with most.

Where the format has both a current logical type and an older converted type
for a column, the profile writes both, as the format requires.

It does not write the following:

| Not written | Reason |
|---|---|
| Nanosecond timestamps, TIME, UUID, half-precision floats | Spark fails to read each of these in at least one version in scope. |
| Fixed-length byte columns without a type annotation | Spark 3.3 fails to read them. |
| Unsigned integer annotations, except on `byte` columns | Spark reads them as a wider signed type, and Delta tables have no unsigned types. `byte` is the exception because it has a default form and that form follows pyarrow, under the record on [the byte annotation](0035-byte-annotation.md). |
| INT96 timestamps | Spark reads them, but the format has deprecated them. |

If testing shows that Databricks differs from open-source Spark, a `Databricks`
profile will be added.

## Consequences

- The research found nothing in Databricks that breaks these defaults. It
  could not find documentation on which encodings and codecs the Photon engine
  reads. A live test against Databricks, with Photon on and off, is needed to
  confirm this.
- The research covers Spark and Databricks. That pyarrow, Polars, DuckDB, and
  the cloud warehouses read these defaults is expected, and is confirmed only
  when the reader tests run.
- Spark's source shows it can read data page version 2 and two of the delta
  encodings from version 3.3. They stay out of this profile until Photon and
  the warehouses have been tested with them.
- Files are larger and slower to read than they would be with newer encodings.
  Users who control their readers can choose `Modern`.
- LZ4_RAW and Brotli are available but produce a compatibility message under
  this profile. Spark reads LZ4_RAW only from version 3.5 and does not include
  a Brotli codec.
- Column names containing a space or any of `,;{}()=`, a tab, or a newline
  are reported by validation, because Delta tables reject them unless column
  mapping is enabled. Names that differ only by letter case are also reported.
