## ADDED Requirements

### Requirement: Entries expose typed commit metadata
Every queryable entry SHALL expose `affected_areas` as either null or an ordered unique array of normalized repository-relative areas, `owner` as either null or a string, and `tags` as an ordered unique string array. Null `affected_areas` SHALL mean global applicability and SHALL match every affected-area filter.

#### Scenario: Legacy entry has global applicability
- **WHEN** a migrated entry has no assigned affected-area metadata
- **THEN** its result contains null `affected_areas` and it remains visible under every `--area` filter

### Requirement: New cached commits receive compact intrinsic affected areas
For commits newly entering the compatible cache, the system SHALL derive affected areas from changed paths by treating root-level files as `<root>`, grouping other paths by top-level directory, and reducing each group to its deepest common parent. Root SHALL count as an area, both rename endpoints SHALL participate, and a result containing more than three areas SHALL become null/global.

#### Scenario: Three compact areas are retained
- **WHEN** a new commit changes a root file, paths beneath multiple children of `a`, and paths only beneath `b/sub`
- **THEN** its intrinsic affected areas are `<root>`, `a`, and `b/sub`

#### Scenario: Broad commit becomes global
- **WHEN** compacting a new commit produces four distinct areas
- **THEN** its affected areas are null and match every area query

### Requirement: META patches declared metadata keys
The system SHALL interpret `zmem(META)[<from>, <to>, <operations>...]` as a non-entry effect over `affected_areas`, `owner`, and `tags`. `key=value` SHALL replace a value, `key+=value` SHALL add a unique member to a set-valued key, and `key=null` SHALL reset the key; unknown keys, type-invalid operations, and attempts to change canonical entry fields SHALL fail without mutation and produce diagnostics.

#### Scenario: Later META replaces and extends metadata
- **WHEN** a descendant META replaces `owner` and adds a tag across a valid target range
- **THEN** every targeted entry observes the replacement owner and the unique added tag without changing its conventional scope, score, or validity

#### Scenario: META resets affected areas to global
- **WHEN** META assigns `affected_areas=null` to a complete valid range
- **THEN** the targeted entries become globally applicable and match every area filter

### Requirement: META ranges are complete reachable ancestry
META endpoints SHALL resolve uniquely in the selected trail, `from` SHALL be an ancestor of `to`, both endpoints SHALL precede the META commit, and the inclusive range SHALL contain every selected commit that is both a descendant of `from` and an ancestor of `to`. If attention or trail membership omits any required range commit, the complete META effect SHALL fail atomically.

#### Scenario: Merged ancestry is patched
- **WHEN** a valid META range contains commits from a merged branch that descend from `from` and lead to `to`
- **THEN** those commits receive the patch together with the qualifying mainline commits

#### Scenario: Truncated range changes nothing
- **WHEN** an attention boundary prevents the selected trail from proving a complete META range
- **THEN** no target metadata changes and the query reports a structured diagnostic

### Requirement: META precedence follows ancestry
A META patch SHALL override an earlier conflicting patch only when its commit descends from the earlier patch commit. Conflicting patches from commits that are not ancestors of one another SHALL remain unresolved until a descendant META explicitly resolves the key.

#### Scenario: Concurrent owners require resolution
- **WHEN** two merged branch commits assign different owners to the same target and neither META commit descends from the other
- **THEN** the owner is reported as conflicted until a later descendant META assigns the resolving value
