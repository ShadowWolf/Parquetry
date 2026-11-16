# Decimals are stored as fixed-length bytes in the smallest width that fits

Status: accepted
Date: 2026-11-16

## Context

Parquet allows a decimal to be stored in several ways: as INT32 for up to 9
digits, as INT64 for up to 18, or as bytes for any precision. The decision on
[decimal mapping](0018-decimal-mapping.md) set the default precision and scale
but not the storage. The type mapping page said the library would use INT32
and INT64 where they fit and 16 bytes at precision 38, and gave no width for
the precisions in between.

pyarrow, which is this library's
[reference for what is written](0031-pyarrow-as-reference.md), stores every
decimal as fixed-length bytes by default. The width is the fewest bytes whose
signed range holds every number of that precision: 1 byte for 1 or 2 digits,
4 bytes for 7 to 9, 8 bytes for 17 or 18, 13 bytes for 29 to 31, and 16 bytes
for 36 to 38. The full table is in
[Schema and type mapping](../architecture/schema-and-type-mapping.md). pyarrow
uses INT32 and INT64 only when its `store_decimal_as_integer` option is set.

The project owner asked that a change to match pyarrow be checked against
Databricks first.

### What Spark's source says

The source was read on the branches for versions 3.3, 3.4, 3.5, 4.0, and 4.1.

- Spark's reader accepts a fixed-length decimal of any width that can hold the
  declared precision.
- Spark's writer uses the same widths as pyarrow for decimals of more than 18
  digits. For 18 digits or fewer, which is the range this decision changes,
  its default is INT32 and INT64. It writes fixed-length bytes for those only
  when the setting `spark.sql.parquet.writeLegacyFormat` is on. So the files
  that Spark and Databricks produce themselves hold small decimals as
  integers.

### What was tested

pyarrow 26.0.1 wrote the test files, and Spark 3.3.3, 3.4.4, 3.5.7, 4.0.5, and
4.1.4 read them in containers. Spark has two Parquet readers, a faster
"vectorized" one that is on by default and an older one, and every case was
run with each. Every file was written twice, once as fixed-length bytes and
once as integers.

| Case | Result on all five versions |
|---|---|
| A decimal column at every precision from 1 to 38, 6,000 rows in 4 row groups, with nulls, negative values, and values at the edge of each byte width. Written with dictionary pages, with plain pages, and with pyarrow's limit on the size of a dictionary page set to 1 KB. | Every value equal, in both storage forms. |
| Eight decimal columns that do not allow nulls. | Every value equal. |
| Decimals inside lists, structs, and maps. | Every value equal. |
| Filters on sorted decimal columns across 12 row groups. | Every count right. Spark skipped row groups in both storage forms. |
| A read that asks for a decimal type different from the file's. | The fixed-length form never did worse than the integer form. Details are on the [compatibility page](../architecture/spark-and-databricks-compatibility.md). |

The programs and results are in `docs/research/spark-decimal-check`. No
Parquetry file exists yet, so this shows that Spark reads the form, not that
it reads this library's output.

### What is not known

- Databricks runtimes 14.3 to 18 are built on the 3.5, 4.0, and 4.1 release
  lines of Spark, so the test covers those lines. It does not cover Databricks
  itself or its own query engine, Photon, which this project cannot run yet.
- A Databricks knowledge base article titled "Apache Spark job fails with
  Parquet column cannot be converted error" could not be opened on
  2026-11-16. A second-hand summary says it describes a column expected as a
  decimal and found as fixed-length bytes, and advises turning the vectorized
  reader off. That could not be confirmed. Open-source Spark raises this
  error when the decimal type a query asks for differs from the file's, and
  it does so for the integer form as well.

## Options considered

1. INT32 and INT64 up to 18 digits, and fixed-length bytes above. This is what
   Spark writes by default.
2. Fixed-length bytes in the smallest width at every precision, as pyarrow
   does, with integer storage as an option.

## Decision

Option 2, under the default profile.

- A decimal column is stored as fixed-length bytes, in the smallest width that
  holds its precision. The widths are the ones pyarrow uses.
- An option, for the writer or for one column, stores decimals of 9 digits or
  fewer as INT32 and of 10 to 18 digits as INT64. This is the same choice
  pyarrow offers. It produces no compatibility message, because Spark read
  both forms in the test.
- What the `Modern` profile does is left open. Its delta encoding applies to
  integers and not to fixed-length bytes.

## Consequences

- At the default precision of 38, a decimal takes 16 bytes.
- A .NET `decimal` holds at most 29 digits. A column set to precision 29 takes
  13 bytes.
- Before encoding and compression, the bytes form takes the same space as the
  integer form or less. After them it can be larger. With pyarrow's default
  settings and 1,000,000 values, the two forms were within 4% of each other
  in six of seven cases measured. In the seventh, a column of increasing
  18-digit numbers, the bytes form was 5.2 MB and the integer form 4.3 MB.
  The measurements are in
  `docs/research/pyarrow-parity/decimal_size_output.txt`.
- Minimum and maximum statistics for a fixed-length decimal are compared as
  signed numbers, not as unsigned bytes. With unsigned comparison a negative
  value would sort above a positive one, and readers would skip rows they
  should return. pyarrow writes both the older and the newer statistics
  fields for these columns, and the library does the same.
- Which form is faster to write and read has not been measured. The
  benchmarks will compare them.
- The tests against a live Databricks workspace, with Photon on and off, must
  cover the following before the first release: decimal columns at several
  precisions, a table whose decimal type differs from the file's, and a write
  of the result to a Delta table. If Databricks fails on any of them, this
  decision is reopened.
