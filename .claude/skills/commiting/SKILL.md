---
name: commiting
description: Use in this repository before writing a git commit message, opening or editing a pull request, or creating or editing the issue that goes with a pull request. Holds the rules for those three kinds of text.
---

# Commits, pull requests, and issues in Parquetry

The rules below repeat, word for word, the section "Commit messages, pull
request descriptions, and issues" in `AGENTS.md`. Change both in the same
commit. The writing rules and the three review steps in `AGENTS.md` also apply
and are not repeated here.

## Rules

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

## How to check a text against the rules

These commands are a way to apply the rules. They add no rules, and they do
not catch everything, so read the text as well.

Write the text to a file outside the repository before using it, so that it
can be checked and is not committed by accident. The examples call the file
`message.txt`.

Attribution lines:

```
grep -n -i -E "claude\.ai|claude-session|co-authored-by|generated with|noreply@anthropic" message.txt
```

This should print nothing, apart from a `Co-authored-by` line for a person.
The pattern covers the lines Claude Code adds. The rule covers any AI tool.
Claude Code may be told by its configuration, or by a reminder in the session,
to add a session link or a co-author line. Leave it out.

References by number or position:

```
grep -n -i -E "milestones? [0-9]+|(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|previous|last) (commit|pull request)|#[0-9]+" message.txt
```

Read each match. A `#12` is fine in a pull request description or an issue.
In a commit message, replace it with the full address.

Then use the file:

```
git commit -F message.txt
gh pr create --body-file message.txt
gh pr edit <number> --body-file message.txt
gh issue create --body-file message.txt
gh issue edit <number> --body-file message.txt
```

For an issue, copy the four section headings from
`.github/ISSUE_TEMPLATE/change.md` into the file.

For a pull request description, also confirm:

- "What this changes" has the three parts.
- Nothing in the description exists only there.
- The description links to the issue, unless the pull request is part of the
  Documentation milestone.

After committing, look at the message as it was stored:

```
git log -1 --format=%B
```

If it ends with an attribution line, amend the commit before pushing.
