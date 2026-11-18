# The solution starts with three projects, and the build enforces the technical rules

Status: accepted
Date: 2026-11-18

## Context

The [architecture overview](../architecture/README.md#repository-layout)
plans twelve projects. When the solution was created, in the "Solution and
CI" milestone, none of them had any code.

`AGENTS.md` has technical rules that a build can check: the core package has
no third-party dependencies, the main code path works under Native AOT and
trimming, and every public type and member has an XML doc comment. A rule
that the build checks does not depend on a reviewer noticing.

## Options considered

For the projects:

1. Create only the projects the milestone uses. Each other project is added
   by the milestone that first puts code in it.
2. Create all twelve, most of them empty.

## Decision

Option 1 for the projects. The project owner chose it on 2026-11-17. The
solution has `src/Parquetry`, `tests/Parquetry.Tests`, and
`tests/Parquetry.Interop.Tests`. With option 2, settings such as the source
generator's `netstandard2.0` target would have been written before there was
code to try them on.

The build settings below were proposed with the plan for the milestone, and
the project owner raised no objection to them:

- The solution file is `Parquetry.slnx`, the format the .NET 10 SDK creates.
- `global.json` asks for the .NET 10 SDK, version 10.0.100 or a later 10.0
  version.
- `Directory.Packages.props` holds the version of every package. Project
  files name a package without a version.
- `Directory.Build.props` sets what every project shares: the `net10.0`
  target, nullable annotations, and warnings treated as errors.
- `src/Directory.Build.props` adds what the published packages share. It
  turns on the XML documentation file, so a public type or member without a
  doc comment is a warning and fails the build.
- `Parquetry.csproj` sets `IsAotCompatible`, which turns on the analyzers
  that report code that would fail under Native AOT or trimming.
- `Parquetry.csproj` has a build target that fails the build if the project
  refers to a package.
- The tests use xUnit v3, as the decision on [tooling](0023-tooling.md)
  says. `global.json` makes `dotnet test` run them with
  Microsoft.Testing.Platform, the test runner that xUnit v3 is built on from
  its version 4.

## Consequences

- A milestone that adds a project also adds it to the solution and writes its
  settings. The repository layout in the architecture overview shows which
  projects exist.
- The four build rules were each tried by breaking them: a public class
  without a doc comment, an unused variable, a call that needs reflection,
  and a package reference in the core project. Each failed the build.
- Test projects do not need XML doc comments, because the setting is in
  `src/Directory.Build.props`.
- The target that rejects package references does not count the references
  the SDK adds for its own build tools, which are marked private. A unit test
  covers the other direction: it fails if the built core assembly refers to
  an assembly that does not ship with the .NET runtime.
- Nothing about packaging is set: no package description, no version number,
  and no rule for how versions are chosen. These are decided before the
  first package is built. The "Flat files" milestone needs a version first,
  because the file's `created_by` field contains it.
