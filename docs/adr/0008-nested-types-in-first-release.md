# The first release writes structs, lists, and maps at any depth

Status: accepted
Date: 2026-11-14

## Context

Parquet stores nested data by flattening it into columns. Each value carries
two small numbers, a repetition level and a definition level, which let a
reader rebuild lists, nested objects, and nulls. Producing these correctly is
the hardest part of a Parquet writer. A writer that handles only flat rows is
much simpler, but adding nesting later changes the interfaces that column
writers and generated code depend on.

## Options considered

1. Full nesting in the first release.
2. Flat rows first, with the interfaces designed to carry levels so nesting can
   be added later.
3. Flat rows plus lists of simple values.

## Decision

The first release writes simple values, nullable values, nested objects, lists,
and maps, nested to any depth.

## Consequences

- The source generator produces level values from the start.
- Lists use the standard three-level layout and maps use a repeated
  `key_value` group with a required key. These are the forms Spark and the
  other verified readers expect.
- Empty nested objects (a class with no properties that can be written to the
  file) cannot be written.
  The generator reports them as an error.
- A type that contains itself is a build error.
- Nesting is built and tested with hand-written code first. That code then
  becomes the reference for what the generator must produce.
