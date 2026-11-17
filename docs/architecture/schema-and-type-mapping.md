# Schema and type mapping

The schema of a file is derived from the .NET type being written. This page
gives the mapping under the default profile and lists what is still undecided.

Parquet stores values in a small set of physical types, such as INT32 and
BYTE_ARRAY. A column can also carry a type annotation, which the format calls a
logical type. It tells readers how to interpret the stored values, for example
that an INT32 holds a date. The format has two generations of annotation: the
current logical types and the older converted types. Where an older converted
type exists for a column, the writer writes both, as the format requires, so
that old readers understand the file. For a time or a timestamp that is not
adjusted to UTC, the writer writes only the current annotation, as pyarrow
does.

## Simple types

| .NET type | Stored as | Parquet type annotation |
|---|---|---|
| `bool` | BOOLEAN | none |
| `sbyte` | INT32 | 8-bit signed integer |
| `byte` | INT32 | 8-bit unsigned integer |
| `short` | INT32 | 16-bit signed integer |
| `int` | INT32 | none |
| `long` | INT64 | none |
| `float` | FLOAT | none |
| `double` | DOUBLE | none |
| `decimal` | Fixed-length bytes, in the smallest width that holds the precision | DECIMAL |
| `string` | BYTE_ARRAY | STRING |
| `byte[]`, `ReadOnlyMemory<byte>` | BYTE_ARRAY | none |
| `DateOnly` | INT32 | DATE |
| `DateTime`, `DateTimeOffset` | INT64 | TIMESTAMP, microseconds, adjusted to UTC |
| An `enum` | The same as its underlying integer type. INT32 for most enums. | The same as its underlying integer type |

`byte` is unsigned in .NET, and its column carries an unsigned 8-bit
annotation, as in pyarrow. Spark reads such a column as a 16-bit integer, but
does not use its statistics to skip data when a query filters on it. Spark
does use the statistics of a signed 16-bit column, so a user who needs fast
filters in Spark can declare the property as `short`. This is the only
unsigned annotation the default profile writes without being asked. The other
unsigned types need an explicit choice, as described below.

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
definition levels. A definition level is a small number stored with each value
of an optional column to record nulls. It is explained in
[Shredding and the source generator](shredding-and-source-generator.md).

### Decimal

The default is precision 38 and scale 18. It can be set per writer and per
property. A decimal is stored as fixed-length bytes, in the smallest width
that holds the column's precision. These are the widths pyarrow uses:

| Precision | Bytes |
|---|---|
| 1 to 2 | 1 |
| 3 to 4 | 2 |
| 5 to 6 | 3 |
| 7 to 9 | 4 |
| 10 to 11 | 5 |
| 12 to 14 | 6 |
| 15 to 16 | 7 |
| 17 to 18 | 8 |
| 19 to 21 | 9 |
| 22 to 23 | 10 |
| 24 to 26 | 11 |
| 27 to 28 | 12 |
| 29 to 31 | 13 |
| 32 to 33 | 14 |
| 34 to 35 | 15 |
| 36 to 38 | 16 |

An option, for the writer or for one column, stores decimals of 9 digits or
fewer as INT32 and of 10 to 18 digits as INT64 instead. Spark 3.3 to 4.1 read
pyarrow-written files in both forms correctly at every precision. The test,
and how the two forms compare in size, are described in the decision record
[decimals are stored as fixed-length bytes](../adr/0036-decimal-storage.md).

A value that cannot be stored exactly raises an error naming the column. The
library does not round. The precision can be set from 1 to 38. Spark and
Delta Lake, the table format Databricks uses, support no more than 38, and a
.NET `decimal` never has more than 29 digits.

### DateTime

| Value | Result |
|---|---|
| `DateTime` with `Kind` of `Utc` | Written as is. |
| `DateTime` with `Kind` of `Local` | Converted to UTC. |
| `DateTime` with `Kind` of `Unspecified` | Error naming the column, unless a writer option says to treat it as UTC or as local. |
| `DateTimeOffset` | Converted to UTC. The offset is not stored. |

A column can also be set to store timestamps without a time zone. Under the
default profile that setting produces a compatibility message, because Spark
3.3 reads such a column as a point in time and a Delta table needs a feature
enabled to hold it. A compatibility message is a finding reported when the
writer is created. It says that the file can be written but that a reader the
profile is meant for cannot read it. It is described in
[Options and profiles](options-and-profiles.md).

Values are stored in microseconds. .NET keeps one more digit, in units of 100
nanoseconds, and most real values have it: `DateTime.UtcNow` does, and so do
values from SQL Server's `datetime2` type.

| Value | Result |
|---|---|
| The 100-nanosecond digit is zero | Written exactly. |
| The digit is not zero | Error naming the column and the option that allows truncation. |
| The digit is not zero and truncation is allowed | The digit is dropped without an error. |

Truncation is allowed by a writer option, which can also be set per column.
This matches what pyarrow does when it is asked to write microseconds: it
raises an error unless `allow_truncated_timestamps` is set. By default pyarrow
does not convert at all. It writes the unit the data has, so data in
nanoseconds stays in nanoseconds. That loses nothing, but Spark, in the
versions checked, cannot read it.

When the digit is dropped, the value moves toward 1970-01-01 00:00:00 UTC,
which is also what pyarrow does. A value in 1970 or later moves earlier. A
value before 1970 moves later, and can move into the next second:
1969-12-31 23:59:59.9999999 becomes 1970-01-01 00:00:00. The change is always
less than one microsecond.

A column can be set to nanoseconds. The `Modern` profile allows this. Under
the default profile it produces a compatibility message. Nanoseconds hold
every digit of a .NET value, but a 64-bit count of them covers only the
years 1677 to 2262. A value outside that range raises an error naming the
column. `default(DateTime)`, which is in the year 1, is such a value.

### Enum

An enum is written as its number, stored the way its underlying type is
stored. An option, per property or per enum type, writes the name as text
instead.

A reader of the number has no record of what it means, and renumbering the
enum's members changes the meaning of files already written. Text avoids both
problems and costs little extra space, because dictionary encoding stores each
distinct name once.

An enum whose underlying type is `ushort`, `uint`, or `ulong` needs an
explicit choice, as those types do. An enum whose underlying type is `byte` is
stored as a `byte` is.

## Types that need an explicit choice

A property of one of these types fails the build unless the user chooses how to
store it. The reason differs by type. In the versions checked, Spark cannot
read the natural Parquet type for `Guid`, `TimeOnly`, and `Half`. The versions
and the details are in
[Spark and Databricks compatibility](spark-and-databricks-compatibility.md).
Spark reads unsigned integers as a wider signed type, and Delta tables have no
unsigned types. Parquet has no type for a length of time that the verified
readers accept.

| .NET type | Choices |
|---|---|
| `Guid` | Text (36 characters). 16 fixed-length bytes with the UUID annotation. 16 fixed-length bytes with no annotation. |
| `TimeOnly` | TIME in microseconds, marked as not adjusted to UTC, as pyarrow writes it. A 64-bit count of microseconds since midnight with no annotation. Text. |
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

`TimeOnly` also has a 100-nanosecond digit, so its two microsecond forms
follow the same rule. A truncated value moves toward midnight.

Both 16-byte forms of a `Guid` use the byte order that the UUID annotation
requires, which is the order of the digits in the text form. That differs from
what `Guid.ToByteArray()` returns by default, where the first three parts are
reversed.

The choice is checked against the profile when the writer is created. Under the
default profile, choosing UUID, TIME, FLOAT16, an unsigned annotation, or 16
bytes with no annotation produces a compatibility message. The last is on the
list because Spark 3.3 cannot read fixed-length bytes without an annotation.
The attribute names for making these choices
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
<optional or required> group <property name> (LIST) {
  repeated group list {
    <optional or required> <element type> element;
  }
}
```

The outer group is optional when the property is nullable, and the element is
optional when the element type is nullable, by the rules in "Required and
optional columns" above. A worked example is in
[Shredding and the source generator](shredding-and-source-generator.md).

This three-level form is the one the format specifies. Older writers produced
shorter two-level forms, which readers do not all interpret the same way. The
library never writes those.

A class with no properties that can be written to the file is rejected. It
would become an empty group, which the Java Parquet library and the readers
built on it do not accept. A type that contains itself is not supported. Both
are reported at build time.

## Column names

A column takes the name of its property. An attribute or a naming policy can
change it. Under the default profile, a compatibility message reports names
that contain a space or any of `,;{}()=`, a tab, or a newline, and names that
differ only by letter case. Spark reads the first kind, but a Delta table
rejects them unless its column mapping feature is turned on.

## Not yet decided

| Question | Notes |
|---|---|
| How does a user leave a property out of the file? | Needed for properties of unsupported types. |
| Can a user supply their own conversion for a type? | It would let the unsupported types be handled once per type and not once per property. |

Smaller points, such as attribute names and which collection types are
written, are in the full list of open questions in the
[architecture overview](README.md#open-questions).
