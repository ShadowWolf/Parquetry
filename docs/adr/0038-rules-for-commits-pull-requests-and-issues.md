# Rules for commit messages, pull request descriptions, and issues

Status: accepted
Date: 2026-11-16

## Context

The project already has writing rules and three review steps for every pull
request, recorded under
[writing rules and three review steps for every pull request](0024-working-rules-for-contributions.md).
Those rules do not cover tool attribution, what a pull request description has
to say about a change, how to refer to other things, or issues.

While
[the pull request that adds the documents](https://github.com/ShadowWolf/Parquetry/pull/1)
was in review, the project owner set five rules for these. The commit messages
in that pull request each ended with a link to the AI session that wrote them,
which the tool adds by default. The owner asked for that to stop and for the
existing messages to be corrected.

## Options considered

The owner stated the rules. The open point was where to write them so that
they are applied:

1. In `AGENTS.md` only, which every contributor and AI tool is told to read.
2. In a Claude Code skill only. A skill is a file of instructions that Claude
   Code loads when it does a particular kind of task.
3. In both.

## Decision

Option 3. The owner asked for a skill. `AGENTS.md` also has the rules, because
it is the file that applies to every tool and person.

The rules as the owner gave them:

1. A commit message, a pull request description, and an issue have no
   `claude.ai` link, no footer, and no co-author line.
2. The section "What this changes" in a pull request description covers the
   cause of the change, the change, and the expected behavior.
3. A pull request description is not the only source of documentation or
   information.
4. Documents, issues, and other things are not referred to in the abstract. A
   milestone or a requirement is named or linked. A mention of an issue comes
   with a link.
5. After the Documentation milestone, every pull request has an issue that
   goes with it. The issue describes the cause of the change, what the change
   needs to do, how the change was validated, and any known issues left
   behind.

The owner did not give reasons for the rules, and this record does not supply
any.

`AGENTS.md` states the rules in more detail than the owner did. These points
were added when the rules were written out, to make them usable, and the owner
can change them:

- The rule against attribution covers any AI tool, not only Claude. It covers
  attribution lines. Text can still name a tool where the tool is the subject,
  as a review section does when an AI agent did the review.
- The rule against abstract references also covers commits, which are given by
  hash, and documents, which are given by path or title.
- On GitHub, `#12` in a pull request description or an issue counts as a link.
  A commit message has the full address.
- The pull request description links to the issue, and the issue is completed
  before the pull request is submitted.
- A pull request that is part of the Documentation milestone needs no issue.
  Every other pull request does, including a later change to the documents.
- The record of the three review steps stays in the pull request description.
  So that it is not only there, the message of a commit that answers a review
  says what the review found, and the issue says how the change was validated.

## Consequences

- The rules are in `AGENTS.md` and in `.claude/skills/commiting/SKILL.md`,
  word for word. The two are changed in the same commit. The skill also has
  commands for checking a text against the rules.
- The rule against attribution takes precedence over a tool's default. A tool
  that is set up to add a session link or a co-author line leaves it out here.
- The commit messages written before the rule were corrected. `main` and the
  pull request's branch were rewritten and pushed again, which was possible
  because nothing had been merged.
- Each milestone in the [roadmap](../architecture/roadmap.md) has a name, so
  that it can be referred to by name and not by number.
- The pull request template has the three parts under "What this changes" and
  a section for the link to the issue. `.github/ISSUE_TEMPLATE/change.md` has
  the four sections of the issue.
- The pull request that adds the documents is part of the Documentation
  milestone and has no issue.
