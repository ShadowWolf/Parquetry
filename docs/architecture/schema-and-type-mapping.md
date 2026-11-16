# Schema and type mapping

The schema of a file is derived from the .NET type being written. This page
gives the mapping under the default profile and lists what is still undecided.

## Simple types

| .NET type | Stored as | Parquet type annotation |
|---|---|---|
| `bool` | BOOLEAN | none |
| `sbyte` | INT32 | 8-bit signed integer |
| `byte` | INT32 | 16-bit signed integer |
| `short` | INT32 | 16-bit signed integer |
| `int` | INT32 | none |
| `long` | INT64 | none |
| `float` | FLOAT | none |
| `double` | DOUBLE | none |
| `decimal` | INT32, INT64, or fixed-length bytes, by precision | DECIMAL |
| `string` | BYTE_ARRAY | STRING |
| `byte[]`, `ReadOnlyMemory<byte>` | BYTE_ARRAY | none |
| `DateOnly` | INT32 | DATE |
| `DateTime`, `DateTimeOffset` | INT64 | TIMESTAMP, microseconds, adjusted to UTC |
| An `enum` | The same as its underlying integer type. INT32 for most enums. | The same as its underlying integer type |

`byte` is unsigned in .NET. The default profile does not write unsigned
annotations, so a `byte` column is annotated as a 16-bit signed integer, which
holds every `byte` value. The other unsigned types need an explicit choice, as
described below.

### Required and optional columns

A Parquet column is either required, meaning it has a value in every row, or
optional, meaning it may be null.

| .NET declaration | Column |
|---|---|
| A value type, such as `int` | Required |
| `Nullable<T>`, such as `int?` | Optional |
| A reference type declared nullable, such as `string?` | Optional |
| A reference type declared non-nullable, such as `string`, in code with nullable annotations enabled | Required |
| A reference type in code without nullable annotations | Optional |

The same applies to the elements of a list and the values of a map:
`List<string>` has required elements and `List<string?>` has optional ones.

.NET does not enforce nullable annotations at run time, so a property declared
as `string` can still hold null. If the writer finds a null in a required
column, it raises an error that names the column.

Required columns are smaller and faster to write, because they store no
definition levels.

### Decimal

The default is precision 38 and scale 18. It can be set per writer and per
property. Storage depends on precision: up to 9 digits uses INT32, up to 18
uses INT64, and more uses fixed-length bytes (16 bytes for precision 38). A
value that cannot be stored exactly raises an error naming the column. The
library does not round. Precision above 38 is rejected under the default
profile because Spark and Delta do not support it.

### DateTime

| Value | Result |
|---|---|
| `DateTime` with `Kind` of `Utc` | Written as is. |
| `DateTime` with `Kind` of `Local` | Converted to UTC. |
| `DateTime` with `Kind` of `Unspecified` | Error naming the column, unless a writer option says to treat it as UTC or as local. |
| `DateTimeOffset` | Converted to UTC. The offset is not stored. |

Values are stored in microseconds. .NET keeps one more digit, in units of 100
nanoseconds, and most real values have it: `DateTime.UtcNow` does, and so do
values from SQL Server's `datetime2` type.

| Value | Result |
|---|---|
| The 100-nanosecond digit is zero | Written exactly. |
| The digit is not zero | Error naming the column and the option that allows truncation. |
| The digit is not zero and truncation is allowed | The digit is dropped without an error. |

Truncation is allowed by a writer option, which can also be set per column.
pyarrow behaves the same way: it raises an error unless
`allow_truncated_timestamps` is set.

When the digit is dropped, the value moves toward 1970-01-01 00:00:00 UTC,
which is also what pyarrow does. A value in 1970 or later moves earlier. A
value before 1970 moves later, and can move into the next second:
1969-12-31 23:59:59.9999999 becomes 1970-01-01 00:00:00. The change is always
less than one microsecond.

### Enum

An enum is written as its number, stored the way its underlying type is
stored. An option, per property or per enum type, writes the name as text
instead.

A reader of the number has no record of what it means, and renumbering the
enum's members changes the meaning of files already written. Text avoids both
problems and costs little extra space, because dictionary encoding stores each
distinct name once.

An enum whose underlying type is `ushort`, `uint`, or `ulong` needs an
explicit choice, as those types do.

## Types that need an explicit choice

A property of one of these types fails the build unless the user chooses how to
store it. For each, either the natural Parquet type is one Spark cannot read,
or Parquet has no matching type.

| .NET type | Choices |
|---|---|
| `Guid` | Text (36 characters). 16 bytes with the UUID annotation. 16 bytes with no annotation. |
| `TimeOnly` | TIME in microseconds. A 64-bit count of microseconds since midnight with no annotation. Text. |
| `Half` | FLOAT, which holds every `Half` value exactly. FLOAT16. |
| `ushort`, `uint`, `ulong` | The next wider signed type (`ulong` becomes a 20-digit decimal). The unsigned annotation. |
| `TimeSpan` | A 64-bit count of microseconds. A 64-bit count of ticks (units of 100 nanoseconds), which keeps every value exactly. Text. |

`TimeSpan` is a length of time. Parquet's TIME type means a time of day, so it
cannot hold a negative value or one of 24 hours or more, and Parquet's
INTERVAL type is not supported by Spark. The integer choices carry no unit in
the file, so the column name should say which unit it holds. A count of
microseconds follows the same rule as timestamps: a value with a non-zero
100-nanosecond digit raises an error unless truncation is allowed, and a
truncated value moves toward zero.

The choice is checked against the profile when the writer is created. Under the
default profile, choosing UUID, TIME, FLOAT16, or an unsigned annotation
produces a validation message. The attribute names for making these choices
will be settled when the feature is built.

## Types that are not supported

A property of type `char`, `Int128`, `UInt128`, or `BigInteger` fails the
build. None of them has a clear Parquet form, and the right substitute depends
on the data. Convert the value to one of the types below in your own code.

### char

| Convert to | What readers see | Tradeoffs |
|---|---|---|
| `string` | Text of one character | Easy to read and query. A `char` that is half of a two-unit character, such as part of an emoji, is not valid text on its own. |
| `int` | The character's code as a number | Holds every `char` value. Readers must convert the number back to see the character. |

### Int128 and UInt128

| Convert to | What readers see | Tradeoffs |
|---|---|---|
| `decimal` with scale 0 | A number | Readers can sort, compare, and do arithmetic. A .NET `decimal` holds about 28 digits, and these types hold up to 39, so large values do not fit. |
| `string` | Text | Holds every value. Readers must convert it to a number, and sorting and filtering compare it as text. |
| `byte[]` | 16 raw bytes | The smallest form. Readers cannot use the value without code that knows the byte order. |

### BigInteger

The alternatives are the same as for `Int128`. A `BigInteger` has no size
limit, so `decimal` works only when the values are known to fit, and the
`byte[]` form varies in length.

## Nested types

| .NET type | Parquet structure |
|---|---|
| A class or struct with properties | A group with one field per property. |
| `T[]`, `List<T>`, and other collections | A list in the standard three-level layout. |
| `Dictionary<TKey, TValue>` | A map: a repeated `key_value` group with a required key. |

A list is written as:

```
optional group lines (LIST) {
  repeated group list {
    optional <element type> element;
  }
}
```

A class with no writable properties cannot be written, because Parquet does not
allow an empty group. A type that contains itself is not supported. Both are
reported at build time.

## Column names

A column takes the name of its property. An attribute or a naming policy can
change it. Under the default profile, validation reports names that contain a
space or any of `,;{}()=`, a tab, or a newline, and names that differ only by
letter case.

## Not yet decided

| Question | Notes |
|---|---|
| How does a user leave a property out of the file? | Needed for properties of unsupported types. |
| Can a user supply their own conversion for a type? | It would let the unsupported types be handled once per type and not once per property. |
