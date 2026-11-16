# pyarrow is the reference for how values are written

Status: accepted
Date: 2026-11-16

## Context

Many choices in a Parquet writer have more than one valid answer: how a small
decimal is stored, what happens when a timestamp loses digits, how a list is
laid out. pyarrow is the most widely used Parquet writer outside the Java
tools. Other tools are tested against its files, and many of this library's
users will also know its behavior.

Two decisions had already been made by checking pyarrow: a timestamp that does
not fit in microseconds raises an error, and a truncated value moves toward
1970.

## Options considered

1. Decide each case on its own merits.
2. Treat pyarrow's default behavior as the reference, and depart from it only
   for a stated reason.

## Decision

Option 2. Where the library has to choose how to write something, it writes
what pyarrow writes by default, where that is possible.

A departure needs a reason, and the reason is recorded. The usual reason is
that Spark cannot read what pyarrow writes, since reading by Spark without
settings is also a goal.

pyarrow's behavior is established by running it, not from memory or from
documentation alone. The programs are kept in `docs/research`.

## Consequences

- Each new decision about written output starts with a pyarrow run.
- [pyarrow parity](../architecture/pyarrow-parity.md) lists every comparison
  made so far: where the library matches, where it differs on purpose, and
  where a difference is still to be decided.
- The first review, on 2026-11-16 against pyarrow 26.0.1, found no decision
  that produces a file pyarrow cannot read. It found two defaults that differ
  without a recorded reason: how `byte` is annotated and how small decimals
  are stored. Both are listed as open questions.
- pyarrow's defaults change between versions. The parity page records the
  version checked, and it should be rechecked before each release.
- pyarrow writes Arrow's own schema into the file's metadata. This library
  does not, so a few types that pyarrow restores from that metadata, such as
  a length of time, come back to pyarrow as plain numbers.
