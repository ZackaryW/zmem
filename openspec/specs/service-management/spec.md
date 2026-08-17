# service-management Specification

## Purpose

Defines how users install and manage a stable per-user zmem service runtime from disposable or persistent Python command environments.

## Requirements

### Requirement: Users can manage the per-user service through zmem
The `zmem service` command SHALL provide install, start, status, stop, upgrade, uninstall, and doctor operations with structured JSON output and meaningful nonzero failures.

#### Scenario: Install and start a service
- **WHEN** a user installs the service from an available native binary
- **THEN** zmem assembles the runtime, starts the installed service, and reports a healthy compatible status

#### Scenario: Inspect an absent service
- **WHEN** a user requests status before a runtime is installed
- **THEN** zmem reports that the runtime and service are absent without installing or starting either one

### Requirement: Remote service acquisition is deterministic and verified
When no explicit, configured, packaged, or PATH service binary is available, `zmem service install` and `upgrade` SHALL select the current platform from the release manifest at the exact `zmem` package version, SHALL verify the downloaded artifact's advertised length and SHA-256 digest, and SHALL validate its native release and protocol identity before activation. A failed selection, download, integrity check, or identity check SHALL leave the active runtime unchanged and report a meaningful nonzero failure.

#### Scenario: Install a version-matched service release
- **WHEN** a user installs without a local binary source on a platform present in the exact-version release manifest
- **THEN** zmem downloads, verifies, activates, starts, and reports the healthy compatible service artifact for that platform

#### Scenario: Reject a corrupt service artifact
- **WHEN** a selected release artifact does not match the manifest's advertised integrity metadata
- **THEN** installation fails without activating the artifact or replacing an existing healthy runtime

#### Scenario: Preserve local binary precedence
- **WHEN** a user installs with an explicit or configured local binary source
- **THEN** zmem uses that source without consulting the remote release

#### Scenario: Reject an unsupported platform
- **WHEN** the current operating-system and architecture pair has no supported release target
- **THEN** installation fails before downloading an artifact and identifies the unsupported pair

### Requirement: Active runtime paths are stable and versionless
The active runtime SHALL place the native service beneath `runtime/binary`, the persistent Python host beneath `runtime/host`, and typed release and compatibility metadata in the sibling `runtime/runtime.json`. Versions SHALL be recorded in metadata rather than active directory names.

#### Scenario: Inspect installed runtime metadata
- **WHEN** a user requests status for an installed runtime
- **THEN** the response reports the active paths, release, binary, host, protocol, schema, checksum, and installation identity from validated metadata

### Requirement: Runtime replacement is health-checked and recoverable
Install and upgrade SHALL stage complete replacements outside active paths, validate their artifacts and compatibility, stop the active daemon before switching, retain one previous runtime until the replacement is healthy, and restore that previous runtime if verification fails.

#### Scenario: Replacement service fails its health check
- **WHEN** an upgrade switches to a staged runtime that cannot pass the compatibility health check
- **THEN** zmem restores and restarts the previous healthy runtime and reports the failed upgrade

### Requirement: Python host assembly is portable and transactional
Install and upgrade SHALL create the persistent extension host from the invoking supported Python environment using the platform's native virtual-environment executable strategy and SHALL verify that the staged interpreter can execute and locate its package installation path before activation. If host creation or verification fails, zmem SHALL remove that installation's partial staging directory, SHALL leave any active runtime unchanged, and SHALL return a structured service-management failure that identifies the host assembly operation and its exit or signal cause when available.

#### Scenario: Install through a supported POSIX Python environment
- **WHEN** a user invokes service installation through a supported POSIX Python environment whose virtual environments use linked executables
- **THEN** zmem assembles a usable persistent extension host, activates the complete runtime, and reports a healthy compatible service

#### Scenario: Staged Python host aborts before activation
- **WHEN** the staged extension-host interpreter is terminated by a known signal during its package-path verification
- **THEN** installation fails with a structured service-management error naming that signal, removes the failed installation's partial staging directory, and leaves any active runtime unchanged

### Requirement: Temporary paths do not affect the real installation
Every service-management operation SHALL accept explicit alternate zmem-home and runtime-root paths. Operations using temporary paths SHALL act only beneath those paths and SHALL allow platform startup registration to be disabled.

#### Scenario: Install into an isolated temporary root
- **WHEN** a user installs with alternate home and runtime paths and disables startup registration
- **THEN** the complete runtime and service state are usable beneath those paths without modifying the default runtime or platform startup configuration

### Requirement: Platform startup registration is per user
Default installation SHALL register the stable runtime for the current user through the native Windows, macOS, or Linux user-startup mechanism; uninstall SHALL remove only that registration. Uninstall SHALL preserve repositories, configuration, extensions, and the database unless destructive data removal is explicitly requested.

#### Scenario: Uninstall while keeping data
- **WHEN** a user uninstalls the runtime without requesting data removal
- **THEN** zmem stops the service, removes its per-user startup registration and runtime artifacts, and retains the user's non-runtime zmem data

### Requirement: Managed clients reject incompatible runtimes
The Python client SHALL compare its supported protocol with the installed or running service before repository operations and SHALL report an actionable service-management error when they are incompatible.

#### Scenario: Client observes an incompatible service
- **WHEN** the running service reports an unsupported protocol version
- **THEN** the client refuses the repository operation and directs the user to install or upgrade a compatible runtime
