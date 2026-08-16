## MODIFIED Requirements

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
