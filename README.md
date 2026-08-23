# zmem

`zmem` records structured memory in Git commit messages and queries it through the always-on `zmem-cache` backend. This is a clean-break implementation: it keeps the useful command behavior but does not promise compatibility with the original package's internals or storage.

## Install

Python 3.12 or newer is required.

```console
uv sync --locked
uv build
```

Published releases can be bootstrapped from a disposable uv environment:

```console
uvx zmem service install
uvx zmem service status
```

`uvx` obtains the Python package from the configured Python index. When no local binary source is available, `zmem service install` enumerates stable `ZackaryW/zmem-cache` GitHub Releases and chooses the greatest semantic version with an exact protocol/schema match and an artifact for the current platform. It skips drafts, prereleases, malformed tags, incompatible releases, and releases without that platform, then verifies the selected artifact's advertised size, SHA-256 digest, and native identity. The native and Python release numbers may differ. The installer copies that service and a persistent Python extension host into stable paths below `~/.zmem/runtime`, starts the copied service, and registers it for current-user startup. The active paths never contain a version:

```text
~/.zmem/runtime/
├── binary/zmem-svc[.exe]
├── host/
└── runtime.json
```

Manifest version 2 of `runtime.json` records independent `binary_version` and `host_version` values plus protocol, schema, checksum, installation, and active-path identity; it has no shared `release_version`. Version-1 manifests remain readable for replacement and upgrade. Upgrades use `.staging` and retain `.previous` until the replacement passes its health check.

Source development can select the companion Rust build explicitly:

```console
uv run zmem service install --binary ../zmem-cache/target/release/zmem-svc --no-register
```

Binary discovery checks `--binary`, `ZMEM_SVC_SOURCE`, packaged native data, then `PATH` before consulting the remote inventory. Invalid explicit and environment paths fail without falling through, and local sources never contact the inventory. Offline installations can use any local source. `ZMEM_SVC_RELEASE_INVENTORY` and `ZMEM_SVC_RELEASE_ROOT` can select explicit inventory and asset mirrors for integration or development; their defaults are the GitHub Releases API and `https://github.com/ZackaryW/zmem-cache/releases/download`. Publish the compatible native release before the Python release that selects it. `ZMEM_SVC` remains a direct development override for ordinary memory commands.

A persistent tool installation uses the same explicit service boundary:

```console
uv tool install zmem
zmem service install
```

Service management is JSON-first:

```console
zmem service install
zmem service start
zmem service status
zmem service stop
zmem service upgrade
zmem service doctor
zmem service uninstall       # keeps config, extensions, repositories, and database
```

Every service operation accepts `--home` and `--runtime-root` before its action. `ZMEM_HOME` and `ZMEM_RUNTIME_ROOT` provide the same isolation through the environment. Pass `--no-register` to install, upgrade, or uninstall for temporary integration environments. The CLI automatically registers the selected Git repository and waits for its current `HEAD` to be indexed.

## Commit annotations

Plain entries have score `1.0` by default:

```text
zmem(DECISION): use SQLite for the local cache
zmem(LESSON_LEARNT): committer time is stable history data
```

DECAY and CANCEL are actions over an earlier annotation, identified by a unique commit-prefix and its one-based zmem annotation index:

```text
zmem(DECAY)[a1b2c3d4, 1, 0.5]
zmem(CANCEL)[a1b2c3d4, 1]
```

DECAY multiplies a valid entry's score by a factor from `0.0` through `1.0`. CANCEL applies only to DECISION entries and makes the target invalid with score `0.0`. Neither action is stored as a memory entry.

META applies typed metadata changes to an inclusive commit range without creating a memory entry:

```text
zmem(META)[a1b2c3d4, e5f6a7b8, affected_areas=b/services, owner=platform, tags+=security]
zmem(META)[a1b2c3d4, e5f6a7b8, affected_areas=null]
```

The endpoints must identify a complete reachable ancestry range before the META commit. `key=value` replaces a value, `key+=value` adds one unique set member, and `key=null` resets the key. The declared keys are `affected_areas`, `owner`, and `tags`; canonical entry fields such as event, content, conventional scope, score, and validity cannot be changed. A descendant META takes precedence over an ancestor. Conflicting changes on concurrent branches remain diagnostic until a later descendant META resolves them.

## Commands

Commands emit JSON by default; add `--human` for compact terminal output.

```console
zmem recall --event DECISION --scope cache --limit 20
zmem recall --since HEAD~10
zmem recall --ref feature/payments --area b/services --area c
zmem recall --ref feature/payments --trail
zmem show a1b2c3d4 --diff-content
zmem search sqlite --ref v2.0.0 --area b --in all --include-invalid
zmem links --min-score 0.5
zmem check --file .git/COMMIT_EDITMSG
zmem check --file .git/COMMIT_EDITMSG --deep
zmem check --stdin --conventional --max-subject-length 72
zmem --commit-limit -1 --node-limit -1 check --file .git/COMMIT_EDITMSG --deep
zmem check HEAD --deep
```

Repository errors, missing commits, and service errors use distinct nonzero exit categories and structured error payloads.

Snapshot queries resolve `--ref` as a live Git commit-ish without checking it out. The client sends both the selector and its observed OID; if the ref moves before native synchronization, the query fails with a structured stale-ref error instead of returning a different snapshot. Recall, search, show, and links keep their default JSON envelopes compact by omitting the immutable selected-trail identity while retaining attention and truncation metadata. Add `--trail` to any of those commands when the requested selector, resolved HEAD, attention identity, extension identity, or protocol/schema identity is needed.

New commits receive conservative path-derived `affected_areas`. Root-level files map to `<root>`; paths within a top-level folder are reduced to their deepest common parent; rename sources and destinations both participate. Up to three compact areas are retained, while a broader blast radius becomes `null`. Repeatable `--area` filters are ORed with one another and ANDed with other filters. Parent and child areas overlap hierarchically, `<root>` matches root-level provenance, and `null` is global and always matches. Legacy database entries remain `null` until a later META patch narrows them, so upgrading does not require replaying every historical commit.

`check` treats a file or standard-input message as a hypothetical successor to the current `HEAD`. It runs active trusted expanders, skips hooks, and reports projected entries, relationships, DECAY/CANCEL effects, diagnostics, and before/after target state without persisting the hypothetical commit. Zero annotations are valid unless `--require-annotation` is supplied. `check --file <path> --deep` is the primary effect-validation path: it reconstructs the selected history in isolation before evaluating the file. A commit reference remains available for historical auditing.

Repository commands default to the newest 500 commits and 400 syntactically valid zmem annotations. Set global `--commit-limit` and `--node-limit` before the subcommand; `-1` disables that dimension. `ZMEM_COMMIT_LIMIT` and `ZMEM_NODE_LIMIT` override the defaults, while explicit flags take precedence. DECAY, CANCEL, custom, and unsupported annotations count toward node attention even when they do not become stored entries. Attention truncation is reported separately from command-local result limits such as `recall --limit 20`. A deep unresolved effect under truncated attention is reported as incomplete history; retry with larger limits or both set to `-1` when complete replay is intentional.

## Expanders and hooks

The implementation layout is intentional:

- `zmem/utils` contains reusable parsing, discovery, protocol, and output utilities.
- `zmem/ext/expander` defines behavioral expanders and `ExpansionContext`.
- `zmem/ext/hooks` defines read-only additional actions.
- `zmem/builtin` contains built-in DECISION, LESSON_LEARNT, DECAY, and CANCEL implementations.

User extensions are importable Python files under `~/.zmem/ext/expanders` or `~/.zmem/ext/hooks`. Repository extensions use `${ZMEM_CUSTOM_EXT_ROOT:-.zmem}/{extend,overwrite}/{expanders,hooks}` and require repository trust in `zmem-svc`.

An expander acts on its context and returns `None`:

```python
API_VERSION = 1


class RiskExpander:
    extension_id = "RISK"

    def expand(self, context) -> None:
        context.add_entry(type="RISK", content=context.annotation.content, score=1.0)


def register(registry, mode="extend") -> None:
    registry.extend("RISK", RiskExpander())
```

Available context actions are `add_entry`, `add_relationship`, `decay`, `cancel`, `metadata_patch`, and `diagnose`. A non-`None` return is rejected. Hooks register for `after_expand` or `after_index`, receive read-only data, and cannot mutate canonical actions. Module ordering, collision handling, and extension identities are deterministic.

## Verification

```console
uv run pytest
uv run behave features/annotation-vocabulary
uv run behave features/python-extensions
uv run behave features/memory-cli
uv run behave features/memory-metadata
uv run behave features/memory-trails
uv run behave features/commit-checking
uv run behave features/service-management
uv build
```
