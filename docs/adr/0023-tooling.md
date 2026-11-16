# xUnit, BenchmarkDotNet, and GitHub Actions

Status: accepted
Date: 2026-11-14

## Context

The project needs a test framework, a way to measure speed and allocation, and
continuous integration that can run containers with Spark and Python tools.

## Options considered

For tests: xUnit v3, TUnit, or NUnit. BenchmarkDotNet and GitHub Actions were
common to all three options.

## Decision

- xUnit v3 for unit and integration tests.
- BenchmarkDotNet for throughput and allocation benchmarks.
- GitHub Actions for continuous integration.

## Consequences

- xUnit is the most widely used test framework among open-source .NET
  libraries, so most contributors know it.
- Benchmarks compare Parquetry with `Parquet.Net` and `ParquetSharp`. Those
  libraries are referenced only by the benchmark project.
- Continuous integration runs in the project's GitHub repository.
- Reader tests start containers, so the CI runners must support Docker.
