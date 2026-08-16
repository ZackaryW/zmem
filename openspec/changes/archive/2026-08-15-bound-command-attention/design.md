## Context

The Python CLI currently sends repository requests without a work budget, applies `--limit` only after query rows are materialized, and documents historical-ref deep checking more prominently than proposed-file replay. The native service owns Git traversal and persistence, while the Python host owns canonical annotation parsing and extension expansion. See `proposal.md` and the capability deltas for the accepted public contract.

## Goals / Non-Goals

**Goals:**

- Resolve one immutable attention policy at the CLI boundary and carry it through every repository service request.
- Keep command-local result limits source-compatible and distinguish them from history/node attention.
- Give agents stable structured evidence of the effective policy, observed usage, and incomplete attention.
- Prove the exact `zmem --commit-limit ... --node-limit ... check --file ... --deep` path through the public CLI.

**Non-Goals:**

- Limiting one-object `show` resolution, local service-management work, extension action fan-out, or ordinary commit-message prose.
- Reintroducing the old reference's day-based decay bound.
- Treating an explicit `-1` request as safe for adversarial history; it is a deliberate caller opt-out.

## Decisions

### Resolve attention once, with explicit provenance

A small `zmem.utils.attention` value object will validate built-in defaults, environment values, and optional CLI values. Resolution order is CLI, environment, built-in independently per dimension. Values are positive integers or `-1`; explicit malformed values fail. The client sends both effective values on repository requests and composes returned native attention metadata into every JSON envelope.

This is preferred over allowing the daemon to infer the invoking process's environment, which may differ for an already-running user service.

### Keep attention options global and result limits local

`--commit-limit` and `--node-limit` belong to the root parser and therefore precede the command. Existing `recall --limit` and `search --limit` remain result caps after the subcommand. Documentation and errors will show both positions explicitly.

This avoids changing the established meaning of command-local `--limit` while making attention policy consistent across repository commands.

### Let the native result own traversal truth

Python will not independently estimate truncation. The native response will supply effective limits, observed commits and nodes, truncation, and reached-bound reasons. Query envelopes combine native attention truncation with local result truncation, and check maps inconclusive attention to its validation exit category while preserving preview detail.

This avoids divergent Python/Rust interpretations of the selected history.

### Count through the canonical Python parser before expansion

The host protocol will expose annotation-only inspection that reuses the normal message parser without loading expanders or running hooks. The native service can reserve proposed-message nodes and select whole historical commits before invoking expansion on the chosen replay set. Unsupported annotations still count because counting precedes extension lookup.

This is preferred over duplicating annotation grammar in Rust or counting expansion actions, either of which would drift from hookable parser semantics.

## Risks / Trade-offs

- [Global options must precede subcommands under argparse] → Examples and validation messages will show the canonical ordering, and BDD will exercise it.
- [Two host passes add work for selected commits] → Inspection is parser-only, history is commit-bounded by default, and expansion remains concurrency-bounded.
- [An extension can emit many actions from one annotation] → Node attention intentionally counts source annotations; journal validation and cache capacity remain separate safeguards.
- [An incomplete effect can look like an ordinary missing target] → Native attention metadata upgrades unresolved effects to an explicit incomplete-history diagnostic whenever older reachable history was omitted.

## Migration Plan

Release the Python client together with the protocol-compatible native service. Existing command-local `--limit` usage remains valid. Users requiring former complete-history behavior set both global attention options to `-1` or export both corresponding environment variables. Rollback requires restoring the matching prior Python/native protocol pair.
