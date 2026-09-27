# Proposal

## Why

The native service change `../zmem-cache/openspec/changes/isolate-lookups-and-tier-history-indexing` separates lookups from background indexing and returns typed deferred/timeout outcomes. The Python client currently waits without a subprocess deadline and classifies native stderr strings, so it needs a coordinated contract update.

## What Changes

- **BREAKING**: Cold snapshot commands return structured `not_ready` promptly instead of waiting indefinitely for initial indexing; callers retry explicitly after indexing progresses.
- Expose a positive `--timeout-ms` request budget and propagate remaining time through client Git observation and native execution, with bounded cleanup.
- Preserve native `not_ready`, `busy`, `timeout`, `stale_ref`, job identity and retry guidance in machine-readable CLI failures; never label service delays as invalid annotations.
- Keep successful snapshot envelopes, exact observed-OID selection, attention bounds, and check semantics intact.
- Coordinate protocol/schema identity, runtime compatibility fixtures, tests, and query guidance with the native release.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `memory-cli`: Bounded snapshot waits, typed transient outcomes, and subprocess cleanup.
- `commit-checking`: Deadline-bounded checks with service failure distinct from semantic invalidity.

## Impact

- `src/zmem/client.py`, `src/zmem/cli.py`, Git observation utilities, protocol/runtime identity and output handling.
- Client/protocol/runtime tests, memory-cli and commit-checking behavior scenarios, README and memory-query skill guidance.
- Depends on the native companion change; this change does not implement native scheduling, storage, or multi-database support.
