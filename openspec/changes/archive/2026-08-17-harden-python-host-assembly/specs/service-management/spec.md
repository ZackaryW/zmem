## ADDED Requirements

### Requirement: Python host assembly is portable and transactional
Install and upgrade SHALL create the persistent extension host from the invoking supported Python environment using the platform's native virtual-environment executable strategy and SHALL verify that the staged interpreter can execute and locate its package installation path before activation. If host creation or verification fails, zmem SHALL remove that installation's partial staging directory, SHALL leave any active runtime unchanged, and SHALL return a structured service-management failure that identifies the host assembly operation and its exit or signal cause when available.

#### Scenario: Install through a supported POSIX Python environment
- **WHEN** a user invokes service installation through a supported POSIX Python environment whose virtual environments use linked executables
- **THEN** zmem assembles a usable persistent extension host, activates the complete runtime, and reports a healthy compatible service

#### Scenario: Staged Python host aborts before activation
- **WHEN** the staged extension-host interpreter is terminated by a known signal during its package-path verification
- **THEN** installation fails with a structured service-management error naming that signal, removes the failed installation's partial staging directory, and leaves any active runtime unchanged
