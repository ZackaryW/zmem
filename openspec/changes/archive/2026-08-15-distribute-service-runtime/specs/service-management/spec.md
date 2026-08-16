## ADDED Requirements

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
