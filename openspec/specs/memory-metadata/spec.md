# memory-metadata Specification

## Purpose

Defines typed, trail-layered memory metadata and conservative monorepo affected-area behavior.

## Requirements

### Requirement: Entries expose typed commit metadata
Every queryable entry SHALL expose `affected_areas` as either null or an ordered unique array of normalized repository-relative areas, `owner` as either null or a string, and `tags` as an ordered unique string array. Null `affected_areas` SHALL mean global applicability and SHALL match every affected-area filter.

#### Scenario: BDD target — Legacy entry has global applicability
- **WHEN** executable behavior is covered by `features/memory-metadata/memory-metadata.feature::Legacy entry has global applicability`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps

### Requirement: New cached commits receive compact intrinsic affected areas
For commits newly entering the compatible cache, the system SHALL derive affected areas from changed paths by treating root-level files as `<root>`, grouping other paths by top-level directory, and reducing each group to its deepest common parent. Root SHALL count as an area, both rename endpoints SHALL participate, and a result containing more than three areas SHALL become null/global.

#### Scenario: BDD target — Three compact areas are retained
- **WHEN** executable behavior is covered by `features/memory-metadata/memory-metadata.feature::Three compact areas are retained`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps

#### Scenario: BDD target — Broad commit becomes global
- **WHEN** executable behavior is covered by `features/memory-metadata/memory-metadata.feature::Broad commit becomes global`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps

### Requirement: META patches declared metadata keys
The system SHALL interpret `zmem(META)[<from>, <to>, <operations>...]` as a non-entry effect over `affected_areas`, `owner`, and `tags`. `key=value` SHALL replace a value, `key+=value` SHALL add a unique member to a set-valued key, and `key=null` SHALL reset the key; unknown keys, type-invalid operations, and attempts to change canonical entry fields SHALL fail without mutation and produce diagnostics.

#### Scenario: BDD target — Later META replaces and extends metadata
- **WHEN** executable behavior is covered by `features/memory-metadata/memory-metadata.feature::Later META replaces and extends metadata`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps

#### Scenario: BDD target — META resets affected areas to global
- **WHEN** executable behavior is covered by `features/memory-metadata/memory-metadata.feature::META resets affected areas to global`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps

### Requirement: META ranges are complete reachable ancestry
META endpoints SHALL resolve uniquely in the selected trail, `from` SHALL be an ancestor of `to`, both endpoints SHALL precede the META commit, and the inclusive range SHALL contain every selected commit that is both a descendant of `from` and an ancestor of `to`. If attention or trail membership omits any required range commit, the complete META effect SHALL fail atomically.

#### Scenario: BDD target — Merged ancestry is patched
- **WHEN** executable behavior is covered by `features/memory-metadata/memory-metadata.feature::Merged ancestry is patched`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps

#### Scenario: BDD target — Truncated range changes nothing
- **WHEN** executable behavior is covered by `features/memory-metadata/memory-metadata.feature::Truncated range changes nothing`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps

### Requirement: META precedence follows ancestry
A META patch SHALL override an earlier conflicting patch only when its commit descends from the earlier patch commit. Conflicting patches from commits that are not ancestors of one another SHALL remain unresolved until a descendant META explicitly resolves the key.

#### Scenario: BDD target — Concurrent owners require resolution
- **WHEN** executable behavior is covered by `features/memory-metadata/memory-metadata.feature::Concurrent owners require resolution`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps
