# The write API has a high-level form and a low-level synchronous form

Status: accepted
Date: 2026-11-14

## Context

Writing a row is fast and usually needs no I/O. Sending data to storage is slow
and should be asynchronous. If every row write were an async call, each one
would carry overhead that adds up over millions of rows, and the row could not
be passed by reference.

## Options considered

1. A layered API: high-level methods that take a sequence or batch and handle
   flushing, plus a low-level synchronous write with an explicit async flush.
2. One method, `ValueTask WriteAsync(T row)`, which completes synchronously
   unless a flush is due.
3. Batch methods only, with no per-row method.

## Decision

Option 1.

```csharp
// High level
await using var writer = ParquetWriter.Create<Order>(destination, options);
await writer.WriteAsync(ordersAsyncEnumerable, ct);
await writer.WriteAsync(batchMemory, ct);

// Low level: synchronous writes, async only when a flush is due
foreach (var order in orders)
{
    writer.Write(in order);
    if (writer.NeedsFlush)
        await writer.FlushAsync(ct);
}
await writer.CompleteAsync(ct);
```

## Consequences

- `Write` does no I/O. It reads the row, appends values to column buffers, and
  encodes and compresses a page when a buffer fills.
- I/O happens in `FlushAsync` and `CompleteAsync`. The high-level methods
  call `FlushAsync` themselves, and disposing a writer that was not completed
  aborts the destination.
- `NeedsFlush` means the caller should call `FlushAsync` before the next
  `Write` to stay within the memory budget. Reading it costs one field read.
- A caller who ignores `NeedsFlush` uses more memory but still gets a correct
  file.
- `CompleteAsync` finishes the file. Disposing a writer without calling it
  aborts the file and commits nothing, so a failed write does not leave a
  truncated file that looks complete.
- Writing from an `IAsyncEnumerable<T>` costs one async step per row, which
  comes from that interface and cannot be avoided.
