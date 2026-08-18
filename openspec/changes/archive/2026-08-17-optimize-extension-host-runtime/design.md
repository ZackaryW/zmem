## Context

See `proposal.md`. The Python host reads one JSON request to EOF and exits. Remote runtime acquisition constructs the native release tag directly from the Python package version, even though runtime metadata already has separate host and binary version fields and compatibility is governed by protocol and schema identities.

## Goals / Non-Goals

**Goals:**

- Provide deterministic parser-only batch inspection without loading extensions or running hooks.
- Discover the greatest published stable native version compatible with this client and platform.
- Preserve local source precedence, strict manifests, artifact integrity, transactional activation, and standard-library-only packaging.

**Non-Goals:**

- Persistent Python workers, concurrent parsing inside the host, or changes to annotation grammar.
- Automatic native upgrades during ordinary memory commands.
- Accepting protocol or schema ranges; compatibility remains exact for both typed identities.

## Decisions

### Add one-request `inspect_batch` under protocol version 3

The request carries an `items` array of strict objects containing non-empty string `id` and string `message` fields. The host validates the complete array before parsing, calls the existing parser sequentially for each message, and returns an `inspections` array with the same ordered IDs, counts, and diagnostics. Invalid input fails the whole request. Sequential parsing preserves determinism and is sufficient because one Python startup is amortized across the batch.

This reuses the existing parser and JSON boundary. A multi-request framed loop was rejected for now because long-lived imported module state and worker recycling are unrelated to parser batching.

### Discover stable releases through the GitHub release inventory

Remote acquisition will enumerate the repository's published releases through the GitHub releases API, following pagination. Only non-draft, non-prerelease tags exactly matching `vMAJOR.MINOR.PATCH` participate. Versions are ordered by their numeric triple using minimum standard-library code; prerelease ordering is unnecessary because prereleases are excluded.

For candidates in descending order, acquisition reads the existing strict release manifest and selects the first that matches `PROTOCOL_VERSION`, `SCHEMA_VERSION`, the tag's release version, and the current target. Individual incompatible or inapplicable candidates are skipped; transport failure or exhaustion without a match returns a specific discovery failure. The selected artifact then follows the unchanged size, SHA-256, binary-identity, staging, health-check, and rollback path.

Explicit `--binary`, `ZMEM_SVC_SOURCE`, packaged binaries, and PATH remain higher precedence and never contact the inventory. Test seams inject the opener and inventory URL; the production implementation uses `urllib` and adds no dependency.

### Treat component versions as independent runtime facts

The runtime manifest keeps the Python package version as `host_version` and the service-reported version as `binary_version`; compatibility continues to require exact protocol and schema equality. The generic `release_version` field is removed in a manifest-version-2 format to avoid a misleading shared version. Status exposes both component versions. Existing manifest version 1 remains readable for stop, replacement, and upgrade, and the next successful installation writes version 2.

## Risks / Trade-offs

- [Unauthenticated GitHub API limits can block discovery] → Minimize requests by evaluating newest candidates first, surface transport/rate-limit details, and preserve explicit/local binary escape hatches.
- [A newer compatible service may contain a regression] → Installation remains explicit, upgrade keeps rollback health checks, and users can supply an explicit binary when pinning is required.
- [Mutable release inventory makes selection time-dependent] → Report the selected native version and persist it in runtime metadata so every installed runtime is auditable.
- [Manifest format migration can strand a damaged runtime] → Read both manifest versions and write only version 2 after successful staging.

## Migration Plan

Publish the protocol/schema-3 native service and its strict manifest first. Release the Python package afterward; installation discovers that native version independently of Python package version. Existing runtimes remain inspectable and replaceable, while upgrade writes manifest version 2. Rollback to the prior Python package can still stop and replace the service through its version-1-compatible reader.
