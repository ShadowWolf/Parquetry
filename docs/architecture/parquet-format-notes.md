# Parquet format notes

This page covers the parts of the Parquet format that shape the design. It is
not a full description of the format. The specification is at
<https://github.com/apache/parquet-format>.

## File structure

A Parquet file has this order:

```
"PAR1"                      4 bytes that mark the start
row group 1
  column chunk for column 1
    dictionary page (optional)
    data page, data page, ...
  column chunk for column 2
  ...
row group 2
...
page index (optional)
bloom filters (optional; may also sit elsewhere)
footer                      schema, row groups, positions of every column chunk
footer length               4 bytes
"PAR1"                      4 bytes that mark the end
```

A row group is a horizontal slice of the data: some number of rows. Inside a
row group, the data is stored one column at a time. The stored data for one
column in one row group is a column chunk. A column chunk is a series of pages.
A page holds a few thousand values and is the unit that gets encoded and
compressed.

Only leaf values are stored as columns. A nested object or a list has no column
of its own. Its structure is recorded through the levels described in
[Shredding and the source generator](shredding-and-source-generator.md).

## Two properties the design depends on

A column chunk must be one unbroken range of bytes. The footer records where
each chunk starts and how long it is, and a reader reads that range. A writer
cannot put a page of column A, then a page of column B, then another page of
column A.

The bytes of a page do not contain file positions. Each page begins with a
small header that gives its sizes and encoding. Positions appear only in the
footer and the page index, and those are written last. A writer can therefore
produce the bytes of a chunk before it knows where in the file the chunk will
be.

Together these mean that the writer may produce chunks in any order and in any
place, provided each chunk is contiguous in the final file and the footer
records the right positions. The layouts in
[Layouts and destinations](layouts-and-destinations.md) are built on this.

One ordering rule applies inside a chunk: the dictionary page, if there is one,
comes before the data pages. The dictionary is only complete when the chunk
ends, so a layout must be able to place a page first that was produced last.

## Storage service limits

These limits decide which layout suits which service. They should be checked
against current service documentation when the add-on packages are built.

| | Azure Block Blob | Amazon S3 multipart upload |
|---|---|---|
| Unit | Block | Part |
| Smallest unit | No minimum | 5 MiB, except the last part |
| Most units per object | 50,000 | 10,000 |
| Order of units | Set by a final call that lists the blocks | Set by the part number given at upload |
| Upload in any order | Yes | Yes, but each part's position is already fixed by its number |

Azure lets the writer upload a page as soon as it is finished and decide the
order at the end. S3 would need each column to gather at least 5 MiB before
uploading, which uses more memory than buffering a row group when a table has
many columns.

At the smallest part size, 10,000 parts limit an S3 object to about 49 GiB. The
S3 destination increases its part size as an upload grows to stay under the
part limit.

With Azure, one block per column per row group can exceed 50,000 blocks for a
table with many columns and many row groups. The staged layout therefore treats
a block as a range of bytes that may hold several small column chunks, and
makes blocks larger as the count rises.
