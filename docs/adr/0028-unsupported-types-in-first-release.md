# char, Int128, UInt128, and BigInteger are not supported in the first release

Status: accepted
Date: 2026-11-14

## Context

Four .NET simple types have no clear Parquet form:

| .NET type | Why there is no clear form |
|---|---|
| `char` | One UTF-16 code unit. It could be text or a number. A `char` can also be half of a two-unit character, which is not valid text on its own. |
| `Int128`, `UInt128` | Parquet's widest integer is 64 bits. A decimal with 38 digits is the widest number Spark reads, and these types hold up to 39 digits. |
| `BigInteger` | It has no size limit, and every Parquet number type does. |

These types are rare in data that is written to Parquet. Parquet.Net 6.0.3
fails on `char`, `Int128`, and `BigInteger`, which was checked by running it.
ParquetSharp does not support them, according to its source code.

## Options considered

1. Pick a form for each type and write it.
2. Require the user to choose a form, as for `Guid`.
3. Do not support the types. Fail the build and document the alternatives and
   what each one costs.

## Decision

Option 3. A property of one of these types fails the build. The error message
names the types the user can convert to. The
[type mapping page](../architecture/schema-and-type-mapping.md) describes each
alternative and its tradeoffs, so the user can decide which fits their data.

## Consequences

- The user converts the value to a supported type in their own code. The
  conversion and its limits are visible there.
- With the runtime fallback there is no build step, so the error is raised
  when the writer is created.
- Support can be added later without breaking existing users, because a type
  that fails the build today has no files written by this library.
- A user needs a way to keep such a property on their class without writing
  it, and may want to supply their own conversion. Neither has been designed
  yet. Both are listed as open questions in the
  [architecture overview](../architecture/README.md).
