# CI checks formatting and links, and Dependabot proposes updates

Status: accepted
Date: 2026-11-18

## Context

Continuous integration builds the solution and runs the tests. When it was
set up, the project owner was asked which of four optional additions to
include.

## Options considered

Each of these could be included or left out:

1. A formatting check: an `.editorconfig` file with the code style, and a
   step that fails when a C# file does not follow it.
2. A link check: a step that fails when a relative link in a Markdown file
   points to a file or heading that does not exist.
3. Dependabot, which opens a pull request when a dependency has a new
   version. The question said that each of those pull requests needs an
   issue and the review steps, under the working rules.
4. A code coverage report attached to each run. The question said that there
   is no library code to cover until the "Flat files" milestone.

## Decision

The project owner chose the first three on 2026-11-17 and did not choose the
coverage report. This record does not rule a coverage report out for later.

The author of the change chose how each is done, while building it:

- Formatting: `dotnet format --verify-no-changes`. The `.editorconfig` sets
  indentation, line endings, and three C# rules: a file declares its
  namespace without braces, using directives go above the namespace, and
  `System` namespaces come first. The C# rules were picked as common .NET
  practice and can be changed. No other decision depends on them.
- Line endings: `.gitattributes` makes every checkout use LF. The CI job runs
  on Linux. The setting is for a contributor who runs the check on Windows,
  where Git is often set to check files out with CRLF and the check would then
  report every file.
- Links: `.github/scripts/check_links.py`, a script in this repository that
  uses only Python's standard library. It checks relative links and the
  headings they name. It does not check web addresses, so a run does not
  fail because another site is down. The comment at the top of the script
  lists the forms of link it handles and the ones it does not.
- Dependabot: `.github/dependabot.yml` covers NuGet packages, the actions in
  the workflow, the base images of the reader containers, and the Python
  packages in the Python container. It checks once a week.
- The actions in the workflow are named by commit hash, with the version in
  a comment. A version tag can be moved to different code later, and a hash
  cannot. Dependabot updates both.

## Consequences

- A pull request with unformatted C# code or a broken relative link fails.
  Both checks can be run locally, with the commands in `AGENTS.md`.
- A link to a web address that stops working is not caught.
- Every pull request from Dependabot follows the rules in `AGENTS.md`, like
  any other. Whoever takes the update on opens an issue for it, does the
  three review steps, and rewrites the description, which Dependabot wrote,
  to the template.
- Each reader container's Dockerfile has its own entry in the Dependabot
  file, because the two Spark containers need different rules. For the
  Spark 3.5 container, Dependabot is told to propose patch releases only.
  For the Spark 4 container, it is told to propose every release before
  Spark 5.
- The Dependabot rules were written from Dependabot's documentation and
  source code. They have not been seen to work, because Dependabot reads the
  file only from `main`.
- A new pyarrow version is proposed like any other update. pyarrow is also
  the [reference for what is written](0031-pyarrow-as-reference.md), so such
  an update can change what the comparisons on the
  [pyarrow parity](../architecture/pyarrow-parity.md) page show.
