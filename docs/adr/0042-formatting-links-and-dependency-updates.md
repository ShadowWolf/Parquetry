# CI checks formatting and links, and Dependabot proposes updates

Status: accepted
Date: 2026-11-18

## Context

Continuous integration builds the solution and runs the tests. Three further
checks were offered when it was set up, along with a code coverage report.

## Options considered

Each of these could be included or left out:

1. A formatting check: an `.editorconfig` file with the code style, and a
   step that fails when a C# file does not follow it.
2. A link check: a step that fails when a relative link in a Markdown file
   points to a file or heading that does not exist.
3. Dependabot, which opens a pull request when a dependency has a new
   version.
4. A code coverage report attached to each run.

## Decision

The first three are included. The project owner chose them on 2026-11-17.
The coverage report is left out. There is no library code to cover until the
"Flat files" milestone.

How each is done:

- Formatting: `dotnet format --verify-no-changes`. The `.editorconfig` sets
  indentation, line endings, and three C# rules: a file declares its
  namespace without braces, using directives go above the namespace, and
  `System` namespaces come first. `.gitattributes` makes every checkout use
  LF line endings, so the check gives the same result on Windows. The C#
  rules were picked as common .NET practice and can be changed. No other
  decision depends on them.
- Links: `.github/scripts/check_links.py`, a script in this repository that
  uses only Python's standard library. It checks relative links and the
  headings they name. It does not check web addresses, so a run does not
  fail because another site is down.
- Dependabot: `.github/dependabot.yml` covers NuGet packages, the actions in
  the workflow, the base images of the reader containers, and the Python
  packages in the reader container. It checks once a week.

## Consequences

- A pull request with unformatted C# code or a broken relative link fails.
  Both checks can be run locally, with the commands in `AGENTS.md`.
- A link to a web address that stops working is not caught.
- Every pull request from Dependabot follows the rules in `AGENTS.md`, like
  any other. It needs an issue and the three review steps, and its
  description, which Dependabot writes, has to be rewritten to the template.
- Dependabot does not propose the next major version of Spark for either
  Spark container. One stays on Spark 3.5 and the other follows Spark 4.
- A new pyarrow version is proposed like any other update. pyarrow is also
  the [reference for what is written](0031-pyarrow-as-reference.md), so such
  an update can change what the comparisons on the
  [pyarrow parity](../architecture/pyarrow-parity.md) page show.
- The actions in the workflow are named by commit hash, with the version in
  a comment. Dependabot updates both.
