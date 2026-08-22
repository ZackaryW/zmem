Feature: Typed memory metadata
  Scenario: Legacy entry has global applicability
    Given a migrated memory entry without affected-area metadata
    When I recall it with an affected-area filter
    Then the entry reports null affected areas and remains visible

  Scenario: Three compact areas are retained
    Given a new commit changing a root file, sibling paths under a, and one subtree under b
    When the commit enters the compatible cache
    Then its affected areas are root, a, and b/sub

  Scenario: Broad commit becomes global
    Given a new commit whose compact provenance has four areas
    When the commit enters the compatible cache
    Then its affected areas are null and match every area query

  Scenario: Later META replaces and extends metadata
    Given a selected trail with entries in a complete META range
    When a descendant META replaces owner and adds a tag across that range
    Then each target reports the replacement owner and unique tag without changing canonical fields

  Scenario: META resets affected areas to global
    Given a selected trail with bounded affected areas
    When META resets affected areas across a complete range
    Then each target reports null affected areas and matches every area query

  Scenario: Merged ancestry is patched
    Given a complete META range containing qualifying merged descendants
    When the selected trail applies the metadata patch
    Then every commit in the inclusive reachable range receives the patch

  Scenario: Truncated range changes nothing
    Given attention omits part of a requested META range
    When the trail containing that META is constructed
    Then no target metadata changes and an incomplete-range diagnostic is returned

  Scenario: Concurrent owners require resolution
    Given incomparable META assignments conflict on one metadata key
    When the selected trail reaches their merge without a descendant assignment
    Then that key reports conflict until a descendant META resolves it
