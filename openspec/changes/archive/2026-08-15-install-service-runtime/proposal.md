## Why

`uvx` is a convenient zmem entry point, but its cached environment is disposable and must not become the lifetime owner of the always-on cache service. The Python package needs a public management surface that assembles a stable runtime, registers it for the current user, and remains safe to exercise in temporary paths.

## What Changes

- Add `zmem service install`, `start`, `status`, `stop`, `upgrade`, `uninstall`, and `doctor` commands.
- Assemble the native service binary under `~/.zmem/runtime/binary/` and a persistent Python extension host under `~/.zmem/runtime/host/`.
- Record typed release, binary, host, protocol, schema, checksum, and installation metadata in the sibling `~/.zmem/runtime/runtime.json` file rather than encoding versions in active paths.
- Stage and validate replacements before switching, retain one previous runtime for health-checked rollback, and keep user data by default during uninstall.
- Support explicit temporary zmem-home and runtime-root paths without touching the real user runtime or platform registration.
- Keep `uvx` as bootstrapper and client while the installed runtime owns daemon lifetime.
- Preserve the useful legacy `recall`, `show`, `search`, and `links` behavior; DECAY and CANCEL remain intentional additions rather than legacy compatibility requirements.

## Capabilities

### New Capabilities

- `service-management`: Public service installation, lifecycle, diagnostics, upgrade, rollback, metadata, and isolated-root behavior.

### Modified Capabilities

None.

## Impact

- Affects the Python command surface, service client discovery, runtime assembly, subprocess handling, packaged native-binary discovery, and platform registration adapters.
- Coordinates with the Rust `install-service-runtime` change for service handshake and lifecycle primitives.
- Uses the legacy `C:\Users\ZackaryWang\Documents\GitHub\zmem` repository only as later end-to-end behavioral evidence; its graph, pickle cache, and expander internals are not compatibility contracts.
