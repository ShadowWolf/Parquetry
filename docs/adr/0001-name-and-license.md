# The library is named Parquetry and licensed under MIT

Status: accepted
Date: 2026-11-14

## Context

The library needs a NuGet package ID, which is also its root namespace, and a
license. It will be used by enterprises, public bodies, and individuals, so the
license has to be permissive. The existing .NET Parquet packages are
`Parquet.Net` and `ParquetSharp`, and the new name should not be confused with
either.

## Options considered

| Name | For | Against |
|---|---|---|
| Parquetry | Contains "Parquet", so it appears in NuGet searches for parquet. Short and distinct. | None found. |
| ParquetStream | Describes the streaming focus. | Reads like a class name. |
| Herringbone | Distinct. | Does not contain "parquet", so people would find it only through tags. |
| Colonnade | Distinct. | Same problem as Herringbone. |

## Decision

The library is named `Parquetry`. Add-on packages use it as a prefix:
`Parquetry.S3`, `Parquetry.Azure`, `Parquetry.Extensions.DependencyInjection`,
and `Parquetry.Sync`. The license is MIT.

## Consequences

- None of the four candidate names had a published package on nuget.org on
  2026-11-14. That check did not cover reserved ID prefixes or trademarks.
- The `Parquetry` prefix should be reserved on nuget.org before the first
  package is published.
- The copyright holder named in `LICENSE` is Bryan Wolf, who publishes the
  library as an individual.
