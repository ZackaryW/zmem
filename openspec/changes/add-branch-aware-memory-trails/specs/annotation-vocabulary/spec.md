## ADDED Requirements

### Requirement: META syntax produces typed metadata effects
The parser SHALL recognize `zmem(META)[<from>, <to>, <operation>, ...]` with one-based annotation ordering, preserve typed set, add, and null operations for the host, and reject malformed endpoints, keys, operators, or values diagnostically. META SHALL consume annotation attention but SHALL NOT create a queryable entry.

#### Scenario: BDD target — Parse a metadata patch
- **WHEN** executable behavior is covered by `features/annotation-vocabulary/annotation-vocabulary.feature::Parse a metadata patch`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps

## MODIFIED Requirements

### Requirement: Effects are not entries
DECAY, CANCEL, and META SHALL affect materialized trail state without themselves appearing as stored or queryable entries.

#### Scenario: BDD target — Query a commit containing effects
- **WHEN** executable behavior is covered by `features/annotation-vocabulary/annotation-vocabulary.feature::Query a commit containing effects`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps
