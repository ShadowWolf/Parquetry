# The default profile is the one all verified readers accept

Status: accepted
Date: 2026-11-14

## Context

A user who sets no options should get a file that works wherever they send it.
The readers the project verifies against are Apache Spark (including
Databricks), Arrow-based tools, and cloud warehouses. Spark is the strictest of
these, and Databricks adds limits of its own through Delta Lake.

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
- Statistics in the current `min_value` and `max_value` fields.

It does not write INT96 timestamps, nanosecond timestamps, TIME, UUID,
half-precision floats, unsigned integer annotations, or fixed-length byte
columns without a type annotation. Spark fails on each of these in at least one
supported version.

If testing shows that Databricks differs from open-source Spark, a `Databricks`
profile will be added.

## Consequences

- The research found nothing in Databricks that breaks these defaults. It
  could not find documentation on which encodings and codecs the Photon engine
  reads. A live test against Databricks, with Photon on and off, is needed to
  confirm this.
- Files are larger and slower to read than they would be with newer encodings.
  Users who control their readers can choose `Modern`.
- LZ4_RAW and Brotli are available but produce a validation message under this
  profile. Spark reads LZ4_RAW only from version 3.5 and does not include a
  Brotli codec.
- Column names containing a space or any of `,;{}()=`, a tab, or a newline
  are reported by validation, because Delta tables reject them unless column
  mapping is enabled. Names that differ only by letter case are also reported.
