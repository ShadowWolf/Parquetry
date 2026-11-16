# Memory

Bounded memory use is the library's first priority. This page describes how
memory is counted and limited, and what the limit does not cover.

## What holds memory

| Category | What it is |
|---|---|
| Values and levels | Values appended to column buffers and not yet encoded. |
| Dictionaries | The distinct values of each dictionary-encoded column in the open row group. |
| Held pages | Encoded, compressed pages waiting to be written or staged. |
| Working space | Scratch memory for encoding and compression. |
| In flight | Data handed to a destination and not yet accepted, such as S3 parts being uploaded. |
| Metadata | Row group and page records kept for the footer and page index, and the bloom filters of the open row group. |

## The budget

Each writer has a memory budget in bytes. Several writers can share one budget.

All buffers are rented from a pool through one component, which charges the
budget for the full rented size and credits it when the buffer is returned.
Nothing in the library rents pooled memory any other way.

The budget is a soft limit:

- `Write` never blocks and never fails because of the budget.
- When usage reaches the budget, the writer's `NeedsFlush` property becomes
  true. The caller is expected to call `FlushAsync` before the next `Write`.
- If the caller does that, the most the writer can exceed the budget by is one
  row plus one page per column. A caller who does not flush has no limit.

When a writer is created, the library works out the smallest budget that could
work: enough for one small page per column and working space. If the
configured budget is lower, creation fails and the error states the computed
minimum.

## What a flush does

`NeedsFlush` is true when the writer wants the caller to call `FlushAsync`.
If it is false, `FlushAsync` returns at once and does not close a row group
early.

| Layout | `NeedsFlush` becomes true when | `FlushAsync` then |
|---|---|---|
| Buffered | Usage reaches the budget, or the row group reaches its target size | Closes the row group and writes it to the destination. |
| Staged | A segment is ready to stage, or pending bytes reach the budget | Stages the ready segments. Row groups close by their own size target, independent of the budget. |

A destination can make a flush take longer. The S3 destination does this when
all its upload slots are busy. It has no effect on `NeedsFlush`.

With the buffered layout, the budget also caps the row group size. A small
budget on a table with many columns produces small row groups, which compress
less well and are slower to read. The writer reports row group sizes as a
metric. Users who need large row groups with little memory use a staged
destination: Azure, or the temp-file destination in front of any other
destination, including S3.

## What the budget does not bound

Three kinds of memory grow with the size of the file, and a flush does not
free them:

- Page index and footer records. Every page adds a record that is kept until
  the file is complete.
- S3 part buffers. The part size rises as the upload grows, to stay under
  10,000 parts.
- Pending segments in the staged layout. The target segment size rises as the
  file grows, to stay under the destination's segment limit.

All three are counted against the budget and reported as metrics. What the
writer does when they alone approach the budget is not decided. Flushing more
often would not help, and with the buffered layout it would make row groups
smaller, which adds metadata faster. The options are to raise an error with a
clear message, to reserve a share of the budget for this memory, or to leave
it to the user to start a new file. This is listed in the
[architecture overview](README.md#open-questions).

Until that is decided, the accurate statement is this: memory for row data is
bounded by the budget, and memory for metadata and upload buffers grows slowly
with the file.

## Memory held by a destination

The S3 destination copies bytes into part buffers of its own, at least 5 MiB
for each upload slot. That memory should be charged to the writer's budget and
included in the minimum computed at creation. The destination interfaces shown
in [Layouts and destinations](layouts-and-destinations.md) do not yet give a
destination a way to do either. This is an open question.

## Several writers on one budget

When writers share a budget, `NeedsFlush` on each writer depends on the shared
total. With the buffered layout this can ask a writer that holds little memory
to close its row group because another writer holds a lot. The rule for which
writer is asked to flush, or how the budget is divided, is an open question.

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

Shredding a row is single-threaded, and so is the encoding that happens inside
`Write`. To use more cores, an application runs several writers.

Uploading S3 parts in parallel holds more memory at once. That memory comes
from the same budget, so turning it on leaves less room for buffered pages and
does not raise the writer's total.

Encoding columns in parallel is planned for a late milestone and is not
designed. `Write` is synchronous and a writer is used from one thread, so the
design has to say where the parallel work runs. This is an open question.

## Defaults

The default page size, row group size, dictionary size limit, and memory
budget are not yet set. They will be chosen from benchmark results when the
budget is built.
