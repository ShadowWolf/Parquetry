# Spark and Databricks compatibility

This page records research done on 2026-11-14 into what Apache Spark and
Databricks can read from a Parquet file. The default profile is built on it.

The sources were Spark's source code on each release branch, Spark's issue
tracker, the Delta Lake protocol, the Java Parquet library's source, and
Databricks documentation. "Confirmed" below means the behavior was read in one
of those sources. It does not mean it was tested. Nothing on this page has been
tested by this project yet. The reader tests described in
[Testing](testing.md) will do that, and this page should be corrected when they
disagree with it.

The Spark versions read were 3.3, 3.4, 3.5, 4.0, and 4.1. "Every version
checked" on this page means those. A few rows were also checked against 4.2
and 4.3, and those rows say so. For every other row, 4.2 and 4.3 have not
been checked. Where a table says a feature is
readable from 3.3, that is the oldest version checked, and the feature may be
older.

## Terms used on this page

| Term | Meaning |
|---|---|
| Delta Lake, Delta table | The table format Databricks uses. A Delta table is a set of Parquet files plus a log, and it has rules of its own about types and column names. |
| Photon | Databricks' own query engine, which replaces parts of Spark on clusters where it is enabled. |
| Vectorized reader | Spark's faster Parquet reader, which is on by default. Spark falls back to a slower reader for what it does not handle. |
| Column mapping | A Delta table feature that lets column names contain characters Delta otherwise rejects. |
| Auto Loader | A Databricks feature that loads new files as they arrive. It puts data that does not fit the table's schema into a "rescued data" column. |
| `COPY INTO`, `read_files` | Databricks SQL commands that load files into a table or query them directly. |
| Variant | A Databricks type for semi-structured data. |

## Summary

The default profile's settings are readable by Spark 3.3 through 4.x according
to Spark's source. No Databricks behavior was found that breaks them. Some
things about Databricks could not be confirmed from documentation and need a
live test. The main ones are these, and the full list is at the end of the
page:

- Which encodings and codecs the Photon engine reads.
- Whether Databricks handles old dates the same way as open-source Spark.
- How Databricks treats unsigned integers, UUID, and fixed-length byte columns
  without an annotation.

## Databricks runtime versions

From Databricks release notes:

| Databricks Runtime | Spark version |
|---|---|
| 14.3 LTS | 3.5.0 |
| 15.4 LTS | 3.5.0 |
| 16.4 LTS | 3.5.2 |
| 17.3 LTS | 4.0.0 |
| 18 LTS | 4.1.0 |

The release notes also list runtime 19, on Spark 4.3.0.

Photon passes anything it does not support to Spark. Its documentation lists
supported data types but says nothing about Parquet encodings or codecs.

## Types

| Parquet type | Spark | Databricks | Status |
|---|---|---|---|
| Signed integers (8, 16, 32, 64 bit) | Read in all versions. | Same. These are Delta's own types. | Confirmed |
| Unsigned integers | Read since 3.2 as the next wider signed type. 64-bit unsigned becomes a 20-digit decimal. | Delta has no unsigned types. Databricks behavior not documented. | Spark confirmed. Databricks not confirmed. |
| DECIMAL up to precision 38, stored as INT32, INT64, fixed-length bytes, or bytes | Read. | Delta's maximum precision is 38. | Confirmed |
| DECIMAL above precision 38 | Error. | Not supported. | Confirmed |
| Text (bytes with the STRING annotation) | Read as text. | Same. | Confirmed |
| Bytes with no annotation | Read as binary. | Not documented. | Spark confirmed |
| DATE | Read. | Read. | Confirmed |
| Timestamp, milliseconds or microseconds, adjusted to UTC | Read in all versions. | Same. | Confirmed |
| Timestamp, not adjusted to UTC | 3.3 reads it as a point in time, which is wrong. 3.4 and later read it as a timestamp without time zone. | Supported from runtime 13.3. A Delta table needs the `timestampNtz` feature enabled. | Confirmed |
| Timestamp, nanoseconds | Error in every version checked, unless the setting `spark.sql.legacy.parquet.nanosAsLong` is enabled. | A Databricks knowledge base article reports the same failure. | Confirmed |
| INT96 timestamp | Read. An older form that new writers should not produce. | Not documented. | Spark confirmed |
| TIME | Error in 3.x and 4.0. In 4.1, one form is read, and only when a setting that is off by default is enabled. | A TIME type exists in beta from runtime 18. Reading it from Parquet is not documented. | Spark confirmed. Databricks not confirmed. |
| UUID | Error in every version checked. | Not documented. | Spark confirmed |
| FLOAT16 | Error in every version checked. | Not documented. | Spark confirmed |
| INTERVAL | Error. | Not documented. | Spark confirmed |
| Fixed-length bytes with no annotation | Error in 3.3. Read as binary from 3.4. | Not documented. | Spark confirmed |

## Dates before 1582 and timestamps before 1900

Spark 3.x fails to read these from a file whose writer it does not recognize.
It recognizes a writer by the key `org.apache.spark.version` in the file's
metadata. With that key set to 3.0.0 or later, and without the keys Spark adds
to mark a file written with the old calendar, Spark reads the values as
written. Spark 4.0 reads them as written in
either case. Confirmed in `DataSourceUtils.scala`. The Databricks default is
not documented.

## Nested data

| Structure | Spark | Status |
|---|---|---|
| List in the standard three-level layout | Read. | Confirmed |
| Map as a repeated group of key and value with a required key | Read. | Confirmed |
| Empty group | The Java Parquet library rejects it. Databricks documentation states that Parquet forbids empty structs. | Confirmed |
| Vectorized reader for nested columns | Off by default in 3.3, where a slower reader is used. On by default from 3.4. | Confirmed |

No limit on nesting depth was found.

## Encodings and page versions

These apply to Spark's vectorized reader.

| Feature | Readable from Spark | Status |
|---|---|---|
| PLAIN, dictionary | All versions | Confirmed |
| Data page version 2 | 3.3 | Confirmed |
| DELTA_BINARY_PACKED, DELTA_BYTE_ARRAY | 3.3 | Confirmed |
| DELTA_LENGTH_BYTE_ARRAY | 3.4 | Confirmed |
| BYTE_STREAM_SPLIT | 4.3. Checked as absent in 4.2 and present in 4.3. | Confirmed |

Photon's support for each of these is not documented.

## Compression

| Codec | Spark | Status |
|---|---|---|
| Snappy, Gzip, Zstd | All versions | Confirmed |
| LZ4_RAW | From 3.5. Earlier versions ship a Java Parquet library that lacks it. | Confirmed |
| Brotli | Needs a codec class that Spark does not include. | Confirmed |
| LZO | Needs a library that Spark does not include. | Not confirmed |

Databricks and Photon codec support is not documented.

## Statistics and indexes

| Feature | Behavior | Status |
|---|---|---|
| Page index | Used by Spark's reader since 3.2. | Confirmed |
| `min_value` and `max_value` statistics | Preferred over the older fields, and trusted regardless of which library wrote the file. | Confirmed |
| Older `min` and `max` fields | Ignored for text and byte columns when `created_by` is empty or cannot be parsed. | Confirmed |
| `created_by` | Parsed by the Java Parquet library. The form `<Name> version <x.y.z> (build <hash>)` parses cleanly. | Confirmed |
| Bloom filters | The Java Parquet library can read them. Whether Spark uses them by default was not checked. | Partly confirmed |

## Column names

Spark 3.3 and later read column names containing a space or any of
`,;{}()=`, a tab, or a newline. Delta tables reject such names unless column
mapping is enabled. Spark fails when a query asks for a field and two columns
match it without regard to letter case. Databricks Auto Loader treats such
columns as one and moves the mismatch to its rescued data column. Confirmed.

## What Databricks has that open-source Spark lacks

These do not affect the default profile. They could go into a `Databricks`
profile later.

- Timestamp without time zone, which needs a Delta table feature.
- A TIME type, in beta from runtime 18, which needs a Delta table feature.
- Variant and geospatial types.

## Still to confirm by testing

- Photon's handling of each encoding and codec.
- Databricks' behavior with old dates, with and without the Spark version key.
- Databricks' handling of unsigned integers, UUID, FLOAT16, and unannotated
  fixed-length bytes.
- Whether there is a practical limit on page size or column chunk size near
  2 GB.
- The behavior of `COPY INTO`, `read_files`, and conversion to Delta with
  files from the default profile.
