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
- A share of the budget is reserved for footer data, as described under
  "The reserved share" below. The rest is the row data part.
- When usage reaches the limit of the row data part, the writer's `NeedsFlush`
  property becomes true. The caller is expected to call `FlushAsync` before
  the next `Write`.
- If the caller does that, the most the writer can exceed the budget by is one
  row plus one page per column. A caller who does not flush has no limit.

When a writer is created, the library works out the smallest budget that could
work: enough for one small page per column, working space, and the reserved
share. If the
configured budget is lower, creation fails and the error states the computed
minimum.

## What a flush does

`NeedsFlush` is true when the writer wants the caller to call `FlushAsync`.
If it is false, `FlushAsync` returns at once and does not close a row group
early.

| Layout | `NeedsFlush` becomes true when | `FlushAsync` then |
|---|---|---|
| Buffered | Usage reaches the limit for row data, or the row group reaches its target size | Closes the row group and writes it to the destination. |
| Staged | A pending segment reaches the target size, or usage reaches the limit for row data | Stages the segments that reached the target size. If usage is still at that limit, it also stages the largest of the other pending segments until usage is below it. Row groups close by their own size target, independent of the budget. |

A destination can make a flush take longer. The S3 destination does this when
all its upload slots are busy. It has no effect on `NeedsFlush`.

With the buffered layout, the budget also caps the row group size. A small
budget on a table with many columns produces small row groups, which compress
less well and are slower to read. The writer reports row group sizes as a
metric. Users who need large row groups with little memory use a staged
destination: Azure, or the temp-file destination in front of a sequential
destination such as S3.

## What the budget does not bound

Three things grow with the size of the file and work against the budget:

- Page index and footer records. Every page adds a record that is kept until
  the file is complete. A flush does not free them. A share of the budget is
  reserved for them, as described below.
- S3 part buffers. The part size rises as the upload grows, to stay under
  10,000 parts. The destination holds this memory. Whether it is counted
  against the budget depends on the open question in the next section.
- The segment limit of a staged destination. To stay under it, the staged
  layout raises its target segment size as the file grows, so each column
  holds more pending bytes. Those bytes are counted against the budget, and a
  flush under memory pressure stages them early. Each early segment uses up
  one of the destination's segments, so a very large file with a small budget
  can reach the limit.

### The reserved share

A share of the budget is set aside for page index and footer records.
Everything else in the table at the top of this page is charged to the rest,
the row data part, and `NeedsFlush` is worked out against that part only.
While the share has room, growth in footer records does not cause extra
flushes or smaller row groups. The cost is that the row data part is smaller
than the budget from the first row.

The size of the share is a setting, with a default to be chosen from
benchmarks. The amount in use is reported as a metric. A user who turns the
page index off needs a much smaller share.

So memory for row data is bounded by its part of the budget. Memory for footer
data is bounded by the reserved share only once the next point is decided.

Still to be decided, and listed in the
[architecture overview](README.md#open-questions):

- What the writer does when the share is used up: raise an error that names
  the setting, or continue over the budget and report it.
- Whether the share is set as a number of bytes or as a fraction of the
  budget, and how it works when several writers use one budget.
- What the writer does when a staged destination runs out of segments.

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

Uploading S3 parts in parallel holds more memory at once. That memory is
meant to come from the same budget, so that turning it on leaves less room for
buffered pages and does not raise the writer's total. It depends on the open
question above about memory held by a destination.

Encoding columns in parallel is planned for a late milestone and is not
designed. `Write` is synchronous and a writer is used from one thread, so the
design has to say where the parallel work runs. This is an open question.

## Defaults

The default page size, row group size, dictionary size limit, memory budget,
and reserved share are not yet set. They will be chosen from benchmark results when the
budget is built.
