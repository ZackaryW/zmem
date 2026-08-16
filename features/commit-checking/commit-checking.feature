Feature: Preview zmem commit messages before committing
  Scenario: Ordinary mixed prose checks cleanly
    Given a repository whose HEAD contains a decision
    And a proposed conventional message with ordinary prose and a lesson annotation
    When I check the proposed message from a file
    Then the JSON check succeeds with one projected entry
    And no hypothetical memory is returned by a following query

  Scenario: Proposed cancellation reports projected state
    Given a repository whose HEAD contains a decision
    And a proposed message cancelling that decision
    When I check the proposed message from standard input
    Then the target remains stored as valid with score 1.0
    And the check reports it would become invalid with score 0.0
    And hooks are reported skipped

  Scenario: Requested message policies are enforced together
    Given a proposed non-conventional message without an annotation
    When I check it requiring conventional form, a short subject, and an annotation
    Then the check fails with every requested policy diagnostic

  Scenario: Invalid effect fails with its semantic preview
    Given a repository whose HEAD contains a decision
    And a proposed cancellation of a missing target
    When I check the proposed message from standard input
    Then the check fails with an unresolved-effect diagnostic
    And the original decision remains valid

  Scenario: Active trusted expander participates without hooks
    Given a trusted repository with a custom entry expander and an observing hook
    And a proposed message using the custom annotation
    When I check the proposed message from standard input
    Then the custom entry action is projected
    And the observing hook has not run

  Scenario: Deep check evaluates an existing effect once
    Given a repository history containing a decision followed by one decay
    When I deep-check the existing decay commit
    Then the historical check reports one decay from score 1.0 to 0.5
    And the persistent decision remains at its previously indexed score

  Scenario: Deep proposed file replays history before revealing its effect
    Given reachable history containing an uncached decision
    And a proposed file cancelling that decision
    When I check that file deeply with sufficient attention
    Then the proposed-file check reports cancellation from valid to invalid
    And no replayed or hypothetical memory is persisted

  Scenario: Deep proposed effect distinguishes incomplete attention
    Given reachable history containing an older decision and newer annotations
    And a proposed file cancelling that older decision
    When I check that file deeply below the required attention
    Then the check fails with an attention-threshold diagnostic
    And it does not claim the decision is absent from complete history
