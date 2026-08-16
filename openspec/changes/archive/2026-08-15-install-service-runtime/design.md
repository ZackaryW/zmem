## Context

See `proposal.md`. The current Python client locates `zmem-svc` on PATH and launches it for each request. That works during source development but allows an `uvx` cache path to leak into daemon and extension-host lifetime.

## Goals / Non-Goals

**Goals:**

- Make `uvx zmem service install` produce a self-contained stable runtime without network access after zmem itself is running.
- Keep active paths fixed across upgrades and expose exact identity through typed metadata.
- Make every mutation testable beneath explicit temporary roots.
- Keep platform integration behind small standard-library adapters.

**Non-Goals:**

- Embed CPython into Rust or turn zmem into a PyO3 package.
- Promise compatibility with the legacy graph, pickle data, or extension classes.
- Remove `ZMEM_SVC` and PATH fallbacks used for source development.
- Delete user data during ordinary uninstall.

## Decisions

### Copy the installed pure-Python package into a persistent host environment

Installation creates a standard-library virtual environment without pip, copies the currently running `zmem` package into its site-packages, and invokes that environment as `python -m zmem.host`. This avoids registry access and prevents the host from depending on the disposable `uvx` environment. Alternatives were an embedded interpreter, which increases native packaging complexity, and a second registry install, which adds network and resolver failure modes.

### Discover a native binary through an explicit ladder

The installer uses an explicit command argument first, then `ZMEM_SVC_SOURCE`, then a packaged platform binary, then a PATH executable. The selected file is copied and checksummed before execution. Release wheels can carry the platform binary without making Rust a Python extension.

### Keep the active layout single-slot with transactional side slots

`runtime/binary`, `runtime/host`, and `runtime.json` are the only active locations. Assembly happens in `runtime/.staging/<installation-id>` and the displaced runtime moves to `runtime/.previous`. Metadata is written to a temporary file and renamed. Version-named active directories were rejected because they leak upgrade state into service registration paths.

### Make roots explicit and registration optional

Path resolution accepts CLI overrides and the `ZMEM_HOME`/`ZMEM_RUNTIME_ROOT` environment variables. An explicit no-registration mode is mandatory for integration tests and portable temporary use. Registration adapters emit and invoke only native per-user definitions: Scheduled Tasks on Windows, LaunchAgents on macOS, and systemd user units on Linux.

### Keep bindings and compatibility evidence at public boundaries

One `features/service-management/` root invokes the installed `zmem` entry point. Pure manifest, path, checksum, command-generation, and swap matrices remain unit tests. A later end-to-end audit targets the legacy repository and compares the established recall/show/search/links envelopes while allowing DECAY and CANCEL only in the new implementation.

## Risks / Trade-offs

- [Copying an import package omits third-party dependencies added later] → Record host composition in metadata and fail doctor checks for unresolved imports; revisit wheel installation if zmem gains runtime dependencies.
- [Windows cannot replace a running executable] → Stop and verify daemon exit before moving active paths.
- [A failed process can leave staging or previous paths] → Make recovery idempotent and let doctor identify and clean only recognized runtime-owned remnants.
- [Native startup tools vary or may be unavailable] → Fail registration explicitly while leaving the assembled runtime recoverable and manually startable.

## Migration Plan

First installation stages and validates the runtime, registers it unless disabled, starts it, and verifies protocol health. Upgrade follows the same path but retains one previous runtime and restores it on failure. Uninstall removes registration and runtime artifacts while leaving all non-runtime files under the zmem home unless a separate destructive option is explicitly supplied.
