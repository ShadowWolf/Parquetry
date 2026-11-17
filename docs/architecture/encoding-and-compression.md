# Encoding and compression

A page goes through two steps before it is stored. Encoding turns values into
bytes in a compact form suited to the column's type. Compression then shrinks
those bytes with a general-purpose codec.

## Encodings

| Encoding | Used for | Profile |
|---|---|---|
| PLAIN | Any type. Values are written one after another. | Both |
| RLE and bit-packing hybrid | Repetition levels, definition levels, and dictionary positions. RLE is run-length encoding: a repeated value is stored once with a count. | Both |
| Dictionary (RLE_DICTIONARY) | Columns with repeated values. Each distinct value is stored once, and the pages hold positions in that list. | Both |
| DELTA_BINARY_PACKED | Integers that change slowly, such as timestamps and counters. | Modern |
| DELTA_LENGTH_BYTE_ARRAY | Strings and bytes. | Modern |
| DELTA_BYTE_ARRAY | Strings that share prefixes with their neighbors. | Modern |
| BYTE_STREAM_SPLIT | Floating-point numbers. | Modern |

The default profile uses only the first three, with data page version 1. That
is the combination Spark and pyarrow write by default, so it is the one every
reader has been used with most.

Spark's source shows that it also reads data page version 2,
DELTA_BINARY_PACKED, and DELTA_BYTE_ARRAY from version 3.3. They are still
left out of the default profile, for two reasons. Databricks does not document
which encodings its Photon engine reads, and the cloud warehouses have not
been tested yet. Two of the other encodings are known to fail in Spark:
version 3.3 cannot read DELTA_LENGTH_BYTE_ARRAY, and Spark's vectorized reader
handles BYTE_STREAM_SPLIT only from version 4.3. Details are in
[Spark and Databricks compatibility](spark-and-databricks-compatibility.md).

How the `Modern` profile picks among the newer encodings for a column is not
designed yet.

### Dictionary encoding

A column starts with dictionary encoding, except a BOOLEAN column, which is
never dictionary-encoded. If the dictionary grows past a size
limit, the column switches to PLAIN for the remaining pages of that chunk. The
pages already written stay as they are. The dictionary page is written when the
chunk ends and placed first in the chunk.

The dictionary lives in memory for as long as the chunk is open. Its size is
counted against the memory budget. The size limit will be set from benchmarks.

## Compression

| Codec | Source | Default profile |
|---|---|---|
| None | | Allowed |
| Snappy | Implemented in core | Allowed, and the default |
| Gzip | .NET base class library | Allowed |
| LZ4_RAW | Implemented in core | Compatibility message: Spark reads it only from version 3.5 |
| Brotli | .NET base class library | Compatibility message: Spark does not include a Brotli codec |
| Zstd | Not in core yet | Allowed, because Spark reads it. Until core has it, a user supplies a codec through the interface below. |

The format also defines an older codec named LZ4, whose byte layout differs
between implementations. LZ4_RAW replaced it. The library never writes the
older one.

### Codec interface

```csharp
public interface IParquetCodec
{
    CompressionKind Kind { get; }
    IParquetCompressor CreateCompressor();
}

public interface IParquetCompressor : IDisposable
{
    int GetMaxCompressedLength(int sourceLength);
    int Compress(ReadOnlySpan<byte> source, Span<byte> destination);
}
```

A page is compressed whole, from one span into another. Each column has its own
compressor, so a compressor can keep working memory such as hash tables between
pages without locks. A compressor is not safe to use from two threads at once.

A user can supply a codec of their own, for example one that wraps an existing
Zstd library. `Kind` says which of the format's codecs it produces, and the
writer records that in the footer so that readers know how to decompress the
pages. A supplied codec is used for columns whose compression setting matches
its `Kind`. How a codec is registered on the options will be settled when the
codec interface is built.

### The compressors written for this library

Snappy and LZ4_RAW are implemented in core. Only compression is needed. Tests
decompress the output with reference implementations, which are dependencies of
the test projects only, over generated inputs and inputs designed to hit edge
cases. Benchmarks compare speed and ratio with existing managed libraries.

### .NET 11

.NET 11, released on 2026-11-10, adds `ZstandardEncoder` and `GZipEncoder` to
the base class library. Both compress from one span into another. Neither
exists on .NET 10, which is what the library targets, so the library does not
use them. A user on .NET 11 can wrap the built-in Zstandard encoder in a codec
of their own. The decision is recorded under
[the encoders built into .NET 11](../adr/0034-dotnet-built-in-encoders.md).
