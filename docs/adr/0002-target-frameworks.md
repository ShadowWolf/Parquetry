# Target .NET 8 and .NET 10

Status: replaced by [Target .NET 10 only](0030-target-dotnet-10.md)
Date: 2026-11-14

## Context

The library's performance depends on newer runtime features: `Span<T>`,
hardware intrinsics, static abstract interface members, and Native AOT. Some
enterprise users still run .NET Framework, which can only consume libraries
built for `netstandard2.0`.

## Options considered

1. `net8.0` and `net10.0`.
2. `net10.0` only. This gives the smallest test matrix but excludes users on
   .NET 8.
3. Add `netstandard2.0`. This reaches .NET Framework but needs polyfills,
   separate code paths, and slower fallbacks where intrinsics are missing.

## Decision

Target `net8.0` and `net10.0`.

## Consequences

- .NET Framework applications cannot use the library.
- The code can use modern runtime features without conditional compilation for
  older platforms.
- The main code path must work under Native AOT and trimming, and a test
  project checks this.
- The source generator project itself targets `netstandard2.0`, because the
  C# compiler requires that of generators. This does not affect what consumers
  need.
- .NET 8 reached the end of Microsoft's support on 2026-11-10, and .NET 11 was
  released the same day. This record was written without taking either into
  account, which is why it was replaced.
