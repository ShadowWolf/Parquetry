# Public API

The examples here show the intended shape of the API. Names may change before
the first release.

## Writing

There are two ways to write rows.

The high-level methods take a sequence or a batch and flush when needed:

```csharp
await using var writer = ParquetWriter.Create<Order>(destination, options);

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
| `Write(in T)` | Shreds the row into column buffers. Encodes and compresses a page when a buffer fills. No I/O, no allocation. |
| `NeedsFlush` | True when the caller should flush to stay within the memory budget. |
| `FlushAsync` | Sends buffered data to the destination. Returns immediately if there is nothing to send. |
| `CompleteAsync` | Writes the page index and footer and completes the destination. The file is valid only after this. |
| `DisposeAsync` | Releases memory. If `CompleteAsync` was not called, aborts the destination. |

A caller who never checks `NeedsFlush` still gets a correct file, but the
writer's memory use is then not bounded.

Writing from an `IAsyncEnumerable<T>` involves one async step per row, which
that interface requires. The other forms have no async overhead per row.

A writer is not safe to use from several threads at once.

## Types known and unknown at build time

A type registered with the source generator is written with generated code,
which works under Native AOT. A type the generator has not seen needs the
runtime fallback, which does not. The two use different method names, so a
caller cannot fall into the runtime path by accident, and the compiler warns
when the runtime method is used in an AOT or trimmed build.

## Destinations

`ParquetWriter.Create` accepts a `Stream` or any destination. The S3 and Azure
packages provide ways to create their destinations from the respective SDK
clients.

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
options. Options are validated when the application starts. Named
registrations let one application hold several configurations.

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
  the budget, time spent in flushes.
- Activities: one per file and one per flush, for tracing.

Applications collect these with OpenTelemetry or any other listener.
