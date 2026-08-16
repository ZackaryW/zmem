## Purpose

Defines how users install and manage a stable per-user zmem service runtime from disposable or persistent Python command environments.

## ADDED Requirements

### Requirement: Users can manage the per-user service through zmem
The `zmem service` command SHALL provide install, start, status, stop, upgrade, uninstall, and doctor operations with structured JSON output and meaningful nonzero failures.

#### Scenario: Install and start a service
- **WHEN** a user installs the service from an available native binary
- **THEN** zmem assembles the runtime, starts the installed service, and reports a healthy compatible status

#### Scenario: Inspect an absent service
- **WHEN** a user requests status before a runtime is installed
- **THEN** zmem reports that the runtime and service are absent without installing or starting either one

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
