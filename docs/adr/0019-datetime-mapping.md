# A DateTime of unspecified kind raises an error unless a policy is set

Status: accepted
Date: 2026-11-14

## Context

The default profile stores timestamps as points in time in UTC. A .NET
`DateTime` has a `Kind` that is `Utc`, `Local`, or `Unspecified`. An
unspecified value does not say which time zone it is in, so the writer cannot
know which point in time it means. Many database drivers return unspecified
values.

.NET stores time in units of 100 nanoseconds. The default profile stores
microseconds, because Spark cannot read nanosecond timestamps.

## Options considered

1. Treat unspecified values as UTC by default, with an option to change that.
2. Raise an error for unspecified values unless the user sets a policy.
3. Write `DateTime` as a timestamp without a time zone, and only
   `DateTimeOffset` as a point in time. Spark 3.3 reads timestamps without a
   time zone incorrectly, and Delta tables need a table feature enabled to
   hold them.

## Decision

Option 2.

- `DateTime` with `Kind` of `Utc` is written as is.
- `DateTime` with `Kind` of `Local` is converted to UTC.
- `DateTime` with `Kind` of `Unspecified` raises an error that names the
  column. A writer option changes this to "treat as UTC" or "treat as local".
- `DateTimeOffset` is converted to UTC. The original offset is not stored.
- Values are stored in microseconds. A value that does not fit in microseconds
  raises an error unless the user allows truncation. That rule has its own
  record:
  [timestamp precision loss](0029-timestamp-precision-loss.md).

## Consequences

- The library does not guess a time zone. A user whose data comes from a
  database will usually have to set the policy once.
- Writing a timestamp without a time zone is possible as an explicit column
  setting, with a compatibility message under the default profile.
- With truncation allowed, a value read back may differ from the original by
  less than a microsecond.
