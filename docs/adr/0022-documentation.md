# Decisions and architecture are documented in the repository

Status: accepted
Date: 2026-11-14

## Context

The project owner wants the design documented thoroughly as it is made. The
reasons behind decisions, and the options that were rejected, are easy to lose
once the code exists.

## Options considered

1. A decision record for each decision, an architecture section with a page
   per subsystem, and required XML doc comments on public API.
2. A single architecture document that is updated over time.
3. Option 1, also built into a published documentation site from the first
   commit.

## Decision

Option 1.

- `docs/adr` holds one record per decision, in the format described in its
  README.
- `docs/architecture` holds an overview and one page per subsystem.
- `docs/research` holds the small programs used to check how other libraries
  behave, so that a statement such as "checked by running it" can be checked
  again.
- Every public type and member has an XML doc comment. The build treats a
  missing comment as an error.

## Consequences

- A pull request that makes an architectural decision adds a decision record.
- Architecture pages describe the design as it is and are updated when it
  changes. Decision records are not rewritten.
- A documentation site can be generated from these files later without
  restructuring them.
- All of this text follows the writing rules in `AGENTS.md`.
