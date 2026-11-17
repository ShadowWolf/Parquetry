# Public API

The examples here show the intended shape of the API. Names and signatures may
change before the first release.

## Creating a writer

A writer is created with a static method on `ParquetWriter`. The form depends
on how the row type was registered, as described in
[Shredding and the source generator](shredding-and-source-generator.md).

```csharp
// A type marked with [ParquetSerializable]
await using var writer = ParquetWriter.Create<Order>(destination, options);

// A type listed on a context class
await using var writer = ParquetWriter.Create(
    destination, MyParquetContext.Default.ThirdPartyDto, options);

// A type the source generator has not seen. Not usable under Native AOT.
await using var writer = ParquetWriter.CreateDynamic<LateBoundRow>(destination, options);
```

The first form needs no reflection. The generator adds a member to the marked
type, which is why the type must be `partial`, and `Create<T>` reaches the
generated code through it. A type on a context class cannot be changed, so the
context exposes an object for it and the caller passes that object.

The third form builds its code when the writer is created. It has a different
name so that a caller cannot use it by accident, and the compiler warns when
it is used in a Native AOT or trimmed build.

The destination is a `Stream` or any destination object. The S3 and Azure
packages provide ways to create their destinations from the respective SDK
clients. The options argument can be left out.

## Writing

There are two ways to write rows.

The high-level methods take a sequence or a batch and flush when needed:

```csharp
await writer.WriteAsync(ordersAsyncEnumerable, ct);   // IAsyncEnumerable<Order>
await writer.WriteAsync(ordersEnumerable, ct);        // IEnumerable<Order>
await writer.WriteAsync(batch, ct);                   // ReadOnlyMemory<Order>

await writer.CompleteAsync(ct);
```

The low-level form gives the caller control of the loop. `Write` is synchronous
and does no I/O:

```csharp
foreach (var order in orders)
{
    writer.Write(in order);
    if (writer.NeedsFlush)
        await writer.FlushAsync(ct);
}
await writer.CompleteAsync(ct);
```

| Member | Behavior |
|---|---|
| `Write(in T)` | Shreds the row into column buffers. Encodes and compresses a page when a buffer fills. Does no I/O and does not allocate. |
| `NeedsFlush` | True when the writer wants the caller to call `FlushAsync`: the part of the memory budget for row data is full, or a row group or segment is ready to be sent. Reading it costs one field read. |
| `FlushAsync` | Sends data to the destination. If `NeedsFlush` is false it returns at once and does not close a row group early. |
| `WriteAsync` | Calls `Write` for each row and `FlushAsync` whenever `NeedsFlush` is true. |
| `CompleteAsync` | Closes the last row group, whatever its size, writes the page index and footer, and completes the destination. The file is valid only after this. |
| `DisposeAsync` | Releases memory. If `CompleteAsync` was not called, aborts the destination. |

`Write` does no I/O. I/O happens in `FlushAsync`, in `CompleteAsync`, in the
`WriteAsync` methods because they flush, and in `DisposeAsync` when it aborts.

A caller who never checks `NeedsFlush` still gets a correct file, but the
writer's memory use is then not bounded.

Writing from an `IAsyncEnumerable<T>` involves one async step per row, which
that interface requires. The other forms have no async overhead per row.

A writer is not safe to use from several threads at once.

## Errors while writing

`Write` raises an error when a value cannot be stored as the schema requires.
Examples are a null in a required column, a decimal that does not fit its
precision and scale, and a timestamp that would lose precision. The error
names the column. The full list of cases is in the decision record
[a value that cannot be written ends the write](../adr/0033-value-error-ends-the-write.md).

The error is raised partway through the row, after some columns have already
received their values. The writer cannot continue after it. Every method
except `DisposeAsync` then raises an error, and disposing aborts the file. One
bad value therefore ends the whole write. A caller who expects bad data checks
or cleans rows before writing them.

Two other errors from `Write` are not about a value: the share of the memory
budget reserved for footer data is used up, or a limit of an encrypted file is
reached. They end the write in the same way.

The state of the writer after `FlushAsync` or `CompleteAsync` fails is an open
question, listed in the [architecture overview](README.md#open-questions).

## Dependency injection

`Parquetry.Extensions.DependencyInjection` adds registration for applications
that use `Microsoft.Extensions`:

```csharp
services.AddParquetWriter(options =>
{
    options.Profile = "Compatible";
    options.MemoryBudgetBytes = 256 * 1024 * 1024;
});

// Or from configuration, with a name
services.AddParquetWriter("exports", configuration.GetSection("Parquet:Exports"));
```

It registers a writer factory, which creates writers from the configured
options. Named options let one application hold several configurations.

Checks that need no row type run when the application starts: that the profile
exists, that the codec is known, that the numbers are in range. Checks that
depend on the row type, such as column names and the smallest workable budget,
run when a writer is created, as they do without this package.

## Synchronous package

Core has no synchronous flush or complete. `Parquetry.Sync` adds `Flush`,
`Complete`, and synchronous overloads of the high-level write methods. They
wait on the async methods.

Blocking on async code is safe in console applications and ASP.NET Core. In
applications with a synchronization context, such as desktop UI frameworks, it
can deadlock, and under heavy load it can exhaust the thread pool. The package
is separate and optional for that reason.

## Diagnostics

Core reports through `System.Diagnostics`, which needs no extra packages:

- Metrics: rows written, bytes written, row group sizes, memory in use against
  the budget, how much of the share reserved for footer data is in use, and
  time spent in flushes.
- Activities: one per file and one per flush, for tracing.

Applications collect these with OpenTelemetry or any other listener.
