# A share of the memory budget is reserved for footer and page index data

Status: accepted
Date: 2026-11-16

## Context

The writer keeps a record of every page until the file is complete, because
the page index and footer are written last. This memory grows with the file. A
flush cannot free it.

With one budget for everything, growing footer data would leave less and less
for row data. The writer would ask for flushes more often. With the buffered
layout each flush closes a row group, so row groups would shrink, and smaller
row groups add footer data faster.

## Options considered

1. Raise an error when footer data approaches the budget.
2. Reserve a share of the budget for footer data and give row data the rest.
3. Leave it to the user to start a new file before the problem arises.

## Decision

Option 2.

- A share of the budget is set aside for page index and footer records.
- Row data uses the rest: values, dictionaries, held pages, and working space.
  `NeedsFlush` is worked out against that part only.
- The size of the share is a setting. Its default will be chosen from
  benchmarks, with the other defaults.

## Consequences

- Growth in footer data does not cause extra flushes or smaller row groups.
- The smallest workable budget, computed when a writer is created, includes
  the reserved share.
- The amount of the share in use is reported as a metric, so a user can see a
  large file approaching the limit.
- A user who turns the page index off needs a much smaller share, because the
  footer alone holds one record per column chunk and not one per page.
- What the writer does when the reserved share is used up is still to be
  decided. The choices are to raise an error that names the setting, or to
  continue over the budget and report it. This is listed as an open question
  in the [architecture overview](../architecture/README.md#open-questions).
- The same question for a staged destination that runs out of segments is
  also still open.
