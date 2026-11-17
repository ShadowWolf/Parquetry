# Core I/O is async only, with sync wrappers in a separate package

Status: accepted
Date: 2026-11-14

## Context

Flushing and completing a file involve I/O. Some callers work in synchronous
code and would like synchronous versions of those calls. Offering both in core
would require every destination and layout to implement each operation twice.

## Options considered

1. Async and sync forms of flush, complete, and dispose in core.
2. Async only. Synchronous callers block on the tasks themselves.
3. Async only in core, with an optional package that provides the synchronous
   calls.

## Decision

Option 3. Core has `FlushAsync`, `CompleteAsync`, and `DisposeAsync` only. A
separate package, `Parquetry.Sync`, adds synchronous
methods that wait on the async ones. It is not referenced by any other package.

## Consequences

- Destinations and layouts implement each I/O operation once.
- The synchronous package blocks a thread while waiting. This is safe where
  there is no synchronization context, as in console applications and ASP.NET
  Core. In UI applications, and under heavy load on the thread pool, it can
  cause deadlocks or delays. The package documentation states this.
- Core uses `ConfigureAwait(false)` on every await, so that blocking callers
  are not deadlocked by a captured context.
- `Write(in T)` is already synchronous and is not affected.
