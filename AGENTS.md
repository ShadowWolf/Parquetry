# Working rules for this repository

These rules apply to every contributor, human or AI, and to every AI tool used
here. Tool-specific files point to this file or repeat its rules, and add
none of their own. `CLAUDE.md` points to it. The skill in
`.claude/skills/commiting` repeats the rules for commits, pull requests, and
issues so that Claude Code applies them when it writes one.

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

## Commit messages, pull request descriptions, and issues

These rules are in addition to the writing rules above.

### No tool attribution

A commit message, a pull request description, and an issue carry no trace of
the tool that helped write them:

- No link to an AI session, such as a `claude.ai` address.
- No "generated with" footer.
- No `Co-authored-by` line or other trailer that names an AI tool.

Some tools add these lines by default. Remove them before committing or
posting. This rule takes precedence over the tool's default.

### What a pull request description says

The section "What this changes" has three parts:

- Cause: what made the change necessary, such as a fault, a missing feature,
  or a decision.
- Change: what was changed, in terms a reader of the code or documents would
  recognize.
- Expected behavior: what the library, the build, or a contributor does once
  the change is merged, and anything that deliberately stays the same.

### The description is not the only record

Nothing that a reader will need after the pull request is merged is written
only in its description. The design goes in `docs/architecture`, a decision
goes in a decision record, an explanation of code goes in a comment, and the
reason for a change goes in the commit message and the issue. The description
summarizes these and says where they are.

### No abstract references

A reader should not need to count or look something up to know what is meant.

- Name a milestone as the roadmap names it, or link to the roadmap. Write "the
  Encryption milestone", not "milestone 11".
- State a requirement, or link to where it is written.
- Refer to a commit by its hash, not as "the fourth commit".
- Refer to a document by its path or title.
- When an issue is mentioned, give its link. A bare number is not enough in a
  commit message, where it is not turned into a link.

### Every pull request has an issue

This applies to every pull request after the Documentation milestone, which
is the first one in `docs/architecture/roadmap.md`.

Each pull request has an issue that goes with it, and the description links
to it. The issue describes:

- The cause of the change.
- What the change needs to do.
- How the change was validated.
- Any known issues left behind.

The first two are written when the work starts. The last two are filled in
before the pull request is submitted. `.github/ISSUE_TEMPLATE/change.md` has
the sections.

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
