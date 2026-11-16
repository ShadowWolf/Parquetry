# pyarrow parity

pyarrow is the Python library of the Apache Arrow project. Its Parquet writer
is the reference for this library: Parquetry writes what pyarrow writes by
default, unless there is a recorded reason not to. This page compares what the
documents say Parquetry will write with what pyarrow writes.

The terms used here, such as page index, annotation, and profile, are explained
in the [architecture overview](README.md#terms),
[Parquet format notes](parquet-format-notes.md), and
[Schema and type mapping](schema-and-type-mapping.md).

## How the comparison was made

pyarrow 26.0.1 was run, on 2026-11-16 for the main program and on 2026-11-14
for the timestamp program. Each row below comes from one of these sources:

| Source | What it covers |
|---|---|
| `docs/research/pyarrow-parity/probe.py` | Every row not listed in the entries below. Its output is saved beside it as `output.txt`, so a row can be checked without running anything. |
| `docs/research/pyarrow-timestamp-probe.py` | The two rows about timestamps that lose digits. |
| `docs/research/parquet-net-probe` | The two statements about what Parquet.Net writes. |
| [Spark and Databricks compatibility](spark-and-databricks-compatibility.md) | Every statement about Spark or Delta. Those come from reading Spark's source and have not been tested by this project. |

No Parquetry file exists yet, so pyarrow has not read one. What the comparison
shows is narrower. Under the default profile, each way the documents say
Parquetry stores a type or lays out nested data is one that pyarrow itself
writes, by default or with an option, and reads back. The last section of the
program's output shows the read-back for the forms that are not pyarrow's
default. That section also has two forms the library no longer writes by
default, a decimal as INT32 and a `byte` with a signed annotation, from before
those two decisions were changed to match pyarrow. Two things Parquetry writes are things pyarrow does not write at all:
a count of NaN values, and shortened values in the page index. Both are in the
table of deliberate differences. The `Modern` profile has not been compared.
The reader tests will confirm all of this with real files.

## Which Arrow type each .NET type is compared with

pyarrow writes Arrow data, so a comparison needs an Arrow type for each .NET
type.

| .NET type | Arrow type | Notes |
|---|---|---|
| `bool`, `float`, `double`, `string`, `byte[]` | `bool_`, `float32`, `float64`, `string`, `binary` | |
| `sbyte`, `short`, `int`, `long` | `int8`, `int16`, `int32`, `int64` | |
| `byte`, `ushort`, `uint`, `ulong` | `uint8`, `uint16`, `uint32`, `uint64` | |
| `Half` | `float16` | |
| `decimal` | `decimal128` with the column's precision and scale | |
| `DateOnly` | `date32` | |
| `DateTime`, `DateTimeOffset` | `timestamp` in microseconds with a time zone | Arrow has no unit of 100 nanoseconds. Microseconds is the unit Parquetry stores. The nearest unit that loses nothing is nanoseconds. |
| `TimeOnly` | `time64` in microseconds | The same point about units applies. |
| `TimeSpan` | `duration` in microseconds | The same point about units applies. |
| `Guid` | `uuid` | |
| An `enum` | None. The nearest is a dictionary of text. | |
| `List<T>`, `Dictionary<K, V>`, a class | `list_`, `map_`, `struct` | |

## Where the library matches pyarrow

| Subject | What pyarrow does | Parquetry |
|---|---|---|
| Data page version | Writes version 1. | The same, under the default profile, `Compatible`. |
| Encodings | PLAIN and dictionary. A BOOLEAN column is not dictionary-encoded. | The same, under the default profile. |
| Compression | Snappy. | The same, under the default profile. |
| INT96 timestamps | Not written. | The same. |
| Signed integers | 8-bit and 16-bit values as INT32 with a signed annotation of that width. 32-bit as INT32. 64-bit as INT64. | The same. |
| `byte` | INT32 with an unsigned 8-bit annotation. | The same. |
| Decimals | Fixed-length bytes, in the smallest width that holds the precision: 1 byte for 1 or 2 digits, 4 bytes for 7 to 9, 8 bytes for 17 or 18, 16 bytes for 36 to 38. INT32 and INT64 are used for 18 digits or fewer only when `store_decimal_as_integer` is set. | The same, with the same option. |
| `float`, `double`, `bool` | FLOAT, DOUBLE, BOOLEAN. | The same. |
| Text | BYTE_ARRAY with the STRING annotation and the older UTF8 annotation. | The same. |
| Bytes | BYTE_ARRAY with no annotation. | The same. |
| Dates | INT32 with the DATE annotation. | The same. |
| A timestamp in microseconds with a time zone | INT64 with the TIMESTAMP annotation, microseconds, adjusted to UTC. A value with another offset is converted to UTC, and the offset is not kept in the Parquet schema. | The same for `DateTime` of kind `Utc` or `Local`, and for `DateTimeOffset`. |
| A timestamp that would lose digits when converted to microseconds | When asked to convert, pyarrow raises an error unless `allow_truncated_timestamps` is set. | The same: an error unless the truncation option is set. |
| Direction of that truncation, when it is allowed | Toward 1970. | The same. |
| A timestamp outside the range nanoseconds can hold | An error when the nanosecond value is built. | An error, for a column set to nanoseconds. |
| A decimal value that does not fit the column's precision and scale | An error when the value is built or cast with checking on. | An error. |
| A non-nullable field | A required column. Writing a null into it is an error. | The same. |
| Lists | Three levels, with the inner names `list` and `element`. The element is required when its type is not nullable. | The same. |
| Maps | A repeated `key_value` group with a required key. | The same. |
| A struct with no fields | An error. | The same, reported when the project is built. |
| Minimum and maximum of a floating-point column | NaN is left out. If every value is NaN, neither is written. A zero minimum is written as negative zero and a zero maximum as positive zero. | The same. |
| Older `min` and `max` statistics fields | Written beside the newer `min_value` and `max_value` for the 64-bit integer, double, and boolean columns that were tested. Not written for the text column or the unsigned 8-bit column. | The same for those types. Other types will be checked when statistics are built. |
| Page index for a column chunk in which one page holds only NaN | With the page index turned on, the value ranges for that chunk are left out and the page positions are written. | The same. |
| Bloom filters | Off. | The same. |
| Column names with spaces or punctuation, or that differ only by case | Written as given. | Written as given. Under the default profile the writer also reports a compatibility message, a notice raised when the writer is created. A Delta table rejects names with spaces or punctuation, and Spark fails on a query when two names differ only by case. |
| TIME | Marked as not adjusted to UTC. | The same, when the user chooses TIME for a `TimeOnly`. |

## Where a choice in Parquetry produces what pyarrow writes

For these types the library makes the user choose a representation, and the
build fails until they do. One of the choices is pyarrow's form for the Arrow
type in the table above.

| .NET type | What pyarrow writes | The matching choice | Why the user must choose |
|---|---|---|---|
| `Guid` | 16 fixed-length bytes with the UUID annotation, in the order of the digits in the text form. | 16 bytes with the UUID annotation, in the same byte order. | Spark cannot read UUID. |
| `Half` | 2 fixed-length bytes with the FLOAT16 annotation. | FLOAT16. | Spark cannot read FLOAT16. |
| `ushort`, `uint`, `ulong` | INT32 or INT64 with an unsigned annotation. | The unsigned annotation. | Spark reads these as a wider signed type, and Delta tables have no unsigned types. |
| `TimeOnly` | INT64 with the TIME annotation, microseconds. | TIME in microseconds. | Spark 3.x and 4.0 cannot read TIME. |
| `TimeSpan` | INT64 with no annotation, holding a count of microseconds. | A 64-bit count of microseconds. | Parquet has no type for a length of time that the verified readers accept, so a reader sees a plain number and the user should choose its unit. |

## Differences that are deliberate

| Subject | pyarrow | Parquetry | Reason |
|---|---|---|---|
| A timestamp with digits below a microsecond | pyarrow keeps the unit the data has, apart from writing seconds as milliseconds. Data in nanoseconds is written as nanoseconds, and nothing is lost. | Microseconds, unless a column is set to nanoseconds. A .NET value with a non-zero 100-nanosecond digit therefore raises an error unless truncation is allowed. | Spark, in the versions checked, cannot read nanosecond timestamps. |
| A date and time with no time zone | Written as a timestamp that is not adjusted to UTC, with no error. | A `DateTime` of kind `Unspecified` raises an error unless the user sets a policy for such values. | Spark 3.3 reads such a column as a point in time, and a Delta table needs a feature enabled to hold one. pyarrow's form can be chosen per column. |
| Page index | Off unless asked for. | On. | Readers that do not use it ignore it, and it lets readers skip pages. |
| Long values in the page index | Written whole. A 206-byte value is stored as 206 bytes. | Shortened to 64 bytes. | The page index is kept in memory until the file is complete, so its size has to be limited. |
| Count of NaN values in statistics | Not written. | Written for floating-point columns. | The current format definition requires it. pyarrow 26.0.1 has not adopted it. Readers that do not know the field skip it. |
| The types in the previous section | Written with no choice needed. | A build error until the user chooses. | Given per type in that section. |
| Enums | Arrow has no enum type. Its nearest type, a dictionary of text, is written as text. | The number by default, with text as an option. | The number is what Parquet.Net writes, which was checked by running it, and what `System.Text.Json` writes by default. |
| Spark version key in the file's metadata | Not written. | Written under the default profile. | It lets Spark 3.x read dates before 1582. pyarrow reads a file that has the key with no change in the values. |
| `created_by` | `parquet-cpp-arrow version 26.0.1` | `Parquetry version x.y.z (build <hash>)` | Each writer names itself. |

## Differences still to be decided

This is for the project owner.

| Subject | pyarrow | Parquetry as documented | Notes |
|---|---|---|---|
| Arrow schema in the file's metadata | Written under the key `ARROW:schema`. pyarrow uses it on read to restore Arrow types that Parquet cannot express. | Not written. | Without it, pyarrow reads a `TimeSpan` count as a plain 64-bit integer and an enum written as text as plain text. Every other type the library writes comes back the same either way. Writing it means producing Arrow's serialized schema format, and it makes the footer larger: for a file with 500 columns, pyarrow's footer was 94 KB with it and 60 KB without. |

## Points not yet settled in Parquetry

For these, pyarrow's behavior is the starting point.

| Subject | pyarrow | Notes |
|---|---|---|
| Text that is not valid UTF-8 | Converting such bytes to a string raises an error. The Parquet writer itself does not check: a string array built without that check is written as it is. | The open question is whether Parquetry raises an error or replaces the invalid part. pyarrow's checked path raises an error. |
| Version number in the footer | The footer's version field is 2. pyarrow's API calls this format version 2.6. | To be settled when the footer is built. |
| Rows in a row group | At most 1,048,576. A write of 2,500,000 rows gave row groups of 1,048,576, 1,048,576, and 402,848 rows. | The defaults will be set from benchmarks. |
| Size of a page | At most 20,000 rows. Pages of 8-byte values came out at 160 KB. Pages of 1,000-byte strings came out at about 2 MB. | The defaults will be set from benchmarks. |
