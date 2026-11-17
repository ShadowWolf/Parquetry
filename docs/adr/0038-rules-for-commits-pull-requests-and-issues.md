# Rules for commit messages, pull request descriptions, and issues

Status: accepted
Date: 2026-11-16

## Context

The project already has writing rules and three review steps for every pull
request, recorded under
[working rules for contributions](0024-working-rules-for-contributions.md).
Those rules say how to write and how to review. They do not say what a commit
message, a pull request description, or an issue has to contain.

While the first pull request was in review, the project owner set five rules
for these. One of them came from what the owner saw in that pull request: each
of its commit messages ended with a link to the AI session that wrote it,
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

The rules:

1. No tool attribution. A commit message, a pull request description, and an
   issue carry no link to an AI session, no "generated with" footer, and no
   co-author line or other trailer that names an AI tool.
2. The section "What this changes" in a pull request description covers the
   cause of the change, the change, and the expected behavior.
3. The pull request description is not the only record. Anything a reader
   needs after the merge is also in the repository or in the issue.
4. No abstract references. A milestone or a requirement is named or linked. A
   mention of an issue comes with its link.
5. After the Documentation milestone, every pull request has an issue that
   goes with it. The issue describes the cause of the change, what the change
   needs to do, how the change was validated, and any known issues left
   behind.

## Consequences

- The rules are in `AGENTS.md` and in `.claude/skills/commiting/SKILL.md`. The
  two must be changed together.
- The first rule takes precedence over a tool's default. A tool that is set
  up to add a session link or a co-author line leaves it out here.
- The commits made in the first pull request before this rule were rewritten
  to remove the session link, and the branches were pushed again. Nothing had
  been merged.
- Each milestone in the [roadmap](../architecture/roadmap.md) has a name, so
  that it can be referred to by name and not by number.
- The pull request template has the three parts under "What this changes" and
  a section for the link to the issue. `.github/ISSUE_TEMPLATE/change.md` has
  the four sections of the issue.
- The first pull request belongs to the Documentation milestone and has no
  issue.
