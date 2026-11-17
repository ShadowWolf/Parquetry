# The Arrow schema is not written in the first release

Status: accepted
Date: 2026-11-16

## Context

Arrow is the in-memory data format that pyarrow works with. Some Arrow types
do not survive being written to Parquet. A length of time, which Arrow calls
`duration`, is written as a plain 64-bit integer, and a timestamp loses the
name of its time zone. A Parquet file ends with a
footer, a block of metadata that a reader loads before anything else, and the
footer can hold key-value pairs. When pyarrow writes a Parquet file, it stores
Arrow's own description of the columns there, under the key `ARROW:schema`.
When pyarrow reads the file back, it uses that entry to restore the Arrow
types.

pyarrow is this library's
[reference for what is written](0031-pyarrow-as-reference.md), so leaving the
key out is a difference from pyarrow and needs a decision.

To see what the key changes, pyarrow 26.0.1 wrote the same table twice, once
with the key and once with its `store_schema` setting turned off, and read
both files back. The table shows the type pyarrow reported for each column.
The program is `docs/research/pyarrow-parity/probe.py`, and its output is
saved beside it.

| Column written by pyarrow | Read back with the key | Read back without it |
|---|---|---|
| A length of time (`duration`) in microseconds | A length of time | A plain 64-bit integer |
| Text held in an Arrow dictionary | A dictionary of text | Plain text |
| A timestamp with a named time zone | The same time zone | UTC |
| An unsigned 8-bit integer, a time of day, a UUID, a decimal | The type that was written | The type that was written |

How each row applies to this library:

- The first applies to a `TimeSpan` stored as a count of microseconds. With
  the key, the column could be declared as a length of time. Without it,
  pyarrow reads a 64-bit integer. A `TimeSpan` stored as a count of ticks is a
  64-bit integer either way, because Arrow has no unit of 100 nanoseconds.
- The second does not apply while the key is not written. It would matter only
  if the key were added and declared a column of text as a dictionary.
- The third does not apply. A .NET `DateTimeOffset` carries an offset for each
  value, not a time zone for the column.
- The fourth shows that these types do not need the key. Parquet's own schema
  is enough for pyarrow to restore them.

Writing the key has two costs:

- The value is not in the format Parquet uses for its own metadata. It is a
  schema message of Arrow's IPC format, the format Arrow uses to pass data
  between processes, stored as base64 text. This was
  checked with `docs/research/pyarrow-parity/arrow_schema_key.py`. The
  library has a writer for Parquet's metadata format and would need another
  one for Arrow's. The core package takes no third-party dependencies, so the
  library would have to include that writer itself.
- The footer grows, and a reader loads the whole footer to open a file. For a
  file with 500 columns, pyarrow's footer was 94,451 bytes with the key and
  60,190 bytes without it.

## Options considered

1. Write the key by default, as pyarrow does.
2. Offer it as an option in the first release.
3. Leave it out of the first release. It can be added in a later release.

## Decision

Option 3. The first release does not write the `ARROW:schema` key. It can be
added in a later release. Nothing commits the project to adding it.

The design discussion recommended leaving the key out, and the project owner
agreed. The reasons for the recommendation:

- Of the columns compared, the only one the library writes that pyarrow
  reads differently without the key is a `TimeSpan` stored as a count of
  microseconds.
- Writing the key means building and testing a writer for a second metadata
  format. Offering the key as an option in the first release would cost the
  same work.

## Consequences

- This is a deliberate difference from pyarrow, listed on the
  [pyarrow parity](../architecture/pyarrow-parity.md) page.
- When pyarrow reads a file from the first release, it has only the Parquet
  schema to go on.
- A `TimeSpan` stored as a count of microseconds comes back from pyarrow as a
  64-bit integer, not as a length of time. The record on
  [TimeSpan](0027-timespan-needs-an-explicit-representation.md) already says
  that a column stored this way carries no unit in the file.
- The first release does not need a writer for Arrow's schema format.
- The roadmap lists the key among the items that may follow the first
  release. Whether to add it, and whether it would be written by default or
  only when asked for, is decided then.
