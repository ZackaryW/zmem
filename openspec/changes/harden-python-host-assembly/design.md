## Context

The managed runtime creates a persistent, pip-free virtual environment and copies the zmem package into its `purelib` directory. `assemble_host` calls `venv.EnvBuilder` directly without selecting its executable strategy. The direct API defaults to copies on every platform, while the standard POSIX `python -m venv` entry point defaults to symlinks. A dynamically linked pyenv interpreter can therefore be copied away from the library layout it needs and abort during zmem's first `sysconfig` probe.

Host assembly occurs after an installation-specific staging directory and native binary have been created but before activation. Today a probe exception escapes as raw subprocess text and leaves that partial staging directory behind. The active runtime is not yet switched, but `service doctor` subsequently reports the abandoned staging work.

## Goals / Non-Goals

**Goals:**

- Make host creation follow normal platform venv executable semantics for every supported Python interpreter.
- Preserve the active runtime when any pre-activation host assembly step fails.
- Remove only the failed installation's staging directory.
- Translate interpreter exit and signal failures into actionable service-management diagnostics.
- Prove platform selection, signal formatting, staging cleanup, and service-boundary translation with focused unit tests while retaining the existing public installation scenario.

**Non-Goals:**

- Adding `--host-python`, `ZMEM_HOST_PYTHON`, or another interpreter-selection policy to zmem.
- Bundling CPython, making virtual environments independent of their base Python installation, or changing uv/pyenv lifecycle behavior.
- Changing active runtime paths, metadata, the native protocol, startup registration, or release acquisition.
- Adding an external environment-management dependency.

## Decisions

### Match the native venv executable strategy

Construct `EnvBuilder` with symlinks enabled when `os.name != "nt"` and disabled on Windows. This matches `python -m venv` defaults, keeps Windows launcher/copy handling intact, and fixes the POSIX relocation failure with the existing standard library. Calling a separate `python -m venv` process was rejected because zmem already owns the in-process builder and needs no second orchestration path. Adding virtualenv or another package was rejected under the dependency ladder because the standard library provides the required behavior.

### Diagnose the host probe at its utility boundary

Keep the `sysconfig.get_path("purelib")` probe, but translate `CalledProcessError` into a runtime-assembly error that distinguishes a negative return code (known signal name and number) from a normal nonzero exit and retains non-empty stderr detail. This keeps subprocess mechanics out of the public CLI while giving the service layer stable, actionable context.

### Make one installation-specific stage transactional

Wrap construction of the staged binary, host, and manifest in one failure boundary inside `stage_runtime`. On failure, remove only that generated installation root and re-raise. Do not clear the shared `.staging` parent because it can also contain other installation or release-acquisition work.

### Translate assembly failure at the service boundary

Catch expected runtime-assembly failures around `stage_runtime` before daemon stop or activation and raise `ServiceManagementError` with a managed-runtime assembly prefix. The CLI already maps that public error category to structured JSON and exit category 4. Programming errors remain uncaught.

## Risks / Trade-offs

- [A POSIX host symlink still depends on the selected base Python remaining installed] → This is already true for standard virtual environments through `pyvenv.cfg`; document no stronger portability promise and retain uv's explicit interpreter selection.
- [Symlink creation can fail on an unusual POSIX filesystem] → `venv` falls back to copying with a warning; the executable probe then accepts a usable fallback or returns the actionable failure.
- [Over-broad cleanup could remove unrelated staging work] → Cleanup is scoped to the generated UUID installation root only.
- [Signal names vary by platform] → Resolve known signal numbers through the standard-library `signal.Signals` enum and retain the numeric signal when no symbolic name exists.

## Migration Plan

No metadata or data migration is required. Existing healthy runtimes continue unchanged; a later install or upgrade builds the next host with the corrected strategy. Rollback reverts the Python package change and does not alter an already active runtime.

## Open Questions

None.
