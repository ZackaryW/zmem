## MODIFIED Requirements

### Requirement: CLI reaches a fresh local index
The `zmem` client SHALL connect to or start the per-user service, register the selected repository when needed, resolve the optional `--ref` commit-ish or observed worktree HEAD, and wait until a compatible immutable trail through that resolved commit is available before answering a snapshot query.

#### Scenario: First query in an unregistered repository
- **WHEN** a user runs a query from an unregistered Git repository with an optional resolvable ref
- **THEN** the client registers it, waits for bounded trail construction through the resolved commit, and returns results from that attention view

### Requirement: Commands use a common result envelope
Successful `recall`, `show`, `search`, and `links` commands SHALL emit a JSON object containing `command`, `count`, `results`, `truncated`, and the effective commit/node attention limits and observed usage. Snapshot-query envelopes SHALL additionally contain the typed selected-trail summary. Attention truncation and a command-local result limit SHALL each make `truncated` true without changing the meaning of the other limit. A global human-output option SHALL render the same result.

#### Scenario: Empty successful query
- **WHEN** a supported query matches no entries and its attention view is complete
- **THEN** it exits successfully with count zero, an empty results list, `truncated` false, and the selected trail identity when applicable

#### Scenario: Attention truncation precedes result limiting
- **WHEN** search uses bounded attention and also supplies its command-local result limit
- **THEN** the envelope distinguishes trail attention usage from returned result count and reports truncation when either bound omitted data

### Requirement: Recall filters annotation entries
`recall` SHALL list annotation entries and support filtering by repeatable type, conventional-commit scope, repeatable affected area, inclusive SHA or ISO-date lower bound, result limit, and optional Git commit-ish. Repeated areas SHALL be ORed and combined with other filters by AND. A bounded area SHALL match an equal, ancestor, or descendant requested area; `<root>` SHALL match only root-level provenance; null/global SHALL always match. Recall SHALL support type-count facets.

#### Scenario: Recall one monorepo area from another branch
- **WHEN** recall selects a resolvable branch and requests `--area b/sub`
- **THEN** it returns valid entries from that trail whose metadata is global or hierarchically overlaps `b/sub`

### Requirement: Search and links expose supported derived data
`search` SHALL perform case-insensitive text matching over supported entries, with optional type, regular-expression, validity, limit, repeatable affected-area, and Git commit-ish filters. `links` SHALL return relationships from the selected trail and support source, target, minimum-score, and Git commit-ish filters. Search area matching SHALL use the same OR, hierarchy, `<root>`, and null/global semantics as recall.

#### Scenario: Search combines text and affected area
- **WHEN** search selects a ref, text, and multiple affected areas
- **THEN** it returns entries from that trail matching the text and at least one area while preserving all other requested filters

#### Scenario: No relationship-producing expander
- **WHEN** links is queried for a selected trail whose active expander set produced no stored relationships
- **THEN** the command succeeds with an empty result envelope and the selected trail identity
