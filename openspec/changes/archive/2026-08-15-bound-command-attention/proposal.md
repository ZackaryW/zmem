## Why

Repository commands can currently walk or return an unbounded amount of Git-derived memory, and the public deep-check example emphasizes an existing reference instead of the intended proposed-message workflow. Agents need a predictable attention budget that is bounded by default while retaining an explicit full-history escape hatch.

## What Changes

- **BREAKING**: Bound repository attention by the most recent 500 commits and 400 syntactically valid zmem annotation occurrences by default.
- Add global `--commit-limit` and `--node-limit` options; each accepts a positive integer or `-1` for unlimited traversal.
- Add `ZMEM_COMMIT_LIMIT` and `ZMEM_NODE_LIMIT` default overrides, with explicit CLI values taking precedence over the environment and built-in defaults.
- Count entry, custom, unsupported, DECAY, and CANCEL annotations toward the node budget even when an annotation produces no stored entry; never partially include one historical commit.
- Keep command-local result limits distinct from the global attention limits and report when a bounded view is truncated.
- Make `zmem check --file <path> --deep` the primary deep-check workflow: bounded history is replayed in isolation before the proposed message is evaluated, and an insufficient window produces an explicit incomplete-history result rather than a misleading unresolved effect.
- Preserve explicit historical-reference checking as an additional deep-check mode and leave single-target and non-repository service-management commands unaffected by history traversal limits.

## Capabilities

### New Capabilities

- `command-attention`: Global commit/node attention budgets, environment and CLI resolution, counting rules, and bounded-result reporting.

### Modified Capabilities

- `memory-cli`: Repository query commands expose bounded-view metadata while retaining their separate result-limit behavior.
- `commit-checking`: Deep proposed-file checks become the primary workflow and distinguish incomplete attention from a conclusive semantic failure.

## Impact

The global Python CLI parser, service client protocol, JSON/human envelopes, commit-checking and memory-query behavior, README, authoring skill, unit tests, and capability-owned Behave roots are affected. Existing scripts that depended on implicit complete-history traversal must opt in with both limits set to `-1`.
