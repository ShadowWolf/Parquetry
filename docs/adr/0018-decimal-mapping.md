# Decimals default to precision 38 and scale 18 and are never rounded silently

Status: accepted
Date: 2026-11-14

## Context

A Parquet decimal column has a fixed precision (total digits) and scale (digits
after the decimal point). A .NET `decimal` has neither: each value carries its
own scale, and values can have up to 28 or 29 significant digits. The writer
needs a precision and scale for every decimal column before it writes the
first row.

Spark and Delta support a precision of at most 38.

## Options considered

1. A default of precision 38 and scale 18 that can be changed per writer or
   per property. A value that does not fit raises an error.
2. Require a precision and scale attribute on every decimal property.
3. The same default as option 1, but values with too many decimal places are
   rounded to fit.

## Decision

Option 1. The default is precision 38 and scale 18, which is also what Spark
uses when it infers a decimal type from a Java `BigDecimal`. It can be changed in writer options and on individual properties. A
value that cannot be stored exactly in the column's precision and scale raises
an error that names the column. The library does not round.

## Consequences

- With the default, a value with more than 20 digits before the decimal point,
  or one that needs more than 18 decimal places, raises an error. Users with
  such data set a different precision and scale.
- A column with precision 38 is stored as 16 bytes per value. Users who know
  their data fits in 18 digits can set a lower precision and get 8 bytes per
  value. A precision of 9 or less uses 4 bytes.
- Checking each value costs a little time on every write.
- An error while writing ends the write. The error is raised partway through
  a row, the writer cannot continue, and the file is aborted. Whether the
  writer should undo the partial row instead is an open question, listed in
  the [architecture overview](../architecture/README.md#open-questions).
