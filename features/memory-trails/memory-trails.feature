Feature: Live immutable memory trails
  Scenario: Query an unoccupied branch
    Given a repository with an unoccupied branch containing memory
    When I query that branch without checking it out
    Then the result uses an immutable trail through the branch head without changing the worktree

  Scenario: Branch moves during a query
    Given a client-observed branch head that moves before native resolution
    When I query the branch with the observed commit identity
    Then the query fails with a structured stale-ref error and publishes no trail

  Scenario: Two names resolve to one trail
    Given two Git selectors resolving to one commit under identical identities
    When I query memory through both selectors
    Then both envelopes identify the same immutable trail and their requested selectors
