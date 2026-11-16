# Target .NET 10 only

Status: accepted
Date: 2026-11-16

This record replaces [Target .NET 8 and .NET 10](0002-target-frameworks.md).

## Context

The earlier record chose `net8.0` and `net10.0`. It was written on 2026-11-14
without noticing two things that had happened four days before:

- .NET 8 reached the end of Microsoft's support on 2026-11-10.
- .NET 11 was released on 2026-11-10. It is a standard-term release. .NET 10
  is the current long-term support release. Microsoft's release data gives
  both the same end of support, 2028-11-14.

No library code exists yet, so changing the targets costs nothing.

## Options considered

1. `net10.0` only.
2. `net10.0` and `net11.0`.
3. Keep `net8.0` and `net10.0`.

## Decision

Option 1. The library targets `net10.0`.

Option 2 would matter only for the encoders that .NET 11 adds, which are not
used yet, and it would double what has to be built and tested. Option 3 keeps
a runtime that no longer receives fixes.

## Consequences

- An application on .NET 11 or later can use the library, because a `net10.0`
  library runs on later versions.
- Applications still on .NET 8 cannot use it. They are on a runtime that no
  longer receives fixes.
- There is one target to build and test, which shortens every test run.
  Whether the tests also run on the .NET 11 runtime is settled when continuous
  integration is set up.
- The library cannot call APIs that exist only in .NET 11. The ones that
  matter here are the Zstandard and Gzip encoders. A separate record says
  they are not used yet:
  [the encoders built into .NET 11](0034-dotnet-built-in-encoders.md).
- A `net11.0` target can be added later without breaking anyone.
- The source generator project still targets `netstandard2.0`, because the C#
  compiler requires that of generators.
- The points in the earlier record that do not concern .NET 8 still hold:
  .NET Framework is not supported, and the main code path must work under
  Native AOT and trimming.
