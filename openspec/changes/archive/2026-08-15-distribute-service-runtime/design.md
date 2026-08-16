## Context

The existing runtime assembler already stages a binary and persistent Python host, validates `version-json`, checks protocol compatibility, activates stable paths, and rolls back unhealthy replacements. The missing seam is acquisition of a native binary when local discovery reaches the end of its precedence chain. See the proposal and `service-management` delta for the accepted boundary.

## Goals / Non-Goals

**Goals:**

- Make the default install path deterministic for PyPI and `uvx` consumers.
- Keep all downloaded bytes outside active runtime paths until integrity and identity checks pass.
- Keep platform selection independently testable and error messages actionable.

**Non-Goals:**

- Running service registration as a Python package post-install hook.
- Selecting the newest compatible service independently of the Python package version.
- Providing an alternate package index or a general-purpose artifact downloader.

## Decisions

### Pin service releases to the Python package version

Package version `N` reads `ZackaryW/zmem-cache` release tag `vN`; it never follows `latest`. This makes reinstall and rollback deterministic. Protocol and schema identity remain separate compatibility checks rather than version-selection inputs.

### Preserve local discovery as the complete precedence chain

Resolution remains `--binary`, `ZMEM_SVC_SOURCE`, packaged `_native`, and `PATH`, followed by the remote release. An invalid explicit or environment source is an error and does not fall through. Remote resolution is therefore a default acquisition path, not an override.

### Map platform aliases to Rust targets before reading the manifest

The resolver normalizes Python operating-system and machine values to these targets:

| Operating system | Machine aliases | Release target |
|---|---|---|
| Windows | `AMD64`, `x86_64` | `x86_64-pc-windows-msvc` |
| Windows | `ARM64`, `aarch64` | `aarch64-pc-windows-msvc` |
| Windows | `x86`, `i386`, `i686` | `i686-pc-windows-msvc` |
| macOS | `x86_64`, `AMD64` | `x86_64-apple-darwin` |
| macOS | `arm64`, `aarch64` | `aarch64-apple-darwin` |
| Linux | `x86_64`, `AMD64` | `x86_64-unknown-linux-musl` |
| Linux | `arm64`, `aarch64` | `aarch64-unknown-linux-musl` |

Static musl Linux artifacts avoid a runtime libc branch. Unknown pairs fail before an asset request.

### Use one strict typed manifest

`release-manifest.json` contains `manifest_version`, release/protocol/schema versions, and a list of assets with exact `target`, `name`, `size`, and lowercase SHA-256 fields. Unknown or ill-typed fields, duplicate targets, an unexpected release, unsafe asset names, and unadvertised targets are rejected. The default release root is GitHub HTTPS; `ZMEM_SVC_RELEASE_ROOT` provides an explicit integration/development mirror.

### Reuse transactional activation

The downloader streams the selected asset into a temporary path beneath `runtime/.staging`, enforces the advertised size while hashing, and passes the verified path to the existing assembler. The temporary acquisition is removed after success or failure. Existing native identity, health check, activation, and rollback logic remains authoritative.

## Risks / Trade-offs

- [The two repositories can be tagged inconsistently] → release generation rejects tag/version/identity disagreement, and the client rejects a mismatched manifest.
- [Checksums published beside artifacts do not protect a compromised GitHub release] → keep the repository release permission minimal and leave signed provenance as a future hardening layer.
- [A supported Python platform may lack a release target] → fail before artifact download with the normalized OS/machine pair and publish only explicitly tested targets.
- [Network installation is unavailable offline] → preserve every existing local and packaged source ahead of remote acquisition.

## Migration Plan

1. Merge and tag the coordinated `zmem-cache` release first so the exact-version manifest exists.
2. Publish the same-version Python `zmem` distribution.
3. Roll back by withdrawing the Python release or publishing a corrected coordinated patch version; already active runtimes remain usable.
