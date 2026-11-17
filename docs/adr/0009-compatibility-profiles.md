# Profiles are named presets over individual options

Status: accepted
Date: 2026-11-14

## Context

The Parquet format has many optional parts, and readers support different
subsets. A file that pyarrow reads may fail in Spark because of one type or one
encoding. Users want to say "make this readable by Spark" without learning
which settings that implies. Some users also need to change a single setting
for an unusual reader.

## Options considered

1. Named presets that set defaults, with individual options that can override
   them, and a check that reports overrides the preset's readers cannot handle.
2. Strict presets that cannot be overridden.
3. Individual options only, with documented recipes for each reader.

## Decision

Option 1. A profile is a named set of defaults for format details such as data
page version, timestamp form, list layout, permitted encodings, and codec. A
user picks a profile and may override any option. When a writer is created,
validation lists every setting that the profile's readers cannot read.

Options are resolved in this order: profile defaults, writer options,
per-column options, then validation.

## Consequences

- A profile is an object with a name, not an enum value. New profiles can be
  added without breaking existing code.
- The first release has two profiles: `Compatible`, which is the default, and
  `Modern`, which uses newer format features.
- An override outside the profile produces a compatibility message. A strict
  setting turns those messages into errors.
- Validation reports all problems at once, so a user does not fix them one at
  a time.
- Each profile's claims are meant to be backed by tests against the readers it
  names. Where a claim rests on reading a reader's source code and not on a
  test, the documentation says so.
