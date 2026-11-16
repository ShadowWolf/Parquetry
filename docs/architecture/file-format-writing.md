# File format writing

This page covers how pages, the footer, and the optional structures are
written.

## Thrift

Page headers and the footer are encoded with Thrift's compact protocol. The
library has its own small writer for this and does not depend on a Thrift
package. It writes only the structures Parquet uses.

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

- Statistics are written in the current `min_value` and `max_value` fields, and
  the footer states the sort order used for each column.
- Text and bytes are compared as unsigned bytes.
- For floating-point columns, NaN values are left out of the minimum and
  maximum, and zero is handled so that both positive and negative zero are
  covered.
- Where the right value is uncertain, the statistic is omitted.

Tests run filtered queries in Spark and DuckDB against files with these edge
cases and check that no rows are lost.

## Footer

The footer holds the schema, the row count, the list of row groups with the
position and size of each column chunk, and key-value metadata.

- `created_by` is written as `Parquetry version x.y.z (build <hash>)`. The
  Java Parquet library parses this field, and this form parses cleanly.
- Under the default profile, the key-value metadata includes
  `org.apache.spark.version`, so that Spark 3.x reads dates before 1582 and
  timestamps before 1900. An option turns this off. The exact value will be
  fixed when the feature is built.
- Users can add their own key-value metadata.

## Page index

The page index has two parts for each column chunk: the minimum and maximum of
every page, and the position and first row number of every page. A reader uses
it to skip pages within a row group. It is written after the last row group and
before the footer.

Per-page statistics must be kept until the end of the file, so this data grows
with the file. It is counted against the memory budget. Long minimum and
maximum values are shortened to 64 bytes in the index, in a way that keeps them
valid as lower and upper bounds.

## Bloom filters

A bloom filter lets a reader rule out a column chunk when searching for one
specific value. It helps for columns with many distinct values, where a
dictionary cannot be used for the same purpose.

Bloom filters are off by default and turned on per column. Each one holds
memory while its row group is open. The Parquet format requires the xxHash64
function, which the library implements itself.

## Encryption

Parquet's modular encryption encrypts pages and, optionally, the footer with
AES. Different columns can use different keys, so a reader with one key can
read some columns and not others.

- The library supports both algorithms in the specification: AES-GCM for
  everything, or AES-GCM for metadata with AES-CTR for page data.
- The footer can be encrypted, or left readable and signed.
- The user supplies keys through an interface in core. Core does not include
  integrations with key management services.
- AES comes from the .NET base class library.

A reader of an encrypted file must be configured with the keys. The design of
the key interface will be detailed when the feature is built.
