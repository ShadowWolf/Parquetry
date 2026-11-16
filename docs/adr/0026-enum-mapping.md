# An enum is written as its number by default

Status: accepted
Date: 2026-11-14

## Context

Parquet has an ENUM annotation for text columns, but it only marks a text
value as coming from a fixed set. There is no Parquet type that stores both a
number and its name. A .NET `enum` therefore has to be written either as its
number or as the name of the value.

What other .NET libraries do:

| Library | Result |
|---|---|
| Parquet.Net 6.0.3 | A 32-bit integer holding the number. Checked by running it. |
| ParquetSharp | Enums are not supported. Read from its source code. |
| `System.Text.Json` | The number by default. A converter writes the name. |

## Options considered

1. Write the number by default, with an option to write the name as text.
2. Write the name as text by default, with an option to write the number.
3. Require the user to choose, as for `Guid`.

## Decision

Option 1.

- An enum is written as its number. The column is stored the way the enum's
  underlying type is stored. Most enums use `int`, which becomes INT32 with no
  annotation.
- An option, per property or per enum type, writes the name as text instead.

## Consequences

- The default matches Parquet.Net and `System.Text.Json`, so users moving from
  either get what they expect.
- A reader sees a number with no record of what it means. Renumbering the
  enum's members later changes the meaning of files already written. Users who
  need files that explain themselves choose text.
- Text takes more space per value before encoding. Dictionary encoding removes
  most of that cost, because an enum has few distinct values.
- An enum whose underlying type is `ushort`, `uint`, or `ulong` follows the
  rule for those types: the user must choose how the number is stored, or
  choose text.
- An enum whose underlying type is `byte` is stored as a `byte` is, with an
  unsigned 8-bit annotation.
- The source generator writes the name lookup at build time, so writing names
  does not need reflection and works under Native AOT.
- How a combination of `[Flags]` values is written as text, what is written
  for a number that has no name, and whether the text column carries the
  STRING or the ENUM annotation will be settled when the feature is built.
