# Parquetry

Parquetry is a C# library that writes .NET objects to Parquet files. It is
built for low, bounded memory use and high throughput, and it streams output to
the destination where the Parquet format allows.

**Status: design stage.** The architecture is documented and no library code
exists yet. Nothing is published on NuGet.

## Goals

- Keep memory for row data under a limit the caller sets, whatever the file
  size. Metadata that must be kept until the end of the file grows slowly
  with it.
- Write rows quickly, with no allocation per row.
- Produce files that Apache Spark, Databricks, pyarrow, Polars, DuckDB, and
  cloud warehouses read without reader settings.
- Use Amazon S3 and Azure Blob Storage features directly through add-on
  packages.
- Work with dependency injection and configuration, and also without them.

## Planned packages

| Package | Purpose |
|---|---|
| `Parquetry` | The writer, the source generator, and local destinations. No dependencies. |
| `Parquetry.Azure` | Writes to Azure Blob Storage, uploading blocks while a row group is still open. |
| `Parquetry.S3` | Writes to Amazon S3 with parallel multipart upload. |
| `Parquetry.Extensions.DependencyInjection` | Service registration, configuration binding, named options. |
| `Parquetry.Sync` | Synchronous wrappers for callers that cannot use async code. |

The library targets .NET 8 and .NET 10.

## Planned usage

This is a sketch of the intended API. Names may change before the first
release.

```csharp
[ParquetSerializable]
public partial class Order
{
    public long Id { get; set; }
    public DateTimeOffset PlacedAt { get; set; }
    public List<OrderLine> Lines { get; set; }
}

await using var writer = ParquetWriter.Create<Order>(destination);
await writer.WriteAsync(orders, cancellationToken);
await writer.CompleteAsync(cancellationToken);
```

## Documentation

- [Architecture](docs/architecture/README.md)
- [Decision records](docs/adr/README.md)
- [Roadmap](docs/architecture/roadmap.md)
- [Working rules for contributors](AGENTS.md)

## License

[MIT](LICENSE)
