## Why

Default zmem snapshot-query responses expose the full immutable-trail identity even when an agent only needs relevant memory content. The trail block dominates even an empty response with long attention, extension, commit, and composite trail identifiers, consuming context unless the selected trail is explicitly being audited.

## What Changes

- Omit the selected-trail identity block from default `recall`, `search`, `show`, and `links` output.
- Add an explicit `--trail` option to each snapshot command that restores the existing complete trail identity shape.
- Preserve filtering, validity, attention, truncation, snapshot selection, and result fields unchanged.
- Preserve entry-level `sha` and annotation `index` provenance so matching memories remain actionable effect targets.
- Make the repository memory-query skill prefer a recent `recall --since HEAD~50` context pass before topical search, and request trail identity only for provenance work.
- **BREAKING**: consumers that currently read `trail` from an unqualified snapshot response must request `--trail`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `memory-cli`: Change default snapshot-query envelopes and add explicit selected-trail inclusion.

## Impact

The public Python CLI composition in `src/zmem/cli.py`, memory CLI Behave authority and bindings, focused output tests, README query guidance, and repository `zmem-query-memory` skill are affected. The native service protocol, attention metadata, and stored entry identity remain unchanged.
