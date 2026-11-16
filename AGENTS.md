# Working rules for this repository

These rules apply to every contributor, human or AI, and to every AI tool used
here. Tool-specific files such as `CLAUDE.md` point to this file and add
nothing of their own.

## What this project is

Parquetry is a C# library that writes .NET objects to Parquet files. It is
MIT licensed and will be published on NuGet. The priorities, in order, are
bounded memory use, speed, streaming output, and ease of use.

Read these before changing anything:

- `docs/architecture/README.md` describes how the library is built.
- `docs/adr/README.md` lists the decisions made so far and why.
- `docs/architecture/roadmap.md` lists the order of work.

## Writing

These rules cover everything a person reads: code comments, XML doc comments,
documentation, decision records, commit messages, pull requests, and issues.

1. Write the way an engineer writes to a colleague. Do not use phrasing that
   marks text as machine-written, cliches, or figures of speech you made up.
2. Use plain words. Keep the text as short and as non-technical as the reader
   allows. Explain a term the first time it appears if a new contributor might
   not know it.
3. Do not point to a requirement or decision by an identifier alone. "Per
   ADR 12" or "satisfies R-4.2" tells the reader nothing. Say what the
   requirement or decision is. A title or link may follow.
4. Describe things as they are. Documentation and comments should make sense
   to someone who has not seen the change history. Change history belongs in
   commit messages and pull requests.

## Pull requests

Every pull request goes through three steps before it is submitted.

### Adversarial review

Someone who did not write the change tries to find defects in it: wrong
behavior, missed cases, unsafe memory handling, broken compatibility, weak
tests. For AI-written changes, the reviewer is a separate agent or session that
is given the diff and asked to find faults. Each finding is fixed or answered.

### Clean read

A reviewer with no knowledge of the work session reads only the diff and the
pull request description. This can be a person, or an AI agent started fresh
with no prior context. The reviewer reports anything that is unclear,
unexplained, or hard to follow. Those points are fixed in the code, comments,
or description.

### Red testing

Each new or changed test is run against code that lacks the change, or with the
behavior deliberately broken. The test must fail, and it must fail for the
reason it was written to catch. Then the test must pass with the change in
place. A test that has never been seen to fail does not count as red tested.

### Recording the steps

The pull request description has a section for each step. The template in
`.github/pull_request_template.md` provides them. Write what the adversarial
review found and how it was resolved, what the clean read raised, and how each
test was shown to fail.

### Hotfixes and urgent releases

The person requesting the work can waive these steps by stating that the change
is a hotfix or an urgent release. An AI agent must not decide this on its own.
The pull request must then say which steps were skipped.

## Technical rules

- The core package `Parquetry` has no third-party dependencies and no
  `Microsoft.Extensions` dependencies.
- The main code path must work under Native AOT and trimming.
- Every public type and member has an XML doc comment. The build fails without
  one.
- A new architectural decision gets a decision record in `docs/adr` in the
  same pull request.
- Where a choice has to be made about what is written to a file, find out what
  pyarrow writes by running it, and match it unless there is a reason not to.
  Record the reason. `docs/architecture/pyarrow-parity.md` lists the
  comparisons made so far.

Build and test commands will be added here when the solution is created.
