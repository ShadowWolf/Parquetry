# Which readers verify the output, and which tests need live accounts

Status: accepted
Date: 2026-11-14

## Context

The library does not read Parquet, so other tools must confirm that its files
are correct. The choice of tools decides what the profiles can promise. Some
tools run in a container. Others, such as Databricks and cloud warehouses, need
a paid account and credentials.

## Options considered

For which readers: Apache Spark; pyarrow, Polars, and DuckDB, each of which
has its own Parquet reader; Trino and Athena; and cloud warehouses (Snowflake,
BigQuery, Redshift Spectrum).

For tests that need accounts: run them automatically only when credentials are
supplied, check by hand before each release, or leave them until after the
first release.

## Decision

The verified readers are Apache Spark, pyarrow, Polars, DuckDB, and the cloud
warehouses. Trino and Athena are not verified in the first release.

Tests run in two tiers:

- On every pull request, in containers: pyarrow, Polars, DuckDB, and Spark
  3.5 and the current 4.x release.
- Only when credentials are supplied, in a scheduled or manually started
  workflow: Databricks (with Photon on and off), Snowflake, BigQuery, and
  Redshift Spectrum. Live Azure and S3 tests run the same way.

## Consequences

- A pull request can pass without the live tests having run. A release
  checklist requires a recent successful live run.
- The Spark container tests cover open-source Spark only. Anything specific to
  Databricks is confirmed only by the live tier.
- Spark 3.3 and 3.4 are not in the test matrix. The default profile avoids
  the features those versions lack, according to Spark's source, but this is
  not tested.
- The project needs accounts and credentials for the live tier before the
  first release.
