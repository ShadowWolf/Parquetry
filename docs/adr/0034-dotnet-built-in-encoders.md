# The Zstandard and Gzip encoders built into .NET 11 are not used yet

Status: accepted
Date: 2026-11-16

## Context

.NET 11, released on 2026-11-10, adds `ZstandardEncoder` and `GZipEncoder` to
the base class library. Both compress from one span into another, which is
what a Parquet page needs. Neither exists in .NET 10.

The library has no third-party dependencies and planned to write its own Zstd
compressor after the first release. The built-in Zstandard encoder could
replace that work. Using it would mean adding a `net11.0` target, since the
library targets `net10.0`.

## Options considered

1. Add a `net11.0` target now and use the built-in encoders there.
2. Do not rely on them yet, and look at them again later.

## Decision

Option 2. The project owner does not want to rely on the new Zstandard
library yet. It was released six days before this decision.

## Consequences

- The plan in the earlier record on
  [compression codecs](0012-own-compression-codecs.md) is unchanged: Snappy
  and LZ4_RAW are written for this library, Gzip and Brotli use the streams in
  the base class library, and a Zstd compressor written for this library comes
  after the first release.
- Until then, a user who needs Zstd supplies a codec through the codec
  interface. On .NET 11 that codec can be a thin wrapper over the built-in
  encoder.
- The roadmap carries an item to look at the built-in encoders again before
  work on a Zstd compressor starts. If they have proved reliable by then, a
  `net11.0` target that uses them is the cheaper path.
