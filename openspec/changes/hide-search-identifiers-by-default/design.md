## Context

The native query service must select and synchronize an immutable trail before it can search, and the Python client needs the returned trail internally for correct filtering. The public CLI currently serializes that entire identity for every snapshot command. In the reported zero-result search, the useful envelope was dominated by long `attention_identity`, `extension_identity`, `resolved_oid`, and `trail_id` values even though attention and truncation already communicated the actionable limitation.

The repository's executable authority belongs in the existing `memory-cli` Behave feature. Shared setup and command execution remain in `features/support/lifecycle.py`, with only capability declarations and established step bindings changed.

## Goals / Non-Goals

**Goals:**

- Keep default search output focused on matches, attention, and truncation.
- Preserve exact existing trail data behind an explicit search option.
- Keep snapshot selection, result fields, filtering, and native protocol unchanged.

**Non-Goals:**

- Changing output from recall, show, links, or check.
- Removing entry `sha` or annotation `index` provenance from search results.
- Changing attention defaults or diagnosing why a particular query reaches them.
- Addressing duplicate process output without a repository reproduction.

## Decisions

### Gate only public search serialization

The CLI continues to observe a ref, query the service, decode the typed trail, and use its resolved OID exactly as today. Only the `trail` argument passed to the final search envelope is conditional. This keeps the correction at the public composition boundary and avoids changing shared envelope utilities or the native protocol.

Alternative: strip identity fields in the native service or client. Rejected because downstream commands and branch-aware filtering require that typed identity, and the defect concerns default presentation rather than selection.

### Use `search --trail` as the explicit opt-in

`--trail` names the exact omitted object and restores it without transformation. It is narrower and more discoverable than a generic verbose or debug mode, and it does not imply that entry-level identifiers are hidden.

Alternative: use `--ids` and hide entry `sha`/`index` too. Rejected after the supplied zero-result evidence isolated the burden to the envelope trail and because entry identity is required to author DECAY/CANCEL effects.

### Retain attention metadata by default

The compact `attention` object and top-level `truncated` remain visible. They tell an agent that a zero-result search may be incomplete and what limit was reached; hiding them would make the smaller response misleading.

## Risks / Trade-offs

- Existing consumers may assume every snapshot envelope contains `trail` → Document the breaking search-only change and the `--trail` migration.
- A user may need the selected OID while debugging a search → Preserve the complete existing object under `--trail`, including on empty results.
- Human and JSON output could diverge → Drive both through the same conditional envelope and assert the public JSON behavior through Behave.

## Migration Plan

Consumers that inspect `search` response trail fields add `--trail`. Rollback is the single CLI serialization gate plus its documentation/specification changes; no stored data or service migration is required.

## Open Questions

None.
