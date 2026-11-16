# Memory

Bounded memory use is the library's first priority. This page describes how
memory is counted and limited.

## What holds memory

| Category | What it is |
|---|---|
| Values and levels | Values appended to column buffers and not yet encoded. |
| Dictionaries | The distinct values of each dictionary-encoded column in the open row group. |
| Held pages | Encoded, compressed pages waiting to be written or staged. |
| Working space | Scratch memory for encoding and compression. |
| In flight | Data handed to a destination and not yet accepted, such as S3 parts being uploaded. |
| Metadata | Row group and page records kept for the footer and page index, and open bloom filters. |

## The budget

Each writer has a memory budget in bytes. Several writers can share one budget.

All buffers are rented from a pool through one component, which charges the
budget for the full rented size and credits it when the buffer is returned.
Nothing in the library rents pooled memory any other way.

The budget is a soft limit:

- `Write` never blocks and never fails because of the budget.
- When usage reaches the budget, the writer's `NeedsFlush` property becomes
  true. The caller is expected to call `FlushAsync` before the next `Write`.
- The most the writer can exceed the budget by is one row plus one page per
  column.

When a writer is created, the library works out the smallest budget that could
work: enough for one small page per column, working space, and the
destination's uploads in progress. If the configured budget is lower, creation
fails and the error states the computed minimum.

## What a flush does

| Layout | `NeedsFlush` becomes true when | `FlushAsync` then |
|---|---|---|
| Buffered | Usage reaches the budget, or the row group reaches its target size | Closes the row group and writes it to the destination. |
| Staged | A segment is ready to stage, or pending bytes reach the budget | Stages the ready segments. Row groups close by their own size target, independent of the budget. |
| Buffered, to S3 | As buffered, or all upload slots are busy | As buffered, and waits for an upload slot. |

With the buffered layout, the budget also caps the row group size. A small
budget on a table with many columns produces small row groups, which compress
less well and are slower to read. The writer reports row group sizes as a
metric. Users who need large row groups with little memory use a staged layout.

## Tables with many columns

Every column needs at least a partly filled page of memory. For a table with
hundreds of columns, this floor can be a large part of the budget. When the
budget is tight, the writer reduces the page size it aims for, down to a
minimum, before it reports that the budget is too small.

## Buffer ownership

- A buffer has exactly one owner at a time.
- Passing a buffer to another component is an explicit transfer.
- A layout owns page memory until the destination has accepted the bytes.
- A destination does not keep caller memory after its call completes.
- Debug builds use a pool that fills returned buffers with a marker value and
  tracks buffers that were never returned, so misuse shows up in tests.

## Parallel work

Encoding columns in parallel and uploading parts in parallel both hold more
memory at once. That memory is reserved from the same budget before the work
starts. Turning parallelism on leaves less room for buffered pages. It does not
increase the writer's total memory use.

Shredding a row is single-threaded. To use more cores for shredding, an
application runs several writers that share one budget.

## Defaults

The default page size, row group size, and memory budget are not yet set. They
will be chosen from benchmark results when the budget is built.
