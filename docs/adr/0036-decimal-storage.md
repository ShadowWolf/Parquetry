# Decimals are stored as fixed-length bytes in the smallest width that fits

Status: accepted
Date: 2026-11-16

## Context

Parquet allows a decimal to be stored in several ways: as INT32 for up to 9
digits, as INT64 for up to 18, or as bytes for any precision. The documents
first said the library would use INT32 and INT64 where they fit and 16 bytes
at precision 38, and gave no width for precisions in between.

pyarrow, which is this library's
[reference for what is written](0031-pyarrow-as-reference.md), does it
differently. By default it stores every decimal as fixed-length bytes, in the
smallest width that holds the precision: 1 byte for 1 or 2 digits, 4 bytes for
7 to 9, 8 bytes for 17 or 18, 13 bytes for 29 to 31, and 16 bytes for 36 to
38. It uses INT32 and INT64 only when its `store_decimal_as_integer` option is
set.

The project owner asked that a change to match pyarrow be checked against
Databricks first. What was found:

- Spark's own writer uses the same widths. Its source computes the width as
  the fewest bytes for the precision. It uses that for decimals of more than
  18 digits, and for all decimals when its older file format is selected. The
  source on the 3.3, 3.5, and 4.0 branches was read.
- Spark's reader accepts a fixed-length decimal of any width that can hold the
  declared precision. The same source was read.
- A test was run. pyarrow wrote a file with a decimal column at every
  precision from 1 to 38, holding the largest and smallest values, zero, a
  small value, and a null. Spark 3.5.7, 4.0.5, and 4.1.4 each read it with the
  vectorized reader on and off. Every column came back with the right type and
  every value was equal. The same test passed for a file written with
  `store_decimal_as_integer`. The program and its results are in
  `docs/research/spark-decimal-check`.
- Databricks runtimes 14.3 to 16.4 are built on Spark 3.5, 17.3 on Spark 4.0,
  and 18 on Spark 4.1, so the test covers the Spark versions those runtimes
  use. It does not cover Databricks itself or its Photon engine, which this
  project cannot run yet.
- A search found a Databricks knowledge base article about a "Parquet column
  cannot be converted" error on a decimal column. The article could not be
  opened on 2026-11-16, so its cause and the versions it covers are not known.

## Options considered

1. INT32 and INT64 up to 18 digits, and fixed-length bytes above.
2. Fixed-length bytes in the smallest width at every precision, as pyarrow
   does, with integer storage as an option.

## Decision

Option 2.

- A decimal column is stored as fixed-length bytes, in the smallest width that
  holds its precision. The widths are the ones pyarrow uses.
- A writer option stores decimals of 18 digits or fewer as INT32 or INT64
  instead. This is the same choice pyarrow offers.

## Consequences

- At the default precision of 38, a decimal takes 16 bytes, as before.
- A .NET `decimal` column set to precision 29 takes 13 bytes.
- For 9 digits or fewer the bytes form takes the same space or less than
  INT32. For 10 to 18 digits it takes the same space or less than INT64.
- Integer storage is usually faster to encode and to read. Users who want
  that turn on the option. Spark read both forms in the test.
- The live test against Databricks, with Photon on and off, must include
  decimal columns at several precisions before the first release. If
  Databricks fails on any width, this decision is reopened.
