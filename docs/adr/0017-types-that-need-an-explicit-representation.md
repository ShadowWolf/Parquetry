# Guid, TimeOnly, Half, and unsigned integers need an explicit representation

Status: accepted
Date: 2026-11-14

## Context

Some .NET types map naturally to a Parquet type that Spark cannot read, or
reads as a different type:

| .NET type | Natural Parquet type | Problem |
|---|---|---|
| `Guid` | UUID | Fails in every Spark version checked. |
| `TimeOnly` | TIME | Fails in Spark 3.x and 4.0. |
| `Half` | FLOAT16 | Fails in every Spark version checked. |
| `ushort`, `uint`, `ulong` | Unsigned integer annotations | Spark 3.2 and later reads them as wider signed types. Delta has no unsigned types. |

Each has an alternative form, such as writing a `Guid` as text, but the
alternative changes what readers see.

## Options considered

1. Use a lossless substitute where one exists and document it. Require a choice
   only where none exists.
2. Always require the user to choose a representation.
3. Write the natural Parquet type and warn that Spark cannot read it.

## Decision

Option 2. A property of one of these types must have an explicit
representation chosen by the user. Without one, the build fails with a message
that lists the choices.

## Consequences

- The library never changes how one of these types is stored without the user
  having asked for it.
- The source generator runs at build time and cannot know which profile will
  be used at run time. The rule therefore applies under every profile,
  including `Modern`.
- The chosen representation is checked against the profile when the writer is
  created. Choosing UUID under the default profile produces a validation
  message saying that Spark cannot read the column.
- For a type the user does not own, the choice is made per .NET type on the
  context class, since attributes cannot be added to its properties.
- With the runtime fallback there is no build step, so the same error is
  raised when the writer is created.
- `byte` is unsigned in .NET but is exempt from this rule, because it is common
  and requiring a choice for it would be a burden. It is written as a 32-bit
  integer in every profile. Under the default profile the column is annotated
  as a 16-bit signed integer, which holds every `byte` value and which Spark
  reads as a short. pyarrow writes an unsigned 8-bit annotation for the same
  values. Whether to switch to that is an open question, described on the
  [pyarrow parity](../architecture/pyarrow-parity.md) page.
