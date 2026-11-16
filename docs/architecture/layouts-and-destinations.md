# Layouts and destinations

A destination is where the file's bytes go: a stream, an S3 object, an Azure
blob. A layout decides when page bytes are sent to the destination and in what
arrangement. The background is in
[Parquet format notes](parquet-format-notes.md).

## Destinations

Core defines two kinds.

```csharp
public interface ISequentialDestination : IAsyncDisposable
{
    ValueTask WriteAsync(ReadOnlySequence<byte> data, CancellationToken ct);
    ValueTask CompleteAsync(CancellationToken ct);
    ValueTask AbortAsync();
}

public interface IStagedDestination : IAsyncDisposable
{
    StagingConstraints Constraints { get; }
    ValueTask<SegmentId> StageAsync(ReadOnlySequence<byte> data, CancellationToken ct);
    ValueTask SealAsync(ReadOnlyMemory<SegmentId> order, CancellationToken ct);
    ValueTask CompleteAsync(CancellationToken ct);
    ValueTask AbortAsync();
}
```

A sequential destination accepts bytes in file order.

A staged destination accepts segments in any order, and several at once. A
segment is a run of bytes. The destination is not told what the bytes contain.
Each call returns an identifier. `SealAsync` then takes a list of identifiers
and appends those segments, in that order, to the file. `Constraints` states
the largest segment the destination accepts, the most segments it can hold,
and how many uploads may run at once.

A staged destination must accept a segment of any size up to its largest. Some
segments are small and cannot be made larger, such as a dictionary page that
has to be placed ahead of data that was already staged. A service that sets a
minimum size for each piece, as S3 does, is therefore used as a sequential
destination.

A destination must not keep a reference to the data it was given after its call
completes. The writer reuses that memory. A destination that needs the bytes
for longer, such as one that gathers them into upload parts, copies them into
memory of its own. How that memory is charged to the writer's budget is an open
question, described in [Memory](memory.md).

| Destination | Kind | Package |
|---|---|---|
| A `Stream` | Sequential | `Parquetry` |
| Local temp files, copied into another destination | Staged | `Parquetry` |
| Azure Blob Storage | Staged | `Parquetry.Azure` |
| Amazon S3 | Sequential | `Parquetry.S3` |

### Azure

`StageAsync` uploads a block. `SealAsync` records the order. `CompleteAsync`
commits the block list, at which point the blob becomes visible. Until then
nothing is visible to readers.

### S3

The destination gathers bytes into parts and uploads several parts at once.
When all its upload slots are busy, its `WriteAsync` does not complete until
one is free, so the writer's `FlushAsync` takes longer. That delay is how the
destination slows the writer down. The part size grows as the upload grows, to
stay under the limit of 10,000 parts. `CompleteAsync` completes the multipart
upload, and `AbortAsync` cancels it.

### Temp files

The temp-file destination is a staged destination that sits in front of a
sequential destination, such as a stream or S3. It appends each staged segment
to a local temp file and records where it is. When segments are sealed, it
copies them in the sealed order into the inner destination. This keeps memory
use low for any sequential destination, at the cost of local disk space and a
second copy of the data. Azure does not need it, because Azure is already a
staged destination.

A user turns this on by wrapping their destination. The sketch below shows the
idea. The names are not final.

```csharp
await using var destination = TempFileDestination.Create(innerDestination, tempDirectory);
await using var writer = ParquetWriter.Create<Order>(destination, options);
```

## Layouts

Core has one layout for each kind of destination, and picks the layout from
the destination the writer is given. The layout types are internal. A user
chooses a layout by choosing a destination.

### Buffered layout

The buffered layout works with a sequential destination. It holds the encoded,
compressed pages of the current row group in memory. When the row group closes,
it writes each column's dictionary page and data pages in order.

### Staged layout

The staged layout works with a staged destination. It does not wait for the
row group to close before sending data.

While a row group is open, each column has a pending segment that collects the
column's finished pages. The layout has a target segment size. It works the
target out from the destination's limits, and its starting value will be set
from benchmarks. During `FlushAsync`, the layout stages every pending segment
that has reached the target size. If memory use is still at the budget after
that, it also stages the largest of the remaining pending segments, below the
target size, until usage is under the budget. A segment staged during a flush
holds pages of one column only.

When the row group closes, each column has two things left in memory: its
dictionary page, which is only complete now, and the pages that were not yet
staged. The layout stages these and then seals all of the row group's segments
in file order. For each column that is its dictionary page, then its data in
the order it was produced.

Leftovers that are next to each other in the file are joined into one segment.
The last pages of one column and the dictionary page of the next go into the
same segment. A column that was too small to be staged before the row group
closed shares a segment with its neighbors. A segment does not have to start
or end where a column chunk does. Only the order of bytes in the file matters.

This keeps the number of segments well below one per page. As a file grows,
the layout also raises the target segment size, so that the count stays under
the destination's limit. A larger target means each column holds more pending
bytes, and that memory is counted against the budget.

The file's first four bytes, each row group's bloom filters, the page index,
and the footer are produced by core and staged and sealed like any other
segment.

### Rules both layouts follow

- A column's dictionary page comes first in its chunk, followed by its data
  pages in the order they were produced.
- The layout owns page memory from the moment the column writer asks for it
  until the destination has accepted it.
- The layout reports the starting position of each column chunk. Core computes
  everything in the footer and page index from those positions and from the
  page sizes it recorded. A layout never produces metadata itself.
- Calls for one column come one at a time. The layouts do not depend on calls
  for different columns coming one at a time, so that columns could later be
  encoded in parallel.

### When the two layouts give the same file

Given the same rows, the same options, and the same row group boundaries, both
layouts produce the same bytes. Tests compare them byte for byte.

In normal use the row group boundaries can differ. The buffered layout closes
a row group when the memory budget is reached, and the staged layout does not.
The writer also lowers its page size when the budget is tight. The comparison
tests therefore fix the page size and use a budget large enough that it never
closes a row group early. Encrypted files are left out of the byte comparison
unless the test supplies the random values that encryption uses, because two
encrypted files are otherwise never identical.

## Completing, aborting, and failures

`CompleteAsync` on the writer closes the last row group, whatever its size,
writes the page index and footer, and then completes the destination. If the writer is disposed without that call, it
aborts the destination.

| Destination | After an abort |
|---|---|
| Azure | No blob is visible. Blocks that were uploaded and not committed stay in the storage account until Azure removes them, which it does after a week. |
| S3 | The multipart upload is cancelled and its parts are removed. |
| A stream | The bytes already written remain, and the caller decides what to do with them. |

If the process ends before the abort runs, an S3 upload is left incomplete and
its parts are billed until they are removed. A bucket lifecycle rule that
aborts incomplete multipart uploads covers this case.

Two points are not yet decided: what state the writer is in after `FlushAsync`
or `CompleteAsync` fails or is cancelled, and whether the writer closes a
stream the caller gave it. Both are listed in the
[architecture overview](README.md#open-questions).
