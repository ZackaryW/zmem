# memory-cli Specification

## Purpose

Defines the JSON-first command surface through which users query service-backed zmem entries from a selected Git repository.

## Requirements

### Requirement: CLI reaches a fresh local index
The `zmem` client SHALL connect to or start the per-user service, register the selected repository when needed, resolve the optional `--ref` commit-ish or observed worktree HEAD, and wait until a compatible immutable trail through that resolved commit is available before answering a snapshot query.

#### Scenario: BDD target — First query in an unregistered repository
- **WHEN** executable behavior is covered by `features/memory-cli/memory-cli.feature::First query in an unregistered repository`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps

### Requirement: Commands use a common result envelope
Successful `recall`, `show`, `search`, and `links` commands SHALL emit a JSON object containing `command`, `count`, `results`, `truncated`, and the effective commit/node attention limits and observed usage. Snapshot-query envelopes SHALL additionally contain the typed selected-trail summary. Attention truncation and a command-local result limit SHALL each make `truncated` true without changing the meaning of the other limit. A global human-output option SHALL render the same result.

#### Scenario: BDD target — Empty successful query
- **WHEN** executable behavior is covered by `features/memory-cli/memory-cli.feature::Empty successful query`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps

#### Scenario: BDD target — Attention truncation precedes result limiting
- **WHEN** executable behavior is covered by `features/memory-cli/memory-cli.feature::Attention truncation precedes result limiting`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps

### Requirement: Recall filters annotation entries
`recall` SHALL list annotation entries and support filtering by repeatable type, conventional-commit scope, repeatable affected area, inclusive SHA or ISO-date lower bound, result limit, and optional Git commit-ish. Repeated areas SHALL be ORed and combined with other filters by AND. A bounded area SHALL match an equal, ancestor, or descendant requested area; `<root>` SHALL match only root-level provenance; null/global SHALL always match. Recall SHALL support type-count facets.

#### Scenario: Recall decisions since a boundary
- **WHEN** recall is limited to `DECISION` entries at or after a resolvable boundary
- **THEN** only matching entries are returned and truncation is reported when the limit is exceeded

#### Scenario: BDD target — Recall one monorepo area from another branch
- **WHEN** executable behavior is covered by `features/memory-cli/memory-cli.feature::Recall one monorepo area from another branch`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps

### Requirement: Show returns one commit's memory
`show <sha>` SHALL resolve a full or unique short SHA and return that commit's metadata, annotations, and changed paths, with diff content included only when requested.

#### Scenario: Unknown commit
- **WHEN** show receives an unresolved commit reference
- **THEN** it emits a structured not-found error and exits nonzero

### Requirement: Search and links expose supported derived data
`search` SHALL perform case-insensitive text matching over supported entries, with optional type, regular-expression, validity, limit, repeatable affected-area, and Git commit-ish filters. `links` SHALL return relationships from the selected trail and support source, target, minimum-score, and Git commit-ish filters. Search area matching SHALL use the same OR, hierarchy, `<root>`, and null/global semantics as recall.

#### Scenario: Search excludes invalid entries by default
- **WHEN** search matches both valid and cancelled entries without an include-invalid option
- **THEN** only valid entries are returned

#### Scenario: BDD target — Search combines text and affected area
- **WHEN** executable behavior is covered by `features/memory-cli/memory-cli.feature::Search combines text and affected area`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps

#### Scenario: BDD target — No relationship-producing expander
- **WHEN** executable behavior is covered by `features/memory-cli/memory-cli.feature::No relationship-producing expander`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps

### Requirement: Failures are machine-readable
The CLI SHALL distinguish invalid usage, non-Git repositories, missing targets, unavailable service, and internal failures with structured error output and stable nonzero exit categories.

#### Scenario: Query outside Git
- **WHEN** a repository-scoped command runs outside a Git repository
- **THEN** it emits a structured repository error without registering a path
