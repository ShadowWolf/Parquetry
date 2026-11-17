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

Take this type, in code with nullable annotations enabled:

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
required int64 Id;
optional group Lines (LIST) {
  repeated group list {
    required group element {
      optional binary Sku (STRING);
      required int32 Qty;
    }
  }
}
```

Columns take the names of their properties. The names `list` and `element` are
fixed by the Parquet format. The list itself is optional because `Lines` is
declared nullable. Its elements are required because `OrderLine` is not
declared nullable. The rules are in
[Schema and type mapping](schema-and-type-mapping.md).

There are three columns: `Id`, `Lines.list.element.Sku`, and
`Lines.list.element.Qty`. Each optional or repeated step on the path to a
column adds one to the highest definition level the column can have.

| Column | Highest definition level | What each level means |
|---|---|---|
| `Qty` | 2 | 1: the list is not null. 2: the list has an element. |
| `Sku` | 3 | As for `Qty`, then 3: the `Sku` is not null. |

The repetition level of both can reach 1, because they are inside one list.

| Row | `Lines` | Entries appended to the `Qty` column |
|---|---|---|
| 1 | Two lines, quantities 2 and 1 | value 2, definition 2, repetition 0; value 1, definition 2, repetition 1 |
| 2 | null | no value, definition 0, repetition 0 |
| 3 | empty list | no value, definition 1, repetition 0 |

Every column under a list gets an entry for every row, even when the list is
null or empty. Readers depend on this.

If the property were declared `List<OrderLine?>?`, the element would be
optional, and every level below it would be one higher.

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

A .NET string can hold text that is not valid, such as half of a two-unit
character. It cannot be converted to UTF-8 as it is. Whether the writer raises
an error or substitutes a replacement character is an open question, listed in
the [architecture overview](README.md#open-questions).

These types are public only because generated code in the user's assembly must
call them. They are kept small and hidden from editor completion lists.

## What the generator produces

For each registered type, the generator produces a class that describes the
schema and creates a shredder. Every generated shredder derives from this base
class, which is part of the library:

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

A type reached through a registered type, such as `OrderLine` through `Order`,
does not need its own registration. How a writer is created for each kind of
registration is shown in [Public API](public-api.md).

## Build errors

The generator reports these as errors:

- A type that contains itself, directly or through other types.
- A class with no properties that can be written to the file.
- A `Guid`, `TimeOnly`, `TimeSpan`, `Half`, `ushort`, `uint`, or `ulong`
  property with no chosen representation. `byte` is exempt.
- A `char`, `Int128`, `UInt128`, or `BigInteger` property. These types are not
  supported, and the message names the types to convert to.
- Any other property type the library cannot map.
- Nesting deeper than 255 levels, which is the most a level can record in one
  byte.

## Runtime fallback

For a type the generator did not see, the library builds a shredder when the
writer is created, using compiled expression trees. It calls the same column
buffer methods as generated code. It is marked as requiring dynamic code, so
the compiler warns when it is used in a Native AOT or trimmed application.

The same checks apply, raised as exceptions when the writer is created.

## Keeping the two paths the same

The generator and the runtime fallback see a type in different forms. The
generator sees the compiler's description of the source code. The fallback
sees the loaded type through reflection. Each one first converts what it sees
into the same plain description of the type: its properties, their types, and
which are nullable. The rules that turn that description into a schema and
assign level numbers are written once, in source code that is compiled into
both the generator and the runtime library.

The two conversions are separate code, and they are where the paths could
disagree, for example in how each reads nullable annotations. Tests therefore
run every test type through both paths and require the two Parquet files to be
identical byte for byte.
