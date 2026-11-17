# Dependency injection support is a separate package

Status: accepted
Date: 2026-11-14

## Context

Many applications configure libraries through `Microsoft.Extensions`
dependency injection, options, and configuration. Others, such as small tools
and some batch jobs, do not use a container and should not have to take those
packages.

## Options considered

1. Core has no `Microsoft.Extensions` dependencies. A separate package adds
   registration and configuration binding.
2. Core references the `Microsoft.Extensions` abstractions directly.

## Decision

Option 1. `Parquetry.Extensions.DependencyInjection` provides:

- `AddParquetWriter()` to register the writer factory and options.
- Binding of options from configuration.
- Named options, so an application can have several configurations, for
  example one per profile.
- A writer factory that resolves options and destinations from the container.
- Validation at application start of the settings that do not depend on a row
  type, so a bad configuration fails early. Checks that need the row type run
  when a writer is created.

## Consequences

- Core is usable without a container. `ParquetWriter.Create` takes a
  destination and an options object.
- The options type is a plain class with settable, nullable properties, where
  null means "use the profile's value". That shape binds from configuration
  without core referencing any configuration package.
- Core reports diagnostics through `System.Diagnostics` meters and activity
  sources, which are in the base class library. It does not use `ILogger`.
- Custom codecs and destinations are registered in code, not in configuration
  files.
