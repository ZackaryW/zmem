## Context

The native query service must select and synchronize an immutable trail before it can answer a snapshot query, and the Python client needs the returned trail internally for correct filtering. The public CLI currently serializes that entire identity for every snapshot command. In the reported zero-result search, the useful envelope was dominated by long `attention_identity`, `extension_identity`, `resolved_oid`, and `trail_id` values even though attention and truncation already communicated the actionable limitation. Recall, show, and links use the same envelope path and carry the same presentation defect.

The repository's executable authority belongs in the existing `memory-cli` Behave feature. Shared setup and command execution remain in `features/support/lifecycle.py`, with only capability declarations and established step bindings changed.

## Goals / Non-Goals

**Goals:**

- Keep default snapshot output focused on results, attention, and truncation.
- Preserve exact existing trail data behind an explicit option on every snapshot command.
- Keep snapshot selection, result fields, filtering, and native protocol unchanged.
- Prefer a bounded recent recall pass in agent memory retrieval before narrower text search.

**Non-Goals:**

- Removing entry `sha` or annotation `index` provenance from search results.
- Changing attention defaults or diagnosing why a particular query reaches them.
- Changing output from check or service-management commands.
- Addressing duplicate process output without a repository reproduction.

## Decisions

### Gate only public snapshot serialization

The CLI continues to observe a ref, query the service, decode the typed trail, and use its resolved OID exactly as today. Only the `trail` argument passed to each final snapshot envelope is conditional. The parser exposes the same `--trail` spelling on recall, search, show, and links. This keeps the correction at the public composition boundary and avoids changing shared envelope utilities or the native protocol.

Alternative: strip identity fields in the native service or client. Rejected because downstream commands and branch-aware filtering require that typed identity, and the defect concerns default presentation rather than selection.

### Use command-local `--trail` as the explicit opt-in

`--trail` names the exact omitted object and restores it without transformation. Repeating it on each snapshot parser preserves the established post-subcommand option style and avoids implying that entry-level identifiers are hidden.

Alternative: use `--ids` and hide entry `sha`/`index` too. Rejected after the supplied zero-result evidence isolated the burden to the envelope trail and because entry identity is required to author DECAY/CANCEL effects.

### Retain attention metadata by default

The compact `attention` object and top-level `truncated` remain visible. They tell an agent that a zero-result search may be incomplete and what limit was reached; hiding them would make the smaller response misleading.

### Recall recent context before topical search in the query skill

The memory-query workflow starts with valid memory reachable since `HEAD~50`, then ranks that recent context before using literal or regex search for a narrower unresolved topic. The boundary limits Git history rather than prematurely applying a small result limit, so the skill can still rank all memories produced in those commits. Search remains available for focused retrieval and for broadening when the recent pass is weak.

## Risks / Trade-offs

- Existing consumers may assume every snapshot envelope contains `trail` → Document the snapshot-wide change and the `--trail` migration.
- A user may need the selected OID while debugging a query → Preserve the complete existing object under `--trail`, including on empty results.
- Human and JSON output could diverge → Drive both through the same conditional envelope and assert the public JSON behavior through Behave.

## Migration Plan

Consumers that inspect snapshot response trail fields add `--trail` to recall, search, show, or links as applicable. Rollback is limited to CLI serialization gates plus documentation/specification changes; no stored data or service migration is required.

## Open Questions

None.
