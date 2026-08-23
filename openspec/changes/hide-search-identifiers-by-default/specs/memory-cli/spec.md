## MODIFIED Requirements

### Requirement: Commands use a common result envelope
Successful `recall`, `show`, `search`, and `links` commands SHALL emit a JSON object containing `command`, `count`, `results`, `truncated`, and the effective commit/node attention limits and observed usage. Recall, show, and links envelopes SHALL contain the typed selected-trail summary. Search envelopes SHALL omit that selected-trail summary by default and SHALL include it unchanged when `--trail` is requested. Attention truncation and a command-local result limit SHALL each make `truncated` true without changing the meaning of the other limit. A global human-output option SHALL render the same result.

#### Scenario: BDD target — Empty successful query
- **WHEN** executable behavior is covered by `features/memory-cli/memory-cli.feature::Empty successful query`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps

#### Scenario: BDD target — Attention truncation precedes result limiting
- **WHEN** executable behavior is covered by `features/memory-cli/memory-cli.feature::Attention truncation precedes result limiting`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps

#### Scenario: BDD target — Search hides selected-trail identity unless requested
- **WHEN** executable behavior is covered by `features/memory-cli/memory-cli.feature::Search hides selected-trail identity unless requested`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps

### Requirement: Search and links expose supported derived data
`search` SHALL perform case-insensitive text matching over supported entries, with optional type, regular-expression, validity, limit, repeatable affected-area, Git commit-ish, and selected-trail-output controls. The selected-trail-output control SHALL affect only response serialization, not snapshot selection or result identity. `links` SHALL return relationships from the selected trail and support source, target, minimum-score, and Git commit-ish filters. Search area matching SHALL use the same OR, hierarchy, `<root>`, and null/global semantics as recall.

#### Scenario: Search excludes invalid entries by default
- **WHEN** search matches both valid and cancelled entries without an include-invalid option
- **THEN** only valid entries are returned

#### Scenario: BDD target — Search combines text and affected area
- **WHEN** executable behavior is covered by `features/memory-cli/memory-cli.feature::Search combines text and affected area`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps

#### Scenario: BDD target — No relationship-producing expander
- **WHEN** executable behavior is covered by `features/memory-cli/memory-cli.feature::No relationship-producing expander`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps
