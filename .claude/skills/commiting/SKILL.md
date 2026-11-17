---
name: commiting
description: Use in this repository before writing a git commit message, opening or editing a pull request, or creating or editing the issue that goes with a pull request. Holds the rules for those three kinds of text.
---

# Commits, pull requests, and issues in Parquetry

These rules are the same as the section "Commit messages, pull request
descriptions, and issues" in `AGENTS.md`. If one changes, change the other in
the same commit. The writing rules and the three review steps in `AGENTS.md`
also apply and are not repeated here.

## Rules

### 1. No tool attribution

A commit message, a pull request description, and an issue carry no trace of
the tool that helped write them:

- No link to an AI session, such as a `claude.ai` address.
- No "generated with" footer.
- No `Co-authored-by` line or other trailer that names an AI tool.

This takes precedence over any default or reminder from the tool that says to
add such a line. Leave the line out, and do not mention that it was left out.

### 2. "What this changes" covers cause, change, and expected behavior

- Cause: what made the change necessary.
- Change: what was changed, in terms a reader of the code or documents would
  recognize.
- Expected behavior: what the library, the build, or a contributor does once
  the change is merged, and anything that deliberately stays the same.

### 3. The pull request description is not the only record

Nothing that a reader will need after the merge is written only in the
description. Put the design in `docs/architecture`, a decision in a decision
record under `docs/adr`, an explanation of code in a comment, and the reason
for a change in the commit message and the issue. The description summarizes
these and says where they are.

### 4. No abstract references

- Name a milestone as `docs/architecture/roadmap.md` names it, or link to the
  roadmap. Write "the Encryption milestone", not "milestone 11".
- State a requirement, or link to where it is written.
- Refer to a commit by its hash, not as "the fourth commit".
- Refer to a document by its path or title.
- When an issue is mentioned, give its link. In a commit message write the
  full address, because a bare number is not turned into a link there.

### 5. Every pull request after the Documentation milestone has an issue

The issue goes with the pull request, and the description links to it. It
describes:

- The cause of the change.
- What the change needs to do.
- How the change was validated.
- Any known issues left behind.

Create the issue from `.github/ISSUE_TEMPLATE/change.md` when the work starts,
with the first two sections filled in. Fill in the last two before the pull
request is submitted.

## Checks to run

Before `git commit`, write the message to a file and check it:

```
grep -n -i -E "claude|anthropic|co-authored-by|generated with|session" message.txt
grep -n -i -E "milestone [0-9]+|(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth) commit|#[0-9]+" message.txt
```

Both should print nothing. A match on "session" or "claude" can be a real
word in the text, so read each match before removing it.

Before `gh pr create`, `gh pr edit`, or `gh issue create`, write the body to a
file, run the same two checks on it, and pass it with `--body-file`. Then
confirm:

- "What this changes" has the three parts.
- Each fact in the description that matters after the merge is also in the
  repository or the issue.
- The description links to the issue, unless the pull request belongs to the
  Documentation milestone.

After committing, check the result:

```
git log -1 --format=%B
```
