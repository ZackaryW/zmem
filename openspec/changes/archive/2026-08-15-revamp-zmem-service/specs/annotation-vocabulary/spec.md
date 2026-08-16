## Purpose

Defines the stable annotation syntax, scored entry model, and built-in effects used to turn Git commit messages into durable zmem memory.

## ADDED Requirements

### Requirement: Plain-text annotations become scored entries
The system SHALL materialize each supported `zmem(TYPE): content` annotation as an entry identified by its full commit SHA and one-based annotation index. Every new entry SHALL have score `1.0` and valid state unless an effect changes it. `DECISION` and `LESSON_LEARNT` SHALL preserve their content as plain text.

#### Scenario: Built-in text annotations
- **WHEN** a commit contains `zmem(DECISION): choose SQLite` followed by `zmem(LESSON_LEARNT): timestamps are user controlled`
- **THEN** two valid entries are materialized in annotation order with score `1.0` and their original text

### Requirement: DECAY lowers an earlier entry score
The system SHALL interpret `zmem(DECAY)[<sha>, <index>, <factor>]` as an effect on an earlier reachable entry, resolve a unique short SHA to its full SHA, and multiply the target score by a factor from `0.0` through `1.0`. Multiple DECAY effects SHALL compose by multiplication.

#### Scenario: Repeated decay
- **WHEN** a score `1.0` entry is targeted by factors `0.5` and `0.4` in later reachable commits
- **THEN** its effective score is `0.2`

#### Scenario: Invalid decay target
- **WHEN** a DECAY reference is ambiguous, unresolved, forward-pointing, has an invalid index, or has a factor outside `0.0` through `1.0`
- **THEN** the effect changes no entry and produces a diagnostic

### Requirement: CANCEL invalidates a decision
The system SHALL interpret `zmem(CANCEL)[<sha>, <index>]` as an effect that sets an earlier reachable `DECISION` entry to invalid with score `0.0`. Later DECAY effects SHALL NOT restore a cancelled decision.

#### Scenario: Cancel a decision
- **WHEN** a valid decision is targeted by a later CANCEL annotation
- **THEN** the decision remains addressable but is invalid and has score `0.0`

#### Scenario: Reject a non-decision cancellation
- **WHEN** CANCEL targets an entry whose type is not `DECISION`
- **THEN** no entry changes and a diagnostic is produced

### Requirement: Effects are not entries
DECAY and CANCEL SHALL affect materialized state without themselves appearing as stored or queryable entries.

#### Scenario: Query a commit containing an effect
- **WHEN** a commit contains one DECAY annotation and no entry-producing annotation
- **THEN** the effect is applied but the commit contributes zero queryable entries
