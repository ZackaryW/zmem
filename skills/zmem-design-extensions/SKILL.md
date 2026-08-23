---
name: zmem-design-extensions
description: Design, implement, and verify zmem Python expanders and hooks using ExpansionContext, HookRegistry, extension discovery, trust, extend, and overwrite contracts. Use when an agent needs a new annotation type, entry, relationship, typed metadata patch, diagnostic, read-only observer, or controlled override of built-in behavior.
---

# Design zmem Extensions

Choose the correct extension boundary, keep behavior explicit, and prove it through the public indexing path.

Read [references/extension-api.md](references/extension-api.md) before proposing or implementing an extension.

## Choose the Boundary

- Use an **expander** when an annotation must add an entry or relationship, decay or cancel a target, apply a typed metadata patch, or emit a canonical diagnostic.
- Use a **hook** for an additional read-only action after expansion or indexing. Hooks observe copied context and must not change canonical zmem results.
- Change zmem core only when the required behavior cannot be expressed by either public extension contract.

An expander performs actions over `ExpansionContext` and returns `None`. Never design it to return a dict or another result payload.

## Workflow

1. State the user-visible behavior, annotation grammar, stable uppercase extension ID, accepted inputs, score or metadata rules, diagnostics, and failure behavior.
2. Confirm whether the extension is global or repository-local, whether repository code is trusted, and whether registration extends or overwrites behavior.
3. Reuse the public context and registry APIs. Do not write directly to the SQLite store or service journal.
4. Keep execution deterministic and bounded. Make hook side effects idempotent where practical, and require explicit acceptance before adding network or sensitive-data behavior.
5. Validate inputs before emitting actions. Diagnose unsupported content rather than silently inventing semantics.
6. Add unit case matrices for parsing, validation, action selection, and error isolation.
7. Retain one independently runnable Behave scenario through the public indexing boundary when needed to prove discovery, trust, layering, or effect behavior. Keep bindings thin and use the established capability-owned feature root.
8. Prove the relevant failure first, implement the smallest coherent slice, then run focused and complete repository gates.
9. Exercise a sample commit and inspect the selected trail's entries, effects, metadata, relationships, and diagnostics.

## Review Checklist

- The expander mutates only through context actions and returns `None`.
- The hook returns `None` and does not create canonical entries or effects.
- Registration honors `extend` versus `overwrite` mode.
- Repository-local Python executes only after explicit extension trust.
- Scores and decay factors remain within `0.0..1.0`.
- Metadata patches use declared keys and typed operations, resolve a complete ancestry range, and never rewrite canonical entry fields.
- Duplicate IDs, missing overwrite targets, callback exceptions, and invalid annotations produce stable diagnostics.
- Tests cover discovery order and layering when those behaviors are changed.
