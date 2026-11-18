# The solution starts with three projects, and the build checks three technical rules

Status: accepted
Date: 2026-11-18

## Context

The [architecture overview](../architecture/README.md#repository-layout)
plans twelve projects. When the solution was created, in the "Solution and
CI" milestone, none of them had any code.

`AGENTS.md` has technical rules that a build can check, fully or in part: the
core package has no third-party dependencies, the main code path works under
Native AOT and trimming, and every public type and member has an XML doc
comment. A rule that the build checks does not depend on a reviewer noticing.

## Options considered

For the projects:

1. Create only the projects the milestone uses. Each other project is added
   by the milestone that first puts code in it.
2. Create all twelve, most of them empty.

## Decision

Option 1 for the projects. The project owner chose it on 2026-11-17. The
solution has `src/Parquetry`, `tests/Parquetry.Tests`, and
`tests/Parquetry.Interop.Tests`. With option 2, settings would have been
written before there was code to try them on. One example is the planned
source generator project, which has to target `netstandard2.0` because the C#
compiler requires that of generators.

On the same day the project owner was given a list of settings that would be
used unless the owner said otherwise. The owner answered the questions that
came with the list and did not comment on it. The list was:

- The solution file is `Parquetry.slnx`, the format the .NET 10 SDK creates.
- `global.json` asks for the .NET 10 SDK.
- `Directory.Packages.props` holds the version of every package. Project
  files name a package without a version.
- Nullable annotations are on and warnings are treated as errors, for every
  project. These are in `Directory.Build.props`, with the `net10.0` target.
- A public type or member without a doc comment fails the build. This is in
  `src/Directory.Build.props`, which turns on the XML documentation file for
  the published packages. The missing comment is then a warning, and so an
  error.
- `Parquetry.csproj` sets `IsAotCompatible`, which turns on the analyzers
  that report code that would fail under Native AOT or trimming.
- The tests use xUnit v3, as the decision on [tooling](0023-tooling.md)
  says.

The author of the change added the settings below while building it. They
were not on the list.

- `Parquetry.csproj` has a build target, `RejectDependencies`, that fails
  the build if the project file refers to a package, to a framework other
  than the base one, to an assembly file, or to another project whose
  assembly it would use.
- `global.json` accepts version 10.0.100 of the SDK or any later 10.0
  version.
- `global.json` makes `dotnet test` run the tests with
  Microsoft.Testing.Platform. The `xunit.v3` package, at version 4.0.3 here,
  is built on that test runner. The `--project` option of `dotnet test`,
  which the commands in `AGENTS.md` use, exists only with this setting.
- `Directory.Build.props` turns on implicit usings, the default for new .NET
  projects.
- NuGet's warnings about a package with a published security advisory stay
  warnings. As errors, a new advisory would fail every build, including
  builds of commits that did not change.

## Consequences

- A milestone that adds a project also adds it to the solution and writes its
  settings. The repository layout in the architecture overview shows which
  projects exist.
- The four build rules were each tried by breaking them: a public class
  without a doc comment, an unused variable, a call that needs reflection,
  and a reference of each kind that `RejectDependencies` rejects. Each failed
  the build.
- The analyzers report code that is known to fail under Native AOT or
  trimming. They do not prove that the library works there. The Native AOT
  test application, planned for the "Source generator" milestone, publishes
  and runs a real application.
- Test projects do not need XML doc comments, because the setting is in
  `src/Directory.Build.props`.
- `RejectDependencies` reads the project file. It lets through the package
  references that the SDK adds for its own build tools, such as
  `Microsoft.NET.ILLink.Tasks` for the analyzers, which the SDK marks as
  implicitly defined. A unit test checks the compiled assembly instead: it
  fails if the core assembly refers to an assembly that is not in the .NET
  runtime's folder. The test goes by file name, and it sees a dependency
  only once code uses it.
- If the core project ever needs a build-time package, such as an analyzer,
  `RejectDependencies` has to be changed to allow it by name.
- Nothing about packaging is set: no package description, no version number,
  and no rule for how versions are chosen. These are decided before the
  first package is built. The "Flat files" milestone needs a version first,
  because the file's `created_by` field contains it.
