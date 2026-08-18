## MODIFIED Requirements

### Requirement: Remote service acquisition is deterministic and verified
When no explicit, configured, packaged, or PATH service binary is available, `zmem service install` and `upgrade` SHALL inspect the published stable `zmem-cache` release inventory and select the greatest semantic version whose strict manifest includes the current platform and whose protocol and schema exactly equal the Python client's supported values. Drafts, prereleases, non-semantic tags, incompatible manifests, and releases without the current platform SHALL not be selected. The selected artifact's advertised length and SHA-256 digest and its native release, protocol, and schema identity SHALL be verified before activation. Discovery, selection, download, integrity, or identity failure SHALL leave the active runtime unchanged and report a meaningful nonzero failure. The Python package version and selected native release version SHALL be allowed to differ.

#### Scenario: Install newest compatible independent service release
- **WHEN** published stable service releases include multiple versions and the greatest version compatible with the client supports the current platform
- **THEN** zmem downloads, verifies, activates, starts, and reports that release even when its version differs from the Python package

#### Scenario: Newer service release is incompatible
- **WHEN** the newest published stable service release has a different protocol or schema and an older compatible release supports the current platform
- **THEN** zmem skips the incompatible release and installs the greatest compatible release

#### Scenario: No compatible service release exists
- **WHEN** no published stable release has a valid matching protocol, schema, and current-platform artifact
- **THEN** installation fails without replacing an existing runtime and identifies that no compatible native release was found

#### Scenario: Reject a corrupt service artifact
- **WHEN** the selected compatible release artifact does not match its manifest's advertised integrity metadata
- **THEN** installation fails without activating the artifact or replacing an existing healthy runtime

#### Scenario: Preserve local binary precedence
- **WHEN** a user installs with an explicit or configured local binary source
- **THEN** zmem uses that source without consulting the remote release inventory

#### Scenario: Reject an unsupported platform
- **WHEN** the current operating-system and architecture pair has no supported release target
- **THEN** installation fails before remote release discovery and identifies the unsupported pair

## ADDED Requirements

### Requirement: Runtime metadata identifies independent components
Managed runtime status SHALL report the Python host version and native binary version independently while retaining their shared protocol and schema compatibility identities. Runtime health SHALL depend on compatible protocol and schema values rather than equality between component release versions.

#### Scenario: Compatible component versions differ
- **WHEN** a managed runtime contains a Python host and native binary with different release versions but matching supported protocol and schema values
- **THEN** status reports both versions and treats the runtime as compatible
