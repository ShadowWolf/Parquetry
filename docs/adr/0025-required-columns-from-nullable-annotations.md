# A non-nullable reference type becomes a required column

Status: accepted
Date: 2026-11-14

## Context

A Parquet column is either required or optional. An optional column stores a
definition level for every value so that nulls can be recorded. A required
column does not, which makes it smaller and faster to write, and it tells
readers that the column never holds null.

For value types the choice is clear: `int` is required and `int?` is optional.
For reference types, C# has nullable annotations: `string` means "not null" and
`string?` means "may be null". The compiler warns about violations, but nothing
enforces them at run time. A property declared as `string` can hold null.

Parquet.Net 6.0.3 writes a non-nullable `string` property as an optional
column. This was checked by running it.

## Options considered

1. Follow the annotation. A non-nullable reference type is a required column.
2. Treat every reference type as optional, whatever its annotation.

## Decision

Option 1.

- In code with nullable annotations enabled, a reference type declared
  non-nullable is a required column, and one declared nullable is optional.
- In code without nullable annotations, reference types are optional.
- The same rule applies to list elements and map values.
- If the writer finds a null in a required column, it raises an error that
  names the column.

## Consequences

- The file's schema matches what the C# type says.
- Data that breaks its own annotations fails the write. The error leaves the
  file incomplete, and the writer aborts. A user who cannot fix the data
  declares the property nullable.
- The writer checks for null on every required reference value. The cost is
  one comparison.
- The source generator reads the annotations at build time. The runtime
  fallback reads them through reflection and must reach the same result. The
  same-output tests cover this.
- Changing a property from `string` to `string?` changes the file schema from
  required to optional. Readers that enforce a fixed schema, such as an
  existing Delta table, may reject the change.
