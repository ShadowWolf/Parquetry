# How rows become column chunks is a pluggable strategy

Status: accepted
Date: 2026-11-14

## Context

Applications produce data one row at a time. A Parquet file stores data one
column at a time: within a row group, all values of the first column come
first, then all values of the second, and so on. Each of these runs is called a
column chunk.

Two properties of the format decide what a writer can do:

1. A column chunk must be one unbroken range of bytes in the file. Readers find
   it by a start position and a length. Pages from different columns cannot be
   mixed together as they fill up.
2. The bytes of a column chunk do not depend on where it sits in the file.
   Positions are recorded only in the footer and the page index, which are
   written last. A writer can therefore produce chunk bytes in any order and
   decide the final arrangement at the end.

Because of the first property, most writers hold a whole row group in memory
before writing it. Because of the second, other arrangements are possible.

## Options considered

| Option | Memory held | Notes |
|---|---|---|
| Buffer the row group in memory as encoded, compressed pages | About one compressed row group | Works with any destination that accepts bytes in order. |
| Send each column's pages to storage as they complete, and set the order when the file is committed | About one page and one pending block per column | Azure Block Blob supports this directly. Row groups can be large without using more memory. |
| Write each column's pages to a local temp file and join the files when the row group closes | About one page per column | Works with any destination. Needs local disk. |
| Write many small row groups | Small | Hurts compression and read speed. This is a setting, not a design. |
| Put column chunks in separate files, which the format allows | Small | Almost no reader supports it, including Spark. Rejected. |

Storage services differ in how well they fit the second option:

- Azure Block Blob: blocks have no minimum size and can be uploaded in any
  order. A final call lists the blocks in the order they should appear. A blob
  can have at most 50,000 blocks.
- Amazon S3 multipart upload: every part except the last must be at least
  5 MiB, there can be at most 10,000 parts, and the part number given at upload
  time fixes the order. Staging per column would force each column to hold
  several megabytes, which for a wide table uses more memory than buffering
  the row group.

## Decision

The layout is a strategy that core selects per writer.

- The default buffers one row group in memory, limited by a byte budget, and
  writes it in order.
- Per-column spill to local temp files is available in core as an option.
- Per-column staging is used by the Azure package.
- The S3 package uses in-memory buffering and uploads parts in parallel.

## Consequences

- Column writers hand finished pages to the layout and do not know where the
  bytes go. The layout reports where each chunk ended up, and core computes
  the footer from that.
- All layouts must produce the same file for the same input. Tests compare
  them byte for byte.
- With in-memory buffering, the memory budget also limits row group size. A
  small budget on a wide table gives small row groups. The staged layouts do
  not have this limit.
- The limits quoted for S3 and Azure should be checked against the services'
  current documentation when the add-on packages are built.
- Joining complete row groups from several writers on the storage service is
  possible with the same technique. It is not part of the first release.
