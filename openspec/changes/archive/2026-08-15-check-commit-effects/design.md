## Context

See `proposal.md` and `specs/commit-checking/spec.md`. The Python client currently exposes query commands and launches `zmem-svc` as a subprocess. Annotation expansion is owned by the Python host, while stateful effect resolution belongs to the Rust service. Hooks are explicitly allowed external side effects, so a preview cannot use the ordinary hook path.

## Goals / Non-Goals

**Goals:**

- Give agents, users, and commit hooks one JSON-first semantic validator.
- Keep message-policy checks local and deterministic while delegating projected state to the service.
- Preserve mixed ordinary and annotated commit prose.
- Make fast and deep modes visibly distinct.

**Non-Goals:**

- Installing a Git hook automatically.
- Changing the separate ZPP validator or repository.
- Granting repository-extension trust.
- Running external-side-effect hooks during preview.

## Decisions

### Add one `check` command with explicit input modes

`check --file PATH` and `check --stdin` evaluate a proposed successor. A positional Git reference is accepted only with `--deep`; combining a ref with file or stdin is invalid. `--deep` also composes with a proposed input. This keeps shell quoting out of the primary interface and prevents accidental reinterpretation of an existing effect against current post-effect state.

Alternative: accept arbitrary message text as an option. Rejected because multiline shell quoting is inconsistent across supported platforms.

### Separate local policy diagnostics from service semantics

A new utility validates nonempty subject, optional conventional shape, optional positive maximum subject length, and optional annotation presence. The CLI still requests semantic preview so policy and annotation diagnostics can be returned together. The CLI marks the combined result unsuccessful if either layer reports a validation diagnostic.

Alternative: make conventional commits mandatory. Rejected because zmem already supports scope-less Git history and ordinary messages.

### Extend the service client instead of duplicating effect logic

The Python client invokes a new native `zmem-svc check` operation with message/ref, deep mode, and hook suppression. Returned native fields are passed through a stable JSON check response. Stateful resolution remains solely in Rust.

Alternative: query entries and simulate effects in Python. Rejected because it would duplicate ambiguity, reachability, ordering, and cancellation rules.

### Make hook suppression part of the host protocol

Indexing continues to run both hook events. Check expansion supplies an explicit false hook-execution flag; the host runs expanders and journals their canonical actions but skips both hook phases and reports `hooks: "skipped"`.

### Update the authoring skill after the command is green

The skill will require `zmem check` for any proposed annotated message and recommend `--deep` when an effect target is absent from the rolling cache or when auditing an existing commit.

## Risks / Trade-offs

- [Trusted expanders remain arbitrary Python] → Reuse the existing explicit repository trust boundary and document that check executes active expanders.
- [Fast results can differ from full Git history after eviction] → Make mode explicit and provide deep isolated replay.
- [Python and native package versions can drift] → Treat an unsupported service check operation as an actionable compatibility error.
- [Large histories make deep checking expensive] → Keep deep mode explicit and stream only bounded structured output back to the client.

## Migration Plan

1. Release the compatible service operation and Python client command together.
2. Keep all existing query and indexing commands unchanged.
3. If deployment is rolled back, the unknown command fails without altering stored state; no schema rollback is required.
