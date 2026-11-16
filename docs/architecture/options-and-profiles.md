# Options and profiles

## Profiles

A profile is a named set of defaults chosen so that a particular group of
readers can read the output.

| Setting | `Compatible` (default) | `Modern` |
|---|---|---|
| Intended readers | Spark 3.3 and later, Databricks, Arrow-based tools, cloud warehouses | Current Arrow-based tools and other readers that support the newer format features |
| Data page version | 1 | 2 |
| Encodings | PLAIN, dictionary | Adds the delta encodings and BYTE_STREAM_SPLIT |
| Default codec | Snappy | To be decided |
| Timestamps | Microseconds, UTC | Microseconds, UTC. Nanoseconds are allowed. |
| UUID, TIME, FLOAT16, unsigned annotations | Validation message if chosen | Allowed |
| Spark version key in metadata | Written | To be decided |
| Page index | Written | Written |

A profile is an object with a name, so more can be added later. A `Databricks`
profile will be added if testing shows that Databricks needs different settings
from Spark.

## Options

`ParquetWriterOptions` is a plain class. Most of its properties are nullable,
and null means "use the profile's value".

```csharp
public sealed class ParquetWriterOptions
{
    public string Profile { get; set; } = "Compatible";
    public DataPageVersion? DataPageVersion { get; set; }
    public CompressionKind? Compression { get; set; }
    public long MemoryBudgetBytes { get; set; }
    public RowGroupOptions RowGroup { get; }
    public Dictionary<string, ColumnOptions> Columns { get; }
    // ...
}
```

This shape was chosen so that the class can be filled from a configuration
file by the standard .NET configuration binder, without core referencing any
configuration package.

Options cover, among other things: profile, codec, page size, row group size,
memory budget, the policy for `DateTime` values of unspecified kind, whether
timestamps may be truncated to microseconds, default decimal precision and
scale, whether statistics and the page index are written,
user key-value metadata, and per-column settings such as codec, encoding, and
bloom filter.

## How settings are resolved

When a writer is created, settings are combined in this order. Later steps
override earlier ones.

1. The profile's defaults.
2. Writer options that are not null.
3. Per-column options.

The result is checked and frozen. The writer uses the frozen result and ignores
later changes to the options object.

## Validation

Validation runs once, when the writer is created, against the schema of the
type being written. It collects every problem and reports them together.

There are two kinds of finding.

An error means the file cannot be written as configured. Examples: a memory
budget below the minimum for the number of columns, a decimal precision of
zero, a bloom filter on a column that does not exist.

A compatibility message means the file can be written, but a reader the profile
is meant for cannot read it. Examples under the default profile: LZ4_RAW
compression, a `Guid` column stored with the UUID annotation, a column name
containing a space. Each message names the setting, the column if there is one,
and the reader affected.

By default, compatibility messages are reported and the writer is still
created. A strict setting turns them into errors. How messages are reported
(a callback, a diagnostic event, or both) will be settled when validation is
built.
