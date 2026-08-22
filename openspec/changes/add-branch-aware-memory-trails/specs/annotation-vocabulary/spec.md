## ADDED Requirements

### Requirement: META syntax produces typed metadata effects
The parser SHALL recognize `zmem(META)[<from>, <to>, <operation>, ...]` with one-based annotation ordering, preserve typed set, add, and null operations for the host, and reject malformed endpoints, keys, operators, or values diagnostically. META SHALL consume annotation attention but SHALL NOT create a queryable entry.

#### Scenario: Parse a metadata patch
- **WHEN** a commit contains `zmem(META)[abc123, def456, owner=platform, tags+=security]`
- **THEN** the host emits one validated metadata-patch effect with ordered operations and no META entry

## MODIFIED Requirements

### Requirement: Effects are not entries
DECAY, CANCEL, and META SHALL affect materialized trail state without themselves appearing as stored or queryable entries.

#### Scenario: Query a commit containing effects
- **WHEN** a commit contains one valid META or DECAY annotation and no entry-producing annotation
- **THEN** the effect is applied to its complete valid target while the commit contributes zero queryable entries
