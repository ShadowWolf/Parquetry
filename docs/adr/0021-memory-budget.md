# Memory is tracked against a soft per-writer budget

Status: accepted
Date: 2026-11-14

## Context

Bounded memory use is the first priority of the library. The writer holds
memory in several places: values waiting to be encoded, dictionaries, finished
pages waiting to be written, working space for encoding and compression,
uploads in progress, and data for the footer and page index. A limit only
works if all of these are counted.

A hard limit would mean that a row write could block or fail when memory runs
out. Blocking inside a synchronous call is not acceptable, and failing would
make the writer hard to use.

## Options considered

1. A soft budget. The writer counts all memory, signals when the caller should
   flush, and may go over by a small, known amount.
2. A hard limit that blocks or throws.
3. A limit on rows per row group and no byte accounting.

## Decision

Option 1.

- Each writer has a memory budget in bytes. Several writers can share one.
- All pooled buffers are rented through one component that charges the budget
  for the rented size.
- `Write` never blocks or throws because of the budget. When usage reaches the
  budget, `NeedsFlush` becomes true.
- If the caller flushes when `NeedsFlush` is true, the most the writer can go
  over is one row plus one page per column.
- When a writer is created, the library computes the smallest budget that can
  work for the number of columns and fails if the configured budget is lower.
  The error states the computed minimum.

## Consequences

- Every buffer has one owner at a time, and passing a buffer to another
  component is an explicit step. Debug builds use a pool that detects leaks
  and use after return.
- A destination must not keep a reference to the caller's memory after its
  write call completes.
- Parallel uploads take their memory from the same budget. Turning them on
  reduces the space left for buffered pages. It does not raise total memory
  use. Parallel encoding is planned to work the same way and is not designed
  yet.
- A table with many columns has a minimum memory need that grows with the
  column count. Page size is reduced automatically when the budget is tight.
- With in-memory buffering, the budget limits row group size. The writer
  reports row group sizes as a metric so users can see when the budget is
  making row groups small.
- Footer and page index data grow with file size. They are counted in the
  budget, but a flush cannot free them. What the writer does when they alone
  approach the budget is an open question. So are two others: how a
  destination charges the memory it holds, and which writer flushes when
  several share a budget. All three are described in
  [Memory](../architecture/memory.md).
