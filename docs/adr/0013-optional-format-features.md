# Page index, bloom filters, and encryption are in the first release

Status: accepted
Date: 2026-11-14

## Context

Beyond data and a footer, Parquet defines optional features that help readers
or protect data:

- The page index records the value range and position of every page, so a
  reader can skip pages inside a row group.
- A bloom filter lets a reader rule out a row group when looking for a
  specific value in a column with many distinct values.
- Modular encryption encrypts columns and the footer with AES, with separate
  keys per column if wanted.

Minimum and maximum statistics per column chunk, and key-value metadata in the
footer, are treated as baseline and are always available.

## Options considered

Include any combination of the three features in the first release, or none and
add them later.

## Decision

All three are in the first release.

## Consequences

- The page index needs statistics for every page kept until the file is
  finished. This memory grows with file size. It is counted against the memory
  budget, and long values are shortened to a fixed length in the index.
- The page index is on by default in both profiles, because readers that do
  not use it ignore it. It can be turned off.
- Bloom filters use memory for every column that has one for as long as the
  row group is open. They are off unless the user turns them on for a column.
- Bloom filters need the xxHash64 function, which is not in the base class
  library. Core implements it.
- Encryption uses the AES implementation in the base class library. Core
  defines how the user supplies keys. It does not include integrations with
  key management services.
- An encrypted file always needs keys configured on the reader. This is the one
  case where the default profile's promise of "no reader settings" cannot hold.
- Wrong statistics make readers skip rows that match a query, and nothing
  reports the error. Tests run filtered queries in Spark and DuckDB to check
  that no rows are lost. Where the correct statistic is uncertain, such as
  for NaN values, it is left out.
