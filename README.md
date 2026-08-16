# zmem

`zmem` records structured memory in Git commit messages and queries it through the always-on `zmem-cache` backend. This is a clean-break implementation: it keeps the useful command behavior but does not promise compatibility with the original package's internals or storage.

## Install

Python 3.14 or newer is required.

```console
uv sync --locked
uv build
```

Published releases can be bootstrapped from a disposable uv environment:

```console
uvx zmem service install
uvx zmem service status
```

`uvx` obtains the Python package from the configured Python index. `zmem service install` then resolves the exact same-version `ZackaryW/zmem-cache` GitHub Release, selects the current operating-system and architecture target, verifies its advertised size and SHA-256 digest, and validates the native release, protocol, and schema identity. The installer copies that service and a persistent Python extension host into stable paths below `~/.zmem/runtime`, starts the copied service, and registers it for current-user startup. The active paths never contain a version:

```text
~/.zmem/runtime/
├── binary/zmem-svc[.exe]
├── host/
└── runtime.json
```

`runtime.json` records release, binary, host, protocol, schema, checksum, installation, and active-path identity. Upgrades use `.staging` and retain `.previous` until the replacement passes its health check.

Source development can select the companion Rust build explicitly:

```console
uv run zmem service install --binary ../zmem-cache/target/release/zmem-svc --no-register
```

Binary discovery checks `--binary`, `ZMEM_SVC_SOURCE`, packaged native data, then `PATH` before consulting the remote release. Invalid explicit and environment paths fail without falling through. Offline installations can use any of those local sources. `ZMEM_SVC_RELEASE_ROOT` can select an explicit release mirror for integration or development; the default is `https://github.com/ZackaryW/zmem-cache/releases/download`. `ZMEM_SVC` remains a direct development override for ordinary memory commands.

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

## Commands

Commands emit JSON by default; add `--human` for compact terminal output.

```console
zmem recall --event DECISION --scope cache --limit 20
zmem recall --since HEAD~10
zmem show a1b2c3d4 --diff-content
zmem search sqlite --in all --include-invalid
zmem links --min-score 0.5
zmem check --file .git/COMMIT_EDITMSG
zmem check --file .git/COMMIT_EDITMSG --deep
zmem check --stdin --conventional --max-subject-length 72
zmem --commit-limit -1 --node-limit -1 check --file .git/COMMIT_EDITMSG --deep
zmem check HEAD --deep
```

Repository errors, missing commits, and service errors use distinct nonzero exit categories and structured error payloads.

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

Available context actions are `add_entry`, `add_relationship`, `decay`, `cancel`, and `diagnose`. A non-`None` return is rejected. Hooks register for `after_expand` or `after_index`, receive read-only data, and cannot mutate canonical actions. Module ordering, collision handling, and extension identities are deterministic.

## Verification

```console
uv run pytest
uv run behave features/annotation-vocabulary
uv run behave features/python-extensions
uv run behave features/memory-cli
uv run behave features/commit-checking
uv run behave features/service-management
uv build
```
