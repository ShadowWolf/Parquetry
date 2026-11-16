# Encoding and compression

A page goes through two steps before it is stored. Encoding turns values into
bytes in a compact form suited to the column's type. Compression then shrinks
those bytes with a general-purpose codec.

## Encodings

| Encoding | Used for | Profile |
|---|---|---|
| PLAIN | Any type. Values are written one after another. | Both |
| RLE and bit-packing hybrid | Repetition levels, definition levels, and dictionary positions. | Both |
| Dictionary (RLE_DICTIONARY) | Columns with repeated values. Each distinct value is stored once, and the pages hold positions in that list. | Both |
| DELTA_BINARY_PACKED | Integers that change slowly, such as timestamps and counters. | Modern |
| DELTA_LENGTH_BYTE_ARRAY | Strings and bytes. | Modern |
| DELTA_BYTE_ARRAY | Strings that share prefixes with their neighbors. | Modern |
| BYTE_STREAM_SPLIT | Floating-point numbers. | Modern |

The default profile uses only the first three because every Spark version
checked reads them. According to Spark's source, Spark 3.3 cannot read
DELTA_LENGTH_BYTE_ARRAY, and Spark's fast reader handles BYTE_STREAM_SPLIT only
from version 4.3. Details are in
[Spark and Databricks compatibility](spark-and-databricks-compatibility.md).

### Dictionary encoding

A column starts with dictionary encoding. If the dictionary grows past a size
limit, the column switches to PLAIN for the remaining pages of that chunk. The
pages already written stay as they are. The dictionary page is written when the
chunk ends and placed first in the chunk.

The dictionary lives in memory for as long as the chunk is open. Its size is
counted against the memory budget.

## Compression

| Codec | Source | Default profile |
|---|---|---|
| None | | Allowed |
| Snappy | Implemented in core | Allowed, and the default |
| Gzip | .NET base class library | Allowed |
| LZ4_RAW | Implemented in core | Validation message: Spark reads it only from version 3.5 |
| Brotli | .NET base class library | Validation message: Spark does not include a Brotli codec |
| Zstd | Planned for a later release | Readable by Spark. Until core has it, a user can supply one through the codec interface. |

The library never writes the older LZ4 framing, which differs between
implementations.

### Codec interface

```csharp
public interface IParquetCodec
{
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

A user can register a codec of their own, for example one that wraps an
existing Zstd library.

### The compressors written for this library

Snappy and LZ4_RAW are implemented in core. Only compression is needed. Tests
decompress the output with reference implementations, which are dependencies of
the test projects only, over generated inputs and inputs designed to hit edge
cases. Benchmarks compare speed and ratio with existing managed libraries.
