# File format writing

This page covers how pages, the footer, and the optional structures are
written.

## Thrift

Thrift is the serialization format that Parquet uses for its metadata. Page
headers and the footer are encoded with Thrift's compact protocol. The library
has its own small writer for this and does not depend on a Thrift package. It
writes only the structures Parquet uses.

## Pages

Each page is a header followed by the page's data.

| | Data page version 1 | Data page version 2 |
|---|---|---|
| Profile | Compatible | Modern |
| Levels | Compressed together with the values | Stored uncompressed, ahead of the values |
| Row boundaries | The format lets a page end in the middle of a row | A page always ends at the end of a row |

The library ends every page at the end of a row in both versions, because the
page index requires it.

The length of a page header is not known until the page has been compressed,
because the header records the compressed size. To avoid copying the page, the
column writer leaves room at the front of the buffer, compresses the page after
that gap, and then writes the header so that it ends exactly where the page
data begins.

## Statistics

For each column chunk the writer records the minimum value, maximum value, and
null count. Readers use these to skip data that cannot match a query.

A wrong statistic makes a reader skip rows it should return, and nothing
reports the error. The rules are therefore strict:

- The format has an older pair of fields, `min` and `max`, whose ordering was
  not defined for every type, and a newer pair, `min_value` and `max_value`,
  that replaced them. The library always writes the newer pair. It also
  writes the older pair for integer, floating-point, and boolean columns, and
  not for text or unsigned columns. That is what pyarrow does. Which other
  types pyarrow writes the older pair for will be checked when statistics are
  built. The footer states the ordering used for each column, which the
  format calls the column order.
- Text and bytes are compared as unsigned bytes.
- A decimal stored as fixed-length bytes is compared as a signed number, not
  as unsigned bytes. Compared as bytes, a negative value would sort above a
  positive one. The library writes both pairs of statistics fields for it, as
  pyarrow does.
- Where the right value is uncertain, the statistic is omitted.

Floating-point columns have rules of their own, taken from the format
definition as it stood on 2026-11-16:

- NaN values are left out of the minimum and maximum.
- A count of NaN values is always written, even when it is zero. pyarrow
  26.0.1 does not write this count yet.
- If every non-null value is NaN, no minimum or maximum is written.
- A minimum of zero is written as negative zero and a maximum of zero as
  positive zero, so that the range covers both.

The format defines a second ordering for floating-point columns, IEEE 754
total order, and recommends it over the original one. Older readers do not
know it. Which ordering each profile uses is an open question, listed in the
[architecture overview](README.md#open-questions).

Tests run filtered queries in Spark and DuckDB against files with these edge
cases and check that no rows are lost.

## Footer

The footer holds the schema, the row count, the list of row groups with the
position and size of each column chunk, and key-value metadata.

- `created_by` is written as `Parquetry version x.y.z (build <hash>)`. Readers
  built on the Java Parquet library parse this field to apply workarounds for
  known faults in particular writers. A value in this form parses, so the
  library is not treated as an unknown writer.
- Under the default profile, the key-value metadata includes
  `org.apache.spark.version`, so that Spark 3.x reads dates before 1582 and
  timestamps before 1900. An option turns this off. The exact value will be
  fixed when the feature is built.
- Users can add their own key-value metadata.
- pyarrow also writes Arrow's own schema into the key-value metadata, under
  the key `ARROW:schema`, and uses it to restore Arrow types when it reads the
  file. The first release of the library does not write this key. It may
  be added later. The reasons are in the decision record on
  [the Arrow schema](../adr/0037-arrow-schema-not-written-in-first-release.md).

## Page index

The page index has two parts for each column chunk: the minimum and maximum of
every page, and the position and first row number of every page. A reader uses
it to skip pages within a row group. It is written after the last row group and
before the footer.

Per-page statistics must be kept until the end of the file, so this data grows
with the file. It is counted against the memory budget. What happens when it
grows large is described in [Memory](memory.md). Long minimum and maximum
values are shortened to 64 bytes in the index, in a way that keeps them valid
as lower and upper bounds.

The index has no way to leave out the minimum and maximum of a single page.
With the original ordering, the format says that if every non-null value on
some page of a floating-point column is NaN, the writer must not write the
value part of the index for that column chunk at all. The writer follows this.

## Bloom filters

A bloom filter lets a reader rule out a column chunk when searching for one
specific value. It helps for columns with many distinct values, where a
dictionary cannot be used for the same purpose.

Bloom filters are off by default and turned on per column. The format allows a
filter to sit either after its row group or with the others at the end of the
file. The library writes each row group's filters directly after that row
group, so a filter holds memory only while its row group is open. The Parquet
format requires the xxHash64 function, which the library implements itself.

## Encryption

Parquet's modular encryption encrypts each part of a file separately with AES.
Different columns can use different keys, so a reader with one key can read
some columns and not others.

For an encrypted column, all of these are encrypted:

- Its data pages and dictionary page, and the header of each.
- Its entry in the footer, which holds its statistics.
- Its part of the page index.
- Its bloom filter.

The footer as a whole is either encrypted or left readable and signed. When it
is left readable, the statistics of encrypted columns are taken out of the
readable part and stored encrypted, so that minimum and maximum values do not
leak. A file with an encrypted footer starts and ends with the bytes `PARE`
where other files have `PAR1`.

Other points:

- The library supports both algorithms in the specification: AES-GCM for
  everything, or AES-GCM for metadata with AES-CTR for page data.
- AES-GCM comes from the .NET base class library. The base class library has
  no counter mode, so the library builds AES-CTR on top of its single-block
  AES.
- The format numbers row groups, columns, and pages with 16-bit signed values
  inside encrypted files. An encrypted file can therefore have at most 32,767
  row groups, and a column chunk at most 32,767 pages. The writer raises an
  error before it would exceed either. A small memory budget produces many
  small row groups, so the first limit can be reached in practice.
- The format limits one key to 2^32 AES-GCM operations. The writer counts
  them.
- Every encrypted part includes random values, so two encrypted files are
  never identical, even from the same input.
- The user supplies keys through an interface in core. Core does not include
  integrations with key management services.

A reader of an encrypted file must be configured with the keys. The design of
the key interface will be detailed when the feature is built.
