Feature: Bound repository command attention
  Scenario: Default attention policy is visible
    Given a repository with one decision annotation
    When I recall with the default attention policy
    Then the result reports commit limit 500 and node limit 400
    And its complete attention usage reports one commit and one node

  Scenario: Explicit attention overrides environment without replacing result limit
    Given three decision annotations and environmental attention limits of one
    When I recall with commit limit 3, node limit 2, and result limit 1
    Then the result contains one row from a two-node attention view
    And node attention and result limiting are both reported truncated

  Scenario: Invalid global attention fails before repository traversal
    Given a repository with one decision annotation
    When I recall with commit limit zero
    Then a structured invalid-usage error identifies commit limit

  Scenario: Non-entry annotations still consume node attention
    Given recent commits containing an entry, cancellation, and unsupported annotation
    When I recall under a two-node attention limit
    Then cancellation and unsupported annotation consume the available node attention
    And only supported entries inside that attention view can be returned
