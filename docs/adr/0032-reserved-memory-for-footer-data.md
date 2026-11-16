# A share of the memory budget is reserved for footer and page index data

Status: accepted
Date: 2026-11-16

## Context

The writer keeps a record of every page until the file is complete, because
the page index and footer are written last. This memory grows with the file. A
flush cannot free it. The memory budget and what a flush does are described in
[Memory](../architecture/memory.md).

With one budget for everything, growing footer data would leave less and less
for row data. The writer would ask for flushes more often. With the layout
that buffers a row group in memory, each flush closes a row group, so row
groups would shrink, and smaller row groups add footer data faster.

## Options considered

1. One budget for everything, and an error when footer data approaches it.
2. Reserve a share of the budget for footer data and give row data the rest.
3. One budget for everything, and leave it to the user to start a new file
   before the problem arises.

## Decision

Option 2.

- A share of the budget is set aside for page index and footer records.
- Everything else is charged to the rest of the budget: values, dictionaries,
  held pages, working space, the bloom filters of the open row group, and data
  on its way to the destination. This is called the row data part.
- The writer's `NeedsFlush` property becomes true when the row data part is
  full, not when the whole budget is.
- The size of the share is a setting. Its default will be chosen from
  benchmarks, with the other defaults.

This decides where the limit for row data sits. It does not decide what
happens when the reserved share itself fills up, which stays open.

## Consequences

- While the share has room, growth in footer data does not cause extra
  flushes or smaller row groups.
- The row data part is smaller than the budget from the first row. With the
  buffered layout, row groups are therefore somewhat smaller than they would
  be without a reserved share.
- The smallest workable budget, computed when a writer is created, includes
  the reserved share.
- The amount of the share in use is reported as a metric, so a user can see a
  large file approaching the limit.
- A user who turns the page index off needs a much smaller share, because the
  footer alone holds one record for each column in each row group and not one
  for each page.
- These points are still to be decided, and are listed as open questions in
  the [architecture overview](../architecture/README.md#open-questions):
  - What the writer does when the share is used up: raise an error that names
    the setting, or continue over the budget and report it. Continuing would
    mean the budget no longer limits the writer's memory.
  - Whether the share is set as a number of bytes or as a fraction of the
    budget.
  - How the share works when several writers use one budget.
