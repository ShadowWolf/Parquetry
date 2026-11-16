# Writing rules and three review steps for every pull request

Status: accepted
Date: 2026-11-14

## Context

Much of this project will be written with AI tools. Text produced that way
tends to be wordy, to use stock phrases, and to refer to requirements by labels
that mean nothing to a reader. Code produced that way can pass its own tests
while being wrong, and tests can pass without checking anything.

The project owner set rules to address this.

## Options considered

The owner stated the rules. The open points were how to define the review
steps and how to record them.

For red testing: require every test to be seen failing, require tests to be
written before the code, or use a mutation testing tool.

For a clean read: a reader with no prior context, a final pass over wording by
the author, or both.

For records: a written section in the pull request, a checklist, or no record.

## Decision

Writing, in all text a person reads:

- No phrasing typical of AI output, no cliches, no invented figures of speech.
- Plain wording that is no longer or more technical than the reader needs.
- No references to requirements or decisions by identifier alone.
- Documentation and comments describe things as they are. Change history
  belongs in commit messages and pull requests.

Every pull request, before submission:

- Adversarial review: someone who did not write the change tries to find
  defects in it.
- Clean read: a reviewer with no knowledge of the work session reads only the
  diff and the description and reports what is unclear.
- Red testing: every new or changed test is shown to fail without the change,
  for the expected reason, and then to pass with it.
- The pull request description records each step in its own section.

The person requesting the work can waive the review steps by calling the
change a hotfix or an urgent release. The pull request then lists what was
skipped.

The rules are in `AGENTS.md` at the repository root, written for any AI tool or
person. `CLAUDE.md` refers to that file and adds nothing.

## Consequences

- Each pull request takes longer to prepare.
- For AI-written changes, the adversarial review and the clean read are done
  by separate agents or sessions that did not take part in writing the change.
- Red testing as defined does not require tests to be written first. It
  requires proof that each test can fail.
- An AI agent cannot waive the steps on its own judgment.
