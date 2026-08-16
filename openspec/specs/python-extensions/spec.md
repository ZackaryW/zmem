# python-extensions Specification

## Purpose

Defines trusted Python expanders and hooks that extend annotation behavior without sacrificing deterministic indexing or canonical cache ownership.

## Requirements

### Requirement: Expanders and hooks have separate authority
An expander SHALL receive a typed expansion context containing the current annotation and commit context, SHALL perform canonical work only through context actions such as adding an entry, adding a relationship, decaying a target, cancelling a target, or recording a diagnostic, and SHALL return no expansion value. A hook SHALL observe `after_expand` or `after_index` through a read-only hook context and MAY perform external side effects, but SHALL NOT perform canonical actions or modify entries, scores, effects, anchors, or relationships.

#### Scenario: Expander performs a context action
- **WHEN** the DECISION expander handles a supported annotation
- **THEN** it calls the context entry action and returns no dictionary or other expansion result

#### Scenario: Hook attempts canonical mutation
- **WHEN** a hook attempts to return or apply a canonical data mutation
- **THEN** the extension host rejects the mutation and reports a diagnostic

### Requirement: Global extensions load from the user extension root
The extension host SHALL discover importable Python files under `~/.zmem/ext/expanders` and `~/.zmem/ext/hooks`, load them in deterministic order, and treat them as user-trusted.

#### Scenario: Global expander is present
- **WHEN** a valid global expander registers a previously unknown annotation type
- **THEN** annotations of that type are materialized through that expander

### Requirement: Repository extensions use configured roots and explicit trust
The extension host SHALL discover repository extensions under `${ZMEM_CUSTOM_EXT_ROOT:-.zmem}/extend/{expanders,hooks}` and `${ZMEM_CUSTOM_EXT_ROOT:-.zmem}/overwrite/{expanders,hooks}`, resolving a relative custom root from the repository root. Repository code SHALL remain disabled until the repository is added with extension trust.

#### Scenario: Untrusted repository extension
- **WHEN** a repository contains extension Python but was not trusted
- **THEN** the files are not imported and a diagnostic identifies the disabled extension root

### Requirement: Extension and overwrite registration is deterministic
`extend` SHALL only add new registration IDs, while `overwrite` SHALL only replace existing IDs. Collisions, missing overwrite targets, duplicate overwrites, invalid modules, and API-version mismatches SHALL fail extension-set loading instead of using last-file-wins behavior.

#### Scenario: Duplicate overwrite
- **WHEN** two repository modules overwrite the same expander ID
- **THEN** indexing does not use either ambiguous overwrite and reports the conflict

### Requirement: Extension host uses a versioned typed boundary
The Python extension host SHALL collect context actions in a private typed journal, exchange the journal through a versioned typed boundary with the service, and identify the loaded extension set by stable source hashes. Extension implementations SHALL NOT construct or return the serialized journal representation directly.

#### Scenario: Context actions cross the service boundary
- **WHEN** an expander performs entry and effect actions through its context
- **THEN** the host serializes those actions after expansion and the extension never handles the wire representation

#### Scenario: Extension source changes
- **WHEN** trusted extension source changes after a repository was indexed
- **THEN** the host reports a different extension-set identity so the service can rebuild derived state

### Requirement: Hook failures preserve canonical indexing
A hook failure SHALL be reported as a diagnostic and SHALL NOT roll back otherwise valid canonical indexing.

#### Scenario: after-index hook fails
- **WHEN** an `after_index` hook raises an exception
- **THEN** the completed index remains available and the failure is reported
