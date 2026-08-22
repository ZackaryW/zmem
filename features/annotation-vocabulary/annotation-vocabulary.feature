Feature: Scored zmem annotation vocabulary
  Scenario: Plain text built-ins become scored entries
    Given a commit with DECISION "choose SQLite" and LESSON_LEARNT "timestamps are user controlled"
    When its annotations are expanded
    Then two valid entries retain their text in order with score 1.0

  Scenario: Repeated decay multiplies a target score
    Given an earlier decision entry with score 1.0
    When later reachable commits decay it by 0.5 and 0.4
    Then its effective score is 0.2
    And no DECAY entry is materialized

  Scenario: Invalid decay is diagnosed
    Given an invalid DECAY reference or factor
    When its annotation is expanded
    Then no entry changes
    And an effect diagnostic is returned

  Scenario: Cancel invalidates only a decision
    Given an earlier valid decision entry
    When a later reachable commit cancels it
    Then the decision is invalid with score 0.0
    And no CANCEL entry is materialized

  Scenario: Cancel rejects another entry type
    Given an earlier lesson entry
    When a later reachable commit tries to cancel it
    Then the lesson remains valid
    And an effect diagnostic is returned

  Scenario: Parse a metadata patch
    Given a commit containing a META owner replacement and tag addition
    When its annotations are expanded
    Then one ordered metadata-patch effect is emitted and no META entry is materialized

  Scenario: Query a commit containing effects
    Given a commit containing one valid metadata effect and no entry annotation
    When the commit is queried after expansion
    Then its complete target is updated and the effect commit contributes no queryable entry
