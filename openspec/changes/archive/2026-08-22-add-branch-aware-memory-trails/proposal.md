## Why

Repository-wide memory queries lose precision in monorepos, while the current single-HEAD projection cannot retain branch-specific DECAY, CANCEL, or metadata state. Users need fast affected-area filtering and live Git-reference queries without forcing historical cache rebuilds or duplicating immutable commit facts per branch.

## What Changes

- Add repeatable `--area` filters to `recall` and `search`, with repository-relative hierarchical matching and null/global compatibility for legacy memories.
- Add `--ref` selection for any Git commit-ish while resolving branch names live rather than treating cached aliases as authoritative.
- Add the built-in `zmem(META)[from,to,...]` effect for atomic, range-based patches to declared commit metadata keys.
- Introduce the initial metadata keys `affected_areas`, `owner`, and `tags`; META cannot alter canonical annotation identity, content, conventional scope, score, or validity.
- Expose typed trail diagnostics in ordinary query envelopes while keeping TRAIL cache-native rather than defining a `zmem(TRAIL)` annotation or dedicated trail-management commands.
- **BREAKING**: bump the Python/native protocol and schema compatibility identities so clients cannot silently use a service that lacks trail and META semantics.

## Capabilities

### New Capabilities
- `memory-metadata`: Defines affected-area values, automatic area derivation, META patch operations, range resolution, and metadata precedence.
- `memory-trails`: Defines live reference selection and the typed trail identity exposed by public queries.

### Modified Capabilities
- `memory-cli`: Adds `--area` and `--ref` filtering and trail metadata to the JSON-first query surface.
- `annotation-vocabulary`: Adds META as a built-in metadata effect while preserving canonical entry and DECAY/CANCEL ownership boundaries.

## Impact

The CLI parser, extension host, protocol constants, query envelopes, documentation, tests, and public Behave surfaces change in `zmem`. The paired `zmem-cache` change supplies protocol-compatible trail storage, range application, migration, and reference-aware query results; the matching native release must be published before the Python release selects it.
