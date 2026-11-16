# Shredding and the source generator

Shredding means splitting a row into its leaf values and appending each to the
buffer for its column. It runs once per row and decides most of the library's
speed.

## Levels

Parquet stores only leaf values. To rebuild nested data, each stored value
carries two small numbers.

- The definition level says how much of the path to the value is present. It
  records where a null occurred: the value itself, its parent object, or a
  list further up.
- The repetition level says whether the value starts a new row or continues a
  list, and which list when lists are nested.

Take this type:

```csharp
public class Order
{
    public long Id { get; set; }
    public List<OrderLine>? Lines { get; set; }
}

public class OrderLine
{
    public string? Sku { get; set; }
    public int Qty { get; set; }
}
```

Its Parquet schema is:

```
required int64 id;
optional group lines (LIST) {
  repeated group list {
    optional group element {
      optional binary sku (STRING);
      required int32 qty;
    }
  }
}
```

There are three columns: `id`, `lines.list.element.sku`, and
`lines.list.element.qty`. For the `qty` column, the definition level can reach
3 (the list is present, it has an element, the element is not null) and the
repetition level can reach 1.

| Row | `Lines` | Entries appended to the `qty` column |
|---|---|---|
| 1 | Two lines, quantities 2 and 1 | value 2, definition 3, repetition 0; value 1, definition 3, repetition 1 |
| 2 | null | no value, definition 0, repetition 0 |
| 3 | empty list | no value, definition 1, repetition 0 |

Every column under a list gets an entry for every row, even when the list is
null or empty. Readers depend on this.

## Column buffers

Each leaf column has a typed buffer. Generated code calls it directly.

```csharp
public sealed class ColumnBuffer<TValue> where TValue : unmanaged
{
    public void Append(TValue value);                    // required, not in a list
    public void Append(TValue value, byte definition, byte repetition);
    public void AppendNull(byte definition, byte repetition);
}

public sealed class ByteArrayColumnBuffer                // strings and bytes
{
    public void Append(ReadOnlySpan<char> text, byte definition, byte repetition);
    public void Append(ReadOnlySpan<byte> bytes, byte definition, byte repetition);
    public void AppendNull(byte definition, byte repetition);
}
```

The buffers are sealed and typed so that appending a value involves no boxing
and no interface call. Strings are converted to UTF-8 directly into pooled
memory, without creating a byte array per string.

These types are public only because generated code in the user's assembly must
call them. They are kept small and hidden from editor completion lists.

## What the generator produces

For each registered type, the generator produces a class that describes the
schema and creates a shredder:

```csharp
public abstract class RowShredder<T>
{
    public abstract void Shred(in T row);
}
```

The generated shredder has one field per leaf column, holding that column's
buffer. Its `Shred` method is straight-line code: read a property, append it
with the right levels, move to the next. Level numbers are constants worked out
at build time. For a null or empty list, a generated helper appends the "no
value" entry to every column under that list.

The cost per row is one virtual call to `Shred`. Everything inside can be
inlined by the runtime.

## Registering types

A type is registered in one of two ways. Both produce the same code.

```csharp
[ParquetSerializable]
public partial class Order { /* ... */ }

[ParquetSerializable(typeof(ThirdPartyDto))]
public partial class MyParquetContext : ParquetSerializerContext { }
```

## Build errors

The generator reports these as errors:

- A type that contains itself, directly or through other types.
- A class with no writable properties.
- A `Guid`, `TimeOnly`, `Half`, or unsigned integer property with no chosen
  representation.
- A property type the library cannot map.
- Nesting deeper than 255 levels, which is the most a level can record in one
  byte.

## Runtime fallback

For a type the generator did not see, the library builds a shredder when the
writer is created, using compiled expression trees. It calls the same column
buffer methods as generated code. It is marked as requiring dynamic code, so
the compiler warns when it is used in a Native AOT or trimmed application.

The same checks apply, raised as exceptions when the writer is created.

## Keeping the two paths the same

The rules that turn a .NET type into a schema and assign level numbers are
written in one file. That file is compiled into both the generator and the
runtime library. Tests run every test type through both paths and require the
two files to be identical byte for byte.
