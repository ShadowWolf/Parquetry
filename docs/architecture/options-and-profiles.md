# Options and profiles

## Profiles

A profile is a named set of defaults chosen so that a particular group of
readers can read the output.

| Setting | `Compatible` (default) | `Modern` |
|---|---|---|
| Intended readers | Spark 3.5 and later, Databricks, pyarrow, Polars, DuckDB, and cloud warehouses. Spark 3.3 and 3.4 are expected to work, from reading Spark's source. They are not in the tests that run on every pull request. One test, of decimals and byte columns, has been run on them. | Current versions of pyarrow, Polars, and DuckDB, and other readers that support the newer format features |
| Data page version | 1 | 2 |
| Encodings | PLAIN, dictionary | Adds the delta encodings and BYTE_STREAM_SPLIT |
| Default codec | Snappy | To be decided |
| Timestamps | Microseconds, UTC. Nanoseconds produce a compatibility message if chosen. | Microseconds, UTC. Nanoseconds are allowed. |
| UUID, TIME, FLOAT16, unsigned annotations on `ushort`, `uint`, and `ulong`, fixed-length bytes with no annotation | Compatibility message if chosen | Allowed |
| Spark version key in metadata | Written | To be decided |
| Page index | Written | Written |

A profile is an object with a name, and core holds the built-in ones under
their names. Options refer to a profile by name, as text, so that the choice
can come from a configuration file. More profiles can be added later without
changing existing code. A `Databricks`
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
    public long? MemoryBudgetBytes { get; set; }
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
scale, whether small decimals are stored as integers, whether statistics and the page index are written,
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

Some column settings can also be given by an attribute on a property or on a
context class. How those combine with per-column options is not settled yet.

## Validation

Validation runs once, when the writer is created, against the schema of the
type being written. It collects every problem and reports them together. The
dependency injection package also runs the checks that need no row type when
the application starts.

There are two kinds of finding.

An error means the file cannot be written as configured. Examples: a memory
budget below the minimum for the number of columns, a decimal precision of
zero, a bloom filter on a column that does not exist.

A compatibility message means the file can be written, but a reader or table
format the profile is meant for cannot read it or will reject it. Examples
under the default profile: LZ4_RAW compression, a `Guid` column stored with
the UUID annotation, a column name containing a space, which a Delta table
rejects. Each message names the setting, the column if there is one,
and the reader affected.

By default, compatibility messages are reported and the writer is still
created. A strict setting turns them into errors. How messages are reported
(a callback, a diagnostic event, or both) will be settled when validation is
built.

## Not yet decided

- For the `Modern` profile: its default codec, whether it writes the Spark
  version key, how it picks an encoding for a column, and whether it stores
  small decimals as integers so that its delta encoding can apply.
- Whether a `Databricks` profile is needed.
- Which setting wins when a column is configured both by an attribute and in
  `Columns`, and how `Columns` names a nested column or a renamed one.
- How compatibility messages are reported.
- How a user registers a profile of their own.
