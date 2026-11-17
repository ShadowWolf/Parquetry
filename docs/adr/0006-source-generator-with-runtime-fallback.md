# A source generator maps objects to columns, with a runtime fallback

Status: accepted
Date: 2026-11-14

## Context

For every row, the writer has to read each property and append its value to the
right column. This code runs more often than any other, so it must not use
reflection, box values, or allocate. It also has to work under Native AOT,
where code cannot be generated at run time.

## Options considered

1. A source generator that emits the per-type code at build time, with a
   runtime fallback for types the generator did not see.
2. A source generator only. Users must declare every type in advance.
3. Runtime only: reflection and compiled expression trees, cached per type.
   This has a startup cost and does not work under Native AOT.

## Decision

Option 1. The source generator is the main path. The runtime fallback builds
the same kind of code from expression trees and is marked as unsuitable for
AOT and trimming, so the compiler warns users who call it in those builds.

## Consequences

- The generated code and the fallback call the same column buffer methods.
- The rules that assign repetition and definition levels to each column are
  written once and shared by both paths.
- Tests run every test type through both paths and require identical files.
- The generator reports unsupported shapes, such as a type that contains
  itself, as build errors.
- The column buffer types are public because generated code calls them. They
  are kept small and hidden from editor completion lists.
