## ADDED Requirements

### Requirement: Queries select immutable trails through live Git refs
Snapshot queries SHALL accept an optional Git commit-ish, resolve it against the current repository at request time, and identify the selected cache trail by repository, resolved HEAD, attention policy, extension identity, and protocol/schema identity. Omitting the selector SHALL use the worktree's observed HEAD.

#### Scenario: BDD target — Query an unoccupied branch
- **WHEN** executable behavior is covered by `features/memory-trails/memory-trails.feature::Query an unoccupied branch`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps

### Requirement: Branch aliases are non-authoritative
The system MAY retain reusable aliases for local branches, but it SHALL resolve a requested branch through Git before use and SHALL reject a request when the ref moved after the client's observed resolution. Tags, remote-tracking branches, detached OIDs, and other resolvable commit-ish values SHALL remain selectable without becoming authoritative local-branch aliases.

#### Scenario: BDD target — Branch moves during a query
- **WHEN** executable behavior is covered by `features/memory-trails/memory-trails.feature::Branch moves during a query`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps

### Requirement: Query envelopes identify the selected trail
Successful snapshot queries SHALL include a typed trail summary containing the requested selector, resolved HEAD, trail identity, effective attention identity and usage, extension identity, and protocol/schema identity. TRAIL SHALL remain a cache-native entity and SHALL NOT be parsed as a commit annotation or exposed through dedicated trail-management commands in this change.

#### Scenario: BDD target — Two names resolve to one trail
- **WHEN** executable behavior is covered by `features/memory-trails/memory-trails.feature::Two names resolve to one trail`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps
