# memory-cli Specification

## Purpose

Defines the JSON-first command surface through which users query service-backed zmem entries from a selected Git repository.

## Requirements

### Requirement: CLI reaches a fresh local index
The `zmem` client SHALL connect to or start the per-user service, register the selected repository when needed, and wait until the repository's observed HEAD has a current projection for the effective attention policy before answering a query.

#### Scenario: First query in an unregistered repository
- **WHEN** a user runs a query from a Git repository that has not been added
- **THEN** the client registers it, waits for bounded initial indexing through its current HEAD, and returns results from that attention view

### Requirement: Commands use a common result envelope
Successful `recall`, `show`, `search`, and `links` commands SHALL emit a JSON object containing `command`, `count`, `results`, `truncated`, and the effective commit/node attention limits and observed usage. Attention truncation and a command-local result limit SHALL each make `truncated` true without changing the meaning of the other limit. A global human-output option SHALL render the same result.

#### Scenario: Empty successful query
- **WHEN** a supported query matches no entries and its attention view is complete
- **THEN** it exits successfully with count zero, an empty results list, and `truncated` false

#### Scenario: Attention truncation precedes result limiting
- **WHEN** search uses bounded attention and also supplies its command-local result limit
- **THEN** the envelope distinguishes the effective attention usage from returned result count and reports truncation when either bound omitted data

### Requirement: Recall filters annotation entries
`recall` SHALL list annotation entries and support filtering by repeatable type, conventional-commit scope, inclusive SHA or ISO-date lower bound, and result limit. It SHALL support type-count facets.

#### Scenario: Recall decisions since a boundary
- **WHEN** recall is limited to `DECISION` entries at or after a resolvable boundary
- **THEN** only matching entries are returned and truncation is reported when the limit is exceeded

### Requirement: Show returns one commit's memory
`show <sha>` SHALL resolve a full or unique short SHA and return that commit's metadata, annotations, and changed paths, with diff content included only when requested.

#### Scenario: Unknown commit
- **WHEN** show receives an unresolved commit reference
- **THEN** it emits a structured not-found error and exits nonzero

### Requirement: Search and links expose supported derived data
`search` SHALL perform case-insensitive text matching over supported entries, with optional type, regular-expression, validity, and limit filters. `links` SHALL return relationships produced by supported expanders and support source, target, and minimum-score filters.

#### Scenario: Search excludes invalid entries by default
- **WHEN** search matches both valid and cancelled entries without an include-invalid option
- **THEN** only valid entries are returned

#### Scenario: No relationship-producing expander
- **WHEN** links is queried and the active expander set produced no stored relationships
- **THEN** the command succeeds with an empty result envelope

### Requirement: Failures are machine-readable
The CLI SHALL distinguish invalid usage, non-Git repositories, missing targets, unavailable service, and internal failures with structured error output and stable nonzero exit categories.

#### Scenario: Query outside Git
- **WHEN** a repository-scoped command runs outside a Git repository
- **THEN** it emits a structured repository error without registering a path
