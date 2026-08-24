## Why

The repository memory-query skill can be interpreted as encouraging callers to remove both history-attention bounds when broadening retrieval. Complete-history traversal is unnecessarily expensive for routine queries because zmem already reports attention truncation and supports bounded expansion.

## What Changes

- Tell agents not to use `--commit-limit -1 --node-limit -1` for ordinary memory retrieval.
- Prefer the default bounded attention window, then increase limits deliberately and proportionally only when reported truncation leaves relevant evidence unresolved.
- Reserve unbounded traversal for an explicitly justified complete-history need.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. This is agent-facing skill guidance and does not change zmem's public behavior.

## Impact

Only `skills/zmem-query-memory` and this change's planning artifacts are affected. The CLI, attention defaults, specifications, tests, and `zmem-author-commits` deep-check guidance remain unchanged.
