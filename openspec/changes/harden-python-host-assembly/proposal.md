## Why

Managed service installation currently constructs its persistent Python extension host with `venv.EnvBuilder`'s direct-call copy default. On POSIX, that differs from the platform's normal symlink-based `python -m venv` behavior and can make a supported dynamically linked interpreter abort before the runtime is activated; the failure also leaks an incomplete staging directory and exposes a raw subprocess error.

## What Changes

- Assemble the persistent extension host with the platform's normal virtual-environment executable strategy: symlinks on POSIX and native copy/launcher behavior on Windows.
- Treat host creation and its interpreter probe as transactional staging work, removing the incomplete installation-specific staging directory on failure without changing an active runtime.
- Report an actionable service-management error when the staged interpreter cannot run, including whether it exited or was terminated by a known signal.
- Preserve interpreter selection at the invoking environment boundary, including uv's existing `--python` selection; do not add a separate zmem host-interpreter option.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `service-management`: Require supported Python environments to assemble a usable persistent host with platform-appropriate venv semantics, and require failed host assembly to clean its partial staging work and return a meaningful nonzero failure.

## Impact

- Affects runtime host assembly and installation error translation in `src/zmem/utils/runtime.py` and `src/zmem/service.py`.
- Extends focused runtime/service unit coverage and the existing public service-management installation feature surface.
- Adds no dependency, command-line option, manifest field, protocol change, or native-service change.
