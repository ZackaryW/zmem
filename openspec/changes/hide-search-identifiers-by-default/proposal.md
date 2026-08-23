## Why

Default `zmem search` responses expose the full immutable-trail identity even when an agent only needs relevant memory content. The trail block dominates even an empty response with long attention, extension, commit, and composite trail identifiers, consuming context unless the selected trail is explicitly being audited.

## What Changes

- Omit the selected-trail identity block from default `search` output.
- Add an explicit `search --trail` option that restores the existing complete trail identity shape.
- Preserve search filtering, validity, attention, truncation, and all other query commands unchanged.
- Preserve entry-level `sha` and annotation `index` provenance so matching memories remain actionable effect targets.
- **BREAKING**: consumers that currently read `trail` from an unqualified `search` response must request `--trail`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `memory-cli`: Change the default search envelope and add explicit selected-trail inclusion.

## Impact

The public Python CLI composition in `src/zmem/cli.py`, memory CLI Behave authority and bindings, focused output tests, README query guidance, the memory-query skill contract, and the canonical `memory-cli` specification are affected. The native service protocol, attention metadata, and stored entry identity remain unchanged.
