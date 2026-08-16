## Why

The new zmem needs a clean public model for recalling Git-backed memory while delegating durable indexing to the coordinated `zmem-cache` service. The revamp also needs deterministic, user-extensible annotation semantics instead of preserving the legacy in-process graph implementation.

## What Changes

- **BREAKING**: Replace the legacy in-process query implementation with a Python CLI that uses the always-on `zmem-svc` backend; no backward compatibility is promised, while useful `recall`, `show`, `search`, and `links` behavior remains a design target.
- Define scored annotation entries and built-in `DECISION`, `LESSON_LEARNT`, `DECAY`, and `CANCEL` behavior.
- Distinguish deterministic expanders, which perform canonical actions through a controlled expansion context, from lifecycle hooks, which observe completed expansion without changing canonical state.
- Load trusted global and repository-local Python expanders and hooks through deterministic `extend` and `overwrite` registries.
- Provide the Python extension-host boundary used by the coordinated Rust service.
- Preserve JSON-first command output, human-readable output, repository selection, and meaningful process failures where they fit the new service-backed architecture.

## Capabilities

### New Capabilities

- `memory-cli`: Public `zmem` command behavior and its interaction with the local service.
- `annotation-vocabulary`: Scored entries and the built-in text, decay, and cancellation semantics.
- `python-extensions`: Python expander and hook contracts, discovery, precedence, trust, and extension-host behavior.

### Modified Capabilities

None. This repository has no canonical specifications yet.

## Impact

- Affects the `zmem-2` Python package, command entry point, output schemas, configuration discovery, and extension-host protocol.
- Coordinates with the `revamp-zmem-service` change in `zmem-cache`, which owns service lifecycle, Git indexing, SQLite persistence, concurrency, and eviction.
- Retains the legacy `zmem` repository only as behavioral evidence; its Python graph, pickle cache, and extension internals are not compatibility contracts.
