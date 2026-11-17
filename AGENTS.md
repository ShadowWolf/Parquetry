# Working rules for this repository

These rules apply to every contributor, human or AI, and to every AI tool used
here. Tool-specific files point to this file or repeat its rules, and add
none of their own. `CLAUDE.md` points to it. A skill is a file of instructions
that Claude Code loads for one kind of task. The skill in
`.claude/skills/commiting` repeats the rules for commits, pull requests, and
issues, and adds only the commands for checking a text against them.

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

These rules are in addition to the writing rules above. The skill in
`.claude/skills/commiting` repeats this section word for word. Change both in
the same commit.

### 1. No tool attribution

A commit message, a pull request description, and an issue contain none of
these:

- A link to an AI session, such as a `claude.ai` address.
- A "generated with" footer.
- A `Co-authored-by` line or other trailer that names an AI tool. A trailer is
  a `Name: value` line at the end of a commit message.

Some tools add these lines by default. Leave them out. This rule takes
precedence over the tool's default.

The rule is about attribution lines. The text can still name a tool where the
tool is the subject, for example a review section that says an AI agent did
the review.

### 2. "What this changes" in a pull request description covers cause, change, and expected behavior

- Cause: what made the change necessary, such as a fault, a missing feature,
  or a decision.
- Change: what was changed, in terms a reader of the code or documents would
  recognize.
- Expected behavior: what the library, the build, or a contributor does once
  the change is merged.

### 3. The pull request description is not the only record

Documentation and other information must not exist only in a pull request
description. The design goes in `docs/architecture`, a decision goes in a
decision record, an explanation of code goes in a comment, and the reason for
a change goes in the commit message and the issue. The description can repeat
or summarize these.

The three review steps are recorded in the description, as "Recording the
steps" above says. So that the record is not only there, the message of a
commit that answers a review says what the review found, and the issue, where
there is one, says how the change was validated.

### 4. No abstract references

Do not refer to a document, an issue, or anything else by a label that the
reader has to look up or count to understand.

- A milestone: use the name the roadmap gives it, or link to it. Write "the
  Encryption milestone", not "milestone 11".
- A requirement: say what it requires, or link to where it is written. Write
  "the core package has no third-party dependencies", not "requirement 3".
- An issue: give its link. On GitHub, `#12` in a pull request description or
  in an issue is a link. In a commit message, write the full address.
- Other things, such as commits and documents: give a commit's hash and a
  document's path or title. Do not write "the fourth commit" or "the record
  above".

### 5. Every pull request after the Documentation milestone has an issue

Documentation is the first milestone in `docs/architecture/roadmap.md`. A pull
request that is part of it does not need an issue. Every other pull request
does, including a later change to the documents.

The issue describes:

- The cause of the change.
- What the change needs to do.
- How the change was validated.
- Any known issues left behind, meaning problems that remain.

The pull request description links to the issue.
`.github/ISSUE_TEMPLATE/change.md` has the four sections. The last two can
only be written when the work is done, so the issue is completed before the
pull request is submitted.

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
