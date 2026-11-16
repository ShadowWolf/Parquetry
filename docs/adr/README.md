# Decision records

Each file in this folder records one architectural decision: the situation,
the options that were considered, what was chosen, and what follows from it.
Records are numbered in the order they were written. A record is not edited
after it is accepted, apart from corrections. A later decision that changes an
earlier one gets its own record, and the earlier record is marked as replaced
with a link.

## Format

```
# Title

Status: accepted | replaced by <title and link>
Date: YYYY-MM-DD

## Context
## Options considered
## Decision
## Consequences
```

When another document refers to a decision, it says what the decision is. The
title or a link may follow. A bare number is not enough.

## Index

| File | Decision |
|---|---|
| [0001](0001-name-and-license.md) | The library is named Parquetry and licensed under MIT. |
| [0002](0002-target-frameworks.md) | Target .NET 8 and .NET 10. Replaced: the library now targets .NET 10 only. |
| [0003](0003-write-only-scope.md) | The library writes Parquet and does not read it. |
| [0004](0004-row-group-layout-strategies.md) | Core chooses one of several strategies for laying out a row group, with in-memory buffering as the default. |
| [0005](0005-destination-shapes.md) | Core defines two kinds of destination: sequential and staged. |
| [0006](0006-source-generator-with-runtime-fallback.md) | A source generator maps objects to columns. A runtime fallback covers types unknown at build time. |
| [0007](0007-type-registration.md) | Types are registered by an attribute on the type or by a context class. |
| [0008](0008-nested-types-in-first-release.md) | The first release writes structs, lists, and maps at any depth. |
| [0009](0009-compatibility-profiles.md) | Profiles are named presets over individual options, and options can be overridden. |
| [0010](0010-default-profile.md) | The default profile is the one all verified readers accept. |
| [0011](0011-verified-readers-and-test-tiers.md) | Which readers verify the output, and which tests need live accounts. |
| [0012](0012-own-compression-codecs.md) | Core implements its own Snappy and LZ4 compressors. Zstd comes later. |
| [0013](0013-optional-format-features.md) | Page index, bloom filters, and encryption are in the first release. |
| [0014](0014-write-api.md) | The write API has a high-level form and a low-level synchronous form. |
| [0015](0015-async-only-core.md) | Core I/O is async only. Sync wrappers live in a separate package. |
| [0016](0016-dependency-injection-package.md) | Dependency injection support is a separate package. |
| [0017](0017-types-that-need-an-explicit-representation.md) | Guid, TimeOnly, Half, and unsigned integers need an explicit representation. |
| [0018](0018-decimal-mapping.md) | Decimals default to precision 38 and scale 18 and are never rounded silently. |
| [0019](0019-datetime-mapping.md) | A DateTime of unspecified kind raises an error unless a policy is set. |
| [0020](0020-spark-version-metadata-key.md) | The default profile writes the Spark version key so Spark 3.x reads old dates. |
| [0021](0021-memory-budget.md) | Memory is tracked against a soft per-writer budget. |
| [0022](0022-documentation.md) | Decisions and architecture are documented in the repository. |
| [0023](0023-tooling.md) | xUnit, BenchmarkDotNet, and GitHub Actions. |
| [0024](0024-working-rules-for-contributions.md) | Writing rules and three review steps for every pull request. |
| [0025](0025-required-columns-from-nullable-annotations.md) | A non-nullable reference type becomes a required column. |
| [0026](0026-enum-mapping.md) | An enum is written as its number by default, with text as an option. |
| [0027](0027-timespan-needs-an-explicit-representation.md) | TimeSpan needs an explicit representation. |
| [0028](0028-unsupported-types-in-first-release.md) | char, Int128, UInt128, and BigInteger are not supported in the first release. |
| [0029](0029-timestamp-precision-loss.md) | A timestamp that does not fit in microseconds raises an error unless truncation is allowed. |
| [0030](0030-target-dotnet-10.md) | Target .NET 10 only. |
| [0031](0031-pyarrow-as-reference.md) | pyarrow is the reference for what is written to a file. |
| [0032](0032-reserved-memory-for-footer-data.md) | A share of the memory budget is reserved for footer and page index data. |
| [0033](0033-value-error-ends-the-write.md) | A value that cannot be written ends the write. |
| [0034](0034-dotnet-built-in-encoders.md) | The Zstandard and Gzip encoders built into .NET 11 are not used yet. |
| [0035](0035-byte-annotation.md) | A byte column is annotated as an unsigned 8-bit integer. |
| [0036](0036-decimal-storage.md) | Decimals are stored as fixed-length bytes in the smallest width that fits. |
