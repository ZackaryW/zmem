## Context

See `proposal.md` for motivation and the three capability specs for behavior. The repository is a Python 3.14 skeleton, while all durable Git indexing and SQLite writes belong to the coordinated Rust service. Legacy zmem proves useful command shapes and an internal expander idea but exposes no stable plugin API.

## Goals / Non-Goals

**Goals:**

- Keep the Python package responsible for the CLI, annotation vocabulary, extension contracts, and Python extension execution.
- Preserve one deterministic representation across the local protocol.
- Make trusted extension loading inspectable and rebuild-safe.
- Follow the established package ownership: `zmem/utils`, `zmem/ext/expander`, `zmem/ext/hooks`, and `zmem/builtin`.

**Non-Goals:**

- Reuse the legacy graph, pickle format, or Python dependency stack.
- Let hooks mutate canonical index state.
- Let Python processes open the service database.
- Provide a PyO3 binding before an in-process consumer is demonstrated.

## Decisions

### Keep zmem as Python client and extension host

The package remains pure Python and communicates with `zmem-svc` over a versioned local JSON protocol. A dedicated extension-host entry point loads Python modules, constructs an `ExpansionContext` for each annotation, executes expanders against that context, and serializes the context's completed action journal to the service. This avoids embedding and distributing CPython inside the Rust daemon. A future read-only PyO3 module may reuse the Rust core without becoming a second database owner.

### Separate parsing, expansion, and hooks

A small parser under `zmem/utils` recognizes annotation syntax and produces immutable annotation inputs. Classes under `zmem/ext/expander` define deterministic behavioral contracts whose `expand(context) -> None` method invokes explicit context actions. Classes under `zmem/ext/hooks` define read-only lifecycle observations. Built-in implementations live under `zmem/builtin`, including the shared text behavior plus DECAY and CANCEL.

`ExpansionContext` exposes immutable annotation, commit, and repository facts plus controlled actions: `add_entry`, `add_relationship`, `decay`, `cancel`, and `diagnose`. The actions append validated typed records to a private journal; they do not access SQLite. DECAY and CANCEL therefore read as behavior (`context.decay(...)`, `context.cancel(...)`) rather than serializers. `HookContext` omits canonical action methods.

### Serialize the context action journal at the process boundary

Requests include repository identity, commit context, annotation order, trust state, and extension roots. After every expander has acted, the host serializes the private journal as typed entry, relationship, decay, cancel, and diagnostic actions plus hook outcomes, protocol version, and the extension-set hash. Expanders never return dictionaries or construct wire records. Plain internal dataclasses keep the boundary testable without sharing Python objects or granting Python database access.

### Make loader precedence explicit

Built-ins load first, then global additions, then repository `extend`, then repository `overwrite`. Extend collisions and ambiguous overwrites are errors. Files are normalized and sorted before import; module bytes and API metadata feed the extension-set hash. Global modules are trusted by ownership. Repository modules require stored trust granted during registration.

### Keep public command rendering centralized

All commands use one client, one envelope builder, and one error mapping. Pure filtering and rendering matrices remain unit tested; capability BDD roots prove representative behavior through the installed console entry point and a controllable service boundary.

## Risks / Trade-offs

- [Repository Python can execute arbitrary code] → Never import it without explicit persisted trust and show the selected root in diagnostics.
- [Hooks create nondeterministic side effects] → Exclude their output from canonical state and report failures separately.
- [Extension protocol drifts between repositories] → Version every exchange and test shared fixtures from both sides.
- [Context actions could be mistaken for direct database mutations] → Keep the journal private, expose behavior-named methods, and retain validation and application authority in Rust.
- [A pure-Python package duplicates core models] → Share only action-schema fixtures; keep Git, storage, and effect authority in Rust.

## Migration Plan

This is a clean-break repository. Build the new capabilities behind the new service protocol, verify them together, and publish/install the Python client only with a compatible `zmem-svc`. Rollback removes the new client/service installation and database; no legacy data migration is promised.
