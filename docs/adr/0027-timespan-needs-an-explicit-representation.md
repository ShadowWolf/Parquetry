# TimeSpan needs an explicit representation

Status: accepted
Date: 2026-11-14

## Context

A .NET `TimeSpan` is a length of time. It can be negative and can be longer
than a day. It is stored in units of 100 nanoseconds, called ticks.

Parquet has no type for a length of time that the verified readers accept:

- INTERVAL is not supported by Spark.
- TIME means a time of day. It cannot hold a negative value or one of 24 hours
  or more, and Spark 3.x and 4.0 cannot read it.

What other .NET libraries do:

| Library | Result |
|---|---|
| Parquet.Net 6.0.3 | TIME in milliseconds. Digits below a millisecond are dropped without an error. Checked by running it. |
| ParquetSharp | TIME in microseconds. The 100-nanosecond digit is dropped without an error. Its documentation says TIME is meant for a time of day and suggests a 64-bit integer for lengths of time. Read from its source code and documentation. |

## Options considered

1. Write TIME, as the other libraries do.
2. Pick one substitute, such as a 64-bit count of microseconds, and document
   it.
3. Require the user to choose a representation.

## Decision

Option 3. A `TimeSpan` property must have a representation chosen by the user.
Without one, the build fails with a message that lists the choices:

| Choice | What readers see |
|---|---|
| A 64-bit count of microseconds | A whole number. Matches the precision of timestamps in the same file. |
| A 64-bit count of ticks | A whole number. Keeps every `TimeSpan` value exactly. |
| Text | A value people can read. Readers must convert it to do arithmetic. |

This is the same rule that applies to `Guid`, `TimeOnly`, `Half`, and the
unsigned integers, and it works the same way: it applies under every profile,
the choice for a type the user does not own is made on the context class, and
with the runtime fallback the error is raised when the writer is created.

## Consequences

- The library does not write a length of time as a time of day, so a value of
  30 hours or of minus 5 minutes is never written into a column that cannot
  hold it.
- Users moving from Parquet.Net or ParquetSharp get a build error and must
  choose. Their existing files have TIME columns. Offering TIME as a further
  choice for that case has not been decided.
- A count of microseconds cannot hold the 100-nanosecond digit. It follows the
  rule for timestamps: a value with a non-zero digit raises an error unless
  the user allows truncation. See
  [timestamp precision loss](0029-timestamp-precision-loss.md).
- The integer choices carry no unit in the file. The column name or the user's
  documentation has to say whether the number is microseconds or ticks.
- The format of the text choice will be settled when the feature is built.
