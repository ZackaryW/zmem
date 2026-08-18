## ADDED Requirements

### Requirement: Parser-only inspection is batchable
The Python extension host SHALL accept a versioned parser-only batch containing ordered stable item identities and commit-message text. It SHALL parse each item independently without loading expanders or running hooks and SHALL return exactly one ordered result per request item containing the same identity, annotation count, and parser diagnostics. An invalid item SHALL fail the complete batch rather than return a partial result.

#### Scenario: Batch contains multiple commit messages
- **WHEN** the service submits a compatible parser-only batch with multiple identified messages
- **THEN** the host returns one same-order identified inspection result per message without importing extensions or executing hooks

#### Scenario: Batch contains an invalid item
- **WHEN** one batch item lacks a valid identity or message
- **THEN** the host rejects the complete batch without returning results for the other items
