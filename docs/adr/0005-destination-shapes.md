# Core defines two kinds of destination: sequential and staged

Status: accepted
Date: 2026-11-14

## Context

The writer must send bytes to a local stream, to Amazon S3, and to Azure Blob
Storage. Core must not contain cloud-specific code. Azure can accept pieces of
a file in any order and arrange them at the end. A stream and an S3 upload
accept bytes only in order.

## Options considered

1. Each storage package supplies its own layout strategy that owns the
   connection to storage. Core would only define the strategy interface.
2. Core defines two destination interfaces that describe what storage can do,
   and one layout for each. Storage packages implement only a destination.

## Decision

Option 2. Core defines:

- A sequential destination, which accepts bytes in order.
- A staged destination, which accepts segments in any order, returns an
  identifier for each, and later receives the list of identifiers in final
  order. It also states its limits: smallest and largest segment, and the
  largest number of segments.

A `Stream` is wrapped as a sequential destination. The temp-file spill is a
staged destination that writes to a sequential one. Azure is staged. S3 is
sequential.

## Consequences

- The logic that combines small pages into larger segments to stay within a
  service's limits lives in core once. It can be tested without a cloud
  account by using a fake staged destination with tight limits.
- A storage package is small: it translates destination calls into SDK calls.
- Third parties can support other storage by implementing one interface.
- The interfaces between column writers and layouts stay internal until they
  have been used across two releases. The destination interfaces are the
  public extension point.
