Feature: Service-backed zmem commands
  Scenario: First recall starts service and registers repository
    Given an unregistered Git repository with a decision at its HEAD
    When I run zmem recall
    Then the service is available and indexed through that HEAD
    And a recall JSON envelope contains the decision

  Scenario: Recall filters and truncates
    Given indexed decisions and lessons across commits
    When I recall DECISION entries with an inclusive boundary and limit 1
    Then only one matching decision is returned
    And the result is marked truncated when another match exists

  Scenario: Show resolves commit memory
    Given an indexed commit with annotations and changed paths
    When I show its unique short SHA with diff content
    Then one show result contains its metadata, annotations, paths, and diff

  Scenario: Search excludes cancelled entries
    Given indexed valid and cancelled entries containing "cache"
    When I search for "cache"
    Then only the valid entry is returned

  Scenario: Links succeeds without relationships
    Given an index with no relationship-producing expander
    When I run zmem links
    Then an empty successful links envelope is returned

  Scenario: Links returns and filters expander relationships
    Given an indexed custom relationship from "m1" to "m2" with score 0.9
    When I run zmem links from "m1" with minimum score 0.8
    Then the relationship is returned in the links envelope

  Scenario: Repository and target failures are structured
    Given a non-Git directory and an unknown commit target
    When I issue the corresponding repository and show requests
    Then each failure has a stable nonzero category and JSON error
