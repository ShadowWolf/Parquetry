# Unit tests run on three operating systems and on the .NET 11 runtime

Status: accepted
Date: 2026-11-18

## Context

The decision on [tooling](0023-tooling.md) chose GitHub Actions for
continuous integration. It did not say which operating systems the tests run
on. The decision to [target .NET 10 only](0030-target-dotnet-10.md) left one
point open: whether the tests also run on the .NET 11 runtime. An application
on .NET 11 can use a `net10.0` library, so some users will run the library on
a runtime it was not built for.

The reader tests run their readers in Linux containers. Of the runners GitHub
hosts, only the Linux ones can run Linux containers, so the reader tests run
on Linux whatever is decided here.

## Options considered

1. Unit tests on Linux, Windows, and macOS with .NET 10, and once more on
   Linux on the .NET 11 runtime.
2. Unit tests on Linux only with .NET 10, and once more on the .NET 11
   runtime.
3. Unit tests on Linux, Windows, and macOS with .NET 10 only.
4. Unit tests on Linux with .NET 10 only.

## Decision

Option 1. The project owner chose it on 2026-11-17.

The .NET 11 run does not add a `net11.0` target. The job builds the tests for
`net10.0` as usual and starts the test program with the environment variable
`DOTNET_ROLL_FORWARD` set to `LatestMajor`, which makes a .NET program start
on the newest runtime installed. This is what happens to the library inside
an application on .NET 11.

A job that meant to test .NET 11 and ran on .NET 10 would still pass. To
prevent that, each job sets `PARQUETRY_EXPECTED_RUNTIME_MAJOR` to the version
it means to test, and one unit test fails if the runtime is a different
version. The test is skipped when the variable is not set.

This was tried before the workflow was written. In a container that had only
the .NET 11 runtime, the `net10.0` test build ran and reported .NET 11.0.0.
Without the setting it did not start.

## Consequences

- The workflow is `.github/workflows/ci.yml`. It runs for every pull request
  and for every push to `main`.
- GitHub's Linux and Windows runners are x64 and its macOS runner is Arm64,
  so the unit tests run on both kinds of processor. That will matter for
  code that has a separate path for each, such as the compressors.
- A contributor needs only the .NET 10 SDK. `global.json` keeps the build on
  it even where a newer SDK is installed.
- The reader tests run on Linux x64 with .NET 10 only. A fault that appears
  only on another system or runtime, and only in a file's contents, would
  have to be caught by a unit test.
- A `net11.0` target, if one is added later, needs its own test run. The
  roll-forward job does not cover code compiled for .NET 11.
