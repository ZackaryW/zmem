## ADDED Requirements

### Requirement: Queries select immutable trails through live Git refs
Snapshot queries SHALL accept an optional Git commit-ish, resolve it against the current repository at request time, and identify the selected cache trail by repository, resolved HEAD, attention policy, extension identity, and protocol/schema identity. Omitting the selector SHALL use the worktree's observed HEAD.

#### Scenario: Query an unoccupied branch
- **WHEN** a user queries `--ref feature` while another branch is checked out
- **THEN** the query resolves the current `feature` OID and returns the compatible trail without changing the worktree

### Requirement: Branch aliases are non-authoritative
The system MAY retain reusable aliases for local branches, but it SHALL resolve a requested branch through Git before use and SHALL reject a request when the ref moved after the client's observed resolution. Tags, remote-tracking branches, detached OIDs, and other resolvable commit-ish values SHALL remain selectable without becoming authoritative local-branch aliases.

#### Scenario: Branch moves during a query
- **WHEN** the client-observed branch OID differs from the service's live resolution
- **THEN** the query fails with a structured stale-ref error instead of returning either ambiguous trail

### Requirement: Query envelopes identify the selected trail
Successful snapshot queries SHALL include a typed trail summary containing the requested selector, resolved HEAD, trail identity, effective attention identity and usage, extension identity, and protocol/schema identity. TRAIL SHALL remain a cache-native entity and SHALL NOT be parsed as a commit annotation or exposed through dedicated trail-management commands in this change.

#### Scenario: Two names resolve to one trail
- **WHEN** two selectors resolve to the same repository HEAD under identical attention, extension, and compatibility identities
- **THEN** their query envelopes identify the same immutable trail while retaining their respective requested selectors
