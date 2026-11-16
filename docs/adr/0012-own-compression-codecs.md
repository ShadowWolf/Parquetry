# Core implements its own Snappy and LZ4 compressors

Status: accepted
Date: 2026-11-14

## Context

Parquet pages are usually compressed. Snappy is Spark's default codec, and
Zstd is the common choice in newer systems. Neither is in the .NET base class
library for .NET 8 or .NET 10. Gzip and Brotli are. Managed libraries for
Snappy and Zstd exist, but using them makes every consumer take those
dependencies, and the library cannot control how they allocate memory.

Because the library only writes, it needs compressors and not decompressors.

## Options considered

1. Core has no third-party dependencies. Snappy and Zstd ship as separate
   packages that wrap existing libraries.
2. Core depends on existing managed Snappy and Zstd libraries.
3. Core implements the compressors itself.

For Zstd under option 3: write it before the first release, write it later, or
wrap an existing library permanently.

## Decision

Core implements its own compressors and has no third-party dependencies.

- First release: Snappy and LZ4_RAW, implemented in core. Gzip and Brotli use
  the base class library.
- The codec interface is public. A user who needs Zstd before core has it can
  plug in an existing library.
- A Zstd compressor written for this library is a later milestone.

LZ4_RAW is included for users whose readers are all recent. It produces a
compatibility message under the default profile, because Spark reads it only
from version 3.5.

## Consequences

- A Snappy or LZ4 compressor is a modest amount of code. A Zstd compressor
  with good compression ratios is much larger, which is why it comes later.
- Tests decompress the compressors' output with reference implementations,
  used as test-only dependencies, over generated inputs and inputs built to
  reach edge cases.
- Benchmarks compare throughput with the existing managed libraries, so a
  regression is visible.
- The codec interface compresses a whole page from one span into another, and
  each column gets its own compressor instance so working memory can be reused
  without locks.
- On .NET 10 the base class library has no gzip encoder that works
  on spans in one call. The Gzip codec may therefore allocate a stream per
  page. This will be measured when it is built.
- .NET 11, released on 2026-11-10, adds `GZipEncoder` and `ZstandardEncoder`,
  which compress from one span into another. The library does not rely on
  them yet. It targets .NET 10, where they do not exist, and the project owner
  chose to wait. The plan for a Zstd compressor written for this library
  stands, and the built-in encoder is to be looked at again before that work
  starts.
