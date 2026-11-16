# pyarrow parity

The library aims to write what pyarrow writes by default, wherever that is
possible. This page compares each decision made so far with pyarrow.

The comparison was made on 2026-11-16 by running pyarrow 26.0.1. The program
is `docs/research/pyarrow-parity-probe.py`. Where a row below comes from
pyarrow's documentation and not from the run, it says so.

No decision made so far produces a file that pyarrow cannot read. Two defaults
differ from pyarrow without a recorded reason, and they are listed under
[Differences still to be decided](#differences-still-to-be-decided).

## Where the library matches pyarrow

| Subject | What pyarrow writes by default | Parquetry |
|---|---|---|
| Data page version | 1 | The same, under the default profile. |
| Encodings | PLAIN and dictionary | The same, under the default profile. |
| Compression | Snappy | The same. |
| INT96 timestamps | Not written | The same. |
| Signed integers | 8-bit and 16-bit values as INT32 with a signed annotation of that width. 32-bit as INT32. 64-bit as INT64. | The same for `sbyte`, `short`, `int`, and `long`. |
| `float`, `double`, `bool` | FLOAT, DOUBLE, BOOLEAN | The same. |
| Text | BYTE_ARRAY with the STRING annotation and the older UTF8 annotation | The same. |
| Bytes | BYTE_ARRAY with no annotation | The same. |
| Dates | INT32 with the DATE annotation | The same for `DateOnly`. |
| Timestamps with a time zone | INT64, microseconds, adjusted to UTC. A value with another offset is converted to UTC, and the offset is not kept in the Parquet schema. | The same for `DateTime` of kind `Utc` or `Local`, and for `DateTimeOffset`. |
| A timestamp that loses digits when written as microseconds | An error, unless truncation is allowed | The same. |
| Direction of truncation | Toward 1970 | The same. |
| A date outside what nanoseconds can hold | An error | The same. |
| A decimal that does not fit its precision and scale | An error | The same. |
| A non-nullable field | A required column. A null in it is an error. | The same. |
| Lists | Three levels, with the inner names `list` and `element`. The element is required when its type is not nullable. | The same. |
| Maps | A repeated `key_value` group with a required key | The same. |
| A struct with no fields | An error | The same, as a build error. |
| Floating-point statistics | NaN is left out of the minimum and maximum. If every value is NaN, no minimum or maximum is written. A zero minimum is written as negative zero and a zero maximum as positive zero. | The same. |
| Page index for a column chunk with an all-NaN page | The value ranges are left out and the page positions are written | The same. |
| Bloom filters | Off | The same. |
| Column names with spaces or punctuation, or that differ only by case | Written as given | Written as given, with a compatibility message under the default profile. |

## Where a choice in Parquetry produces what pyarrow writes

For these types the library makes the user choose a representation, because
Spark cannot read what pyarrow writes or reads it as a different type. One of
the choices is always pyarrow's form.

| .NET type | What pyarrow writes for its matching type | The matching choice |
|---|---|---|
| `Guid` | 16 fixed-length bytes with the UUID annotation, in the order of the digits in the text form | 16 bytes with the UUID annotation |
| `Half` | 2 fixed-length bytes with the FLOAT16 annotation | FLOAT16 |
| `ushort`, `uint`, `ulong` | INT32 or INT64 with an unsigned annotation | The unsigned annotation |
| `TimeOnly` | TIME in the value's unit, marked as not adjusted to UTC | TIME in microseconds. The library marks it as not adjusted to UTC, to match. |
| `TimeSpan` | INT64 with no annotation, holding a count in the value's unit | A 64-bit count of microseconds |

## Differences that are deliberate

| Subject | pyarrow | Parquetry | Reason |
|---|---|---|---|
| A date and time with no time zone | Written as a timestamp that is not adjusted to UTC, with no error | A `DateTime` of kind `Unspecified` raises an error unless a policy is set | Spark 3.3 reads such a column as a point in time, and a Delta table needs a feature enabled to hold one. pyarrow's form is available as a column setting. |
| Page index | Off unless asked for | On | Readers that do not use it ignore it, and it lets readers skip pages. |
| Types in the table above | Written with no choice needed | A build error until the user chooses | Spark cannot read the result, or reads it as a different type. |
| Enums | Arrow has no enum type. Its nearest type, a dictionary of text, is written as text. | The number by default, with text as an option | The number is what Parquet.Net and `System.Text.Json` write. |
| Arrow schema in the file's metadata | Written under the key `ARROW:schema` | Not written | It is specific to Arrow. Without it, pyarrow reads a `TimeSpan` count as a plain 64-bit integer. |
| Spark version key in the file's metadata | Not written | Written under the default profile | It lets Spark 3.x read old dates. pyarrow ignores it. |

## Differences still to be decided

| Subject | pyarrow | Parquetry as documented | Notes |
|---|---|---|---|
| `byte` | INT32 with an unsigned 8-bit annotation | INT32 with a signed 16-bit annotation | Parquet.Net and ParquetSharp also write the unsigned 8-bit annotation. Spark 3.2 and later reads it as a 16-bit integer, which is what the signed form gives too. |
| Small decimals | Fixed-length bytes at every precision: 4 bytes up to 9 digits, 8 up to 18, 16 up to 38. Integers are used only when `store_decimal_as_integer` is set. | INT32 up to 9 digits and INT64 up to 18 | Both forms are valid, and Spark reads both. |
| Text that is not valid | Python refuses to build such a string, so nothing is written | Open: raise an error or replace the invalid part | pyarrow's behavior points to raising an error. |
| Format version recorded in the footer | pyarrow reports 2.6 for its files | Not yet stated | To be settled when the footer is built. |
| Default sizes | From pyarrow's documentation: row groups of up to 1,048,576 rows, data pages of 1 MB, and a dictionary page limit of 1 MB | Not yet set | These are the starting point for the benchmarks that will set the defaults. |
