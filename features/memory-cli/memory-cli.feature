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

  Scenario: No relationship-producing expander
    Given an index with no relationship-producing expander
    When I run zmem links
    Then an empty successful links envelope is returned

  Scenario: First query in an unregistered repository
    Given an unregistered Git repository with memory on a non-checked-out ref
    When I recall from that ref
    Then the repository is registered and the result identifies its compatible trail

  Scenario: Empty successful query
    Given an indexed trail with no matching entries
    When I recall its missing event type
    Then the complete empty envelope identifies the selected trail

  # zpp-spec: {"root":"repo:openspec","capability":"memory-cli","requirement":"Commands use a common result envelope","feature":"features/memory-cli/memory-cli.feature","scenario":"Snapshot commands hide selected-trail identity unless requested"}
  Scenario: Snapshot commands hide selected-trail identity unless requested
    Given an indexed trail with no matching entries
    When I run every snapshot command with default and explicit trail output
    Then only explicit snapshot envelopes identify the selected trail

  Scenario: Attention truncation precedes result limiting
    Given a trail whose attention and matching results both exceed their limits
    When I search with bounded attention and a result limit
    Then the envelope distinguishes attention usage from result count and reports truncation

  Scenario: Recall one monorepo area from another branch
    Given a branch with global and bounded memories across monorepo areas
    When I recall that branch for area b/sub
    Then only global or hierarchically overlapping valid entries are returned

  Scenario: Search combines text and affected area
    Given a selected trail with matching text across several affected areas
    When I search that ref with text and multiple affected areas
    Then only text matches in at least one requested area preserve the other filters

  Scenario: Links returns and filters expander relationships
    Given an indexed custom relationship from "m1" to "m2" with score 0.9
    When I run zmem links from "m1" with minimum score 0.8
    Then the relationship is returned in the links envelope

  Scenario: Repository and target failures are structured
    Given a non-Git directory and an unknown commit target
    When I issue the corresponding repository and show requests
    Then each failure has a stable nonzero category and JSON error
