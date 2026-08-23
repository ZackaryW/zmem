## MODIFIED Requirements

### Requirement: Commands use a common result envelope
Successful `recall`, `show`, `search`, and `links` commands SHALL emit a JSON object containing `command`, `count`, `results`, `truncated`, and the effective commit/node attention limits and observed usage. Snapshot-query envelopes SHALL omit the typed selected-trail summary by default and SHALL include it unchanged when that command's `--trail` option is requested. The output control SHALL NOT change snapshot selection, result fields, or filtering. Attention truncation and a command-local result limit SHALL each make `truncated` true without changing the meaning of the other limit. A global human-output option SHALL render the same result.

#### Scenario: BDD target — Empty successful query
- **WHEN** executable behavior is covered by `features/memory-cli/memory-cli.feature::Empty successful query`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps

#### Scenario: BDD target — Attention truncation precedes result limiting
- **WHEN** executable behavior is covered by `features/memory-cli/memory-cli.feature::Attention truncation precedes result limiting`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps

#### Scenario: BDD target — Snapshot commands hide selected-trail identity unless requested
- **WHEN** executable behavior is covered by `features/memory-cli/memory-cli.feature::Snapshot commands hide selected-trail identity unless requested`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps
