## Why

Installing the Python CLI does not currently make a native `zmem-svc` artifact available, so users cannot bootstrap the managed service without building Rust or supplying a local binary. Tagged, version-matched service releases let disposable `uvx` and persistent `uv tool` environments install the correct verified runtime on supported platforms.

## What Changes

- Extend `zmem service install` and `upgrade` to resolve the exact same-version `ZackaryW/zmem-cache` GitHub release when no higher-precedence local binary source exists.
- Parse the current operating system and architecture into the supported Rust release target and select that target from a typed release manifest.
- Download through transactional runtime staging, verify the advertised byte length and SHA-256 digest, and retain the existing native identity and protocol checks before activation.
- Preserve precedence for `--binary`, `ZMEM_SVC_SOURCE`, packaged native data, and `PATH`.
- Keep service registration explicit: `uv tool install zmem` installs the Python tool; `zmem service install` downloads and registers the service, while `uvx zmem service install` performs a disposable bootstrap.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `service-management`: Allow managed service installation and upgrade to acquire an exact-version, platform-specific native artifact from a verified release manifest.

## Impact

- Affects service runtime resolution, download validation, command diagnostics, and service-management behavior tests.
- Uses Python standard-library platform, HTTP, hashing, and temporary-file support; no runtime dependency is added.
- Depends on the coordinated `zmem-cache` release contract and GitHub Release asset names.
