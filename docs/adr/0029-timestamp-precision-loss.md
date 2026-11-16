# A timestamp that does not fit in microseconds raises an error unless truncation is allowed

Status: accepted
Date: 2026-11-14

## Context

.NET stores `DateTime`, `DateTimeOffset`, and `TimeSpan` in units of 100
nanoseconds, so a value has seven decimal digits of a second. The default
profile stores timestamps in microseconds, which have six, because Spark
cannot read nanosecond timestamps. A value whose seventh digit is not zero
cannot be stored exactly.

Most real values are affected. `DateTime.UtcNow` has 100-nanosecond
resolution, and so does SQL Server's `datetime2` type by default.

What other libraries do:

| Library | Result |
|---|---|
| pyarrow 26.0.1 | Raises an error when a conversion to microseconds would lose data. Setting `allow_truncated_timestamps` drops the digits without an error. Checked by running it. |
| ParquetSharp | Drops the digit without an error. Read from its source code. |
| Parquet.Net 6.0.3 | Writes timestamps as INT96, which keeps every digit. This library does not write INT96. Checked by running it. |

When pyarrow drops digits, it divides the count of time since 1970 and
discards the remainder. For a value before 1970 the count is negative, so the
value moves later. In the test, 1969-12-31 23:59:59.9999999 became
1970-01-01 00:00:00.

## Options considered

1. Drop the digit by default, with an option that raises an error.
2. Raise an error by default, with an option that drops the digit.

For the direction when the digit is dropped:

1. Always move to the earlier microsecond. The remaining digits never change.
2. Move toward 1970, as pyarrow does.

## Decision

Raise an error by default, and move toward 1970 when the digit is dropped.
Both match pyarrow.

- A `DateTime` or `DateTimeOffset` with a non-zero 100-nanosecond digit raises
  an error that names the column and the option that allows truncation.
- A writer option allows truncation. It can also be set per column. With it
  set, the digit is dropped without an error.
- When the digit is dropped, the value moves toward 1970-01-01 00:00:00 UTC. A
  value in 1970 or later moves earlier. A value before 1970 moves later.
- A `TimeSpan` stored as a count of microseconds follows the same rule. Its
  value moves toward zero.
- A column stored in nanoseconds, which the `Modern` profile allows, holds
  every .NET value exactly, so the rule does not apply to it.

## Consequences

- The library never changes a timestamp without the user having allowed it.
  This is the same rule as for decimals.
- Most users will meet this error on their first write and will set the option
  once. The error message has to make that easy by naming the option.
- The error leaves the file incomplete, and the writer aborts.
- Users who know pyarrow get the behavior they expect, and a file written with
  truncation allowed holds the same values pyarrow would have written from the
  same input.
- Moving toward 1970 has a known cost. A value before 1970 can move into the
  next second, and at a boundary into the next day or year. The change is
  always less than one microsecond. Moving to the earlier microsecond would
  avoid this, and matching pyarrow was judged to be worth more.
- The writer checks the last digit of every timestamp. The cost is one
  remainder operation per value.
