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

A staged destination accepts segments in any order, and several at once. Each
call returns an identifier. `SealAsync` then takes a list of identifiers and
appends those segments, in that order, to the file. `Constraints` states the
smallest and largest segment the destination accepts, the most segments it can
hold, and how many uploads may run at once.

A destination must not keep a reference to the data it was given after its call
completes. The writer reuses that memory.

| Destination | Kind | Package |
|---|---|---|
| A `Stream` | Sequential | `Parquetry` |
| Local temp files, joined into another destination | Staged | `Parquetry` |
| Azure Blob Storage | Staged | `Parquetry.Azure` |
| Amazon S3 | Sequential | `Parquetry.S3` |

### Azure

`StageAsync` uploads a block. `SealAsync` records the order. `CompleteAsync`
commits the block list, at which point the blob becomes visible. Until then
nothing is visible to readers, and an aborted write leaves no blob.

### S3

The destination gathers bytes into parts and uploads several parts at once.
When all its upload slots are busy, its `WriteAsync` does not complete until
one is free. That delay is how it tells the writer to slow down. The part size
grows as the upload grows, to stay under the limit of 10,000 parts.
`CompleteAsync` completes the multipart upload, and `AbortAsync` cancels it.

### Temp files

Each column's pages are appended to a temp file. When a row group closes, the
files are copied into the inner destination in column order. This keeps memory
use low for any destination, at the cost of local disk space and a second copy
of the data.

## Layouts

Core has one layout for each kind of destination. These interfaces are
internal.

The buffered layout works with a sequential destination. It holds the encoded,
compressed pages of the current row group in memory. When the row group closes,
it writes each column's dictionary page and data pages in order.

The staged layout works with a staged destination. As pages are finished, it
groups them into segments that satisfy the destination's limits and stages
them. When the row group closes, it seals the segments in column order. Small
column chunks are combined into shared segments, so that the number of segments
stays within the limit however many columns and row groups a file has.

Both layouts follow the same rules:

- A column's dictionary page comes first in its chunk, followed by its data
  pages in the order they were produced.
- The layout owns page memory from the moment the column writer asks for it
  until the destination has accepted it.
- The layout reports the starting position of each column chunk. Core computes
  everything in the footer and page index from those positions and from the
  page sizes it recorded. A layout never writes metadata.
- Calls for one column come one at a time. Calls for different columns may
  overlap, which leaves room for encoding columns in parallel.

For the same input and options, both layouts must produce the same file. Tests
compare them byte for byte.

## When the file becomes visible

`CompleteAsync` on the writer writes the page index and footer and then
completes the destination. If the writer is disposed without that call, it
aborts the destination. For S3 and Azure this means a failed write leaves no
object. For a stream, the bytes already written remain, and the caller decides
what to do with them.
