Feature: Trusted Python expansion and hooks
  Scenario: Global extension adds a type
    Given a global expander for CUSTOM
    When a CUSTOM annotation is expanded
    Then the expander adds the custom entry through its expansion context
    And the expander returns no expansion value

  Scenario: Repository extension remains disabled without trust
    Given an untrusted repository with an extension under its configured root
    When its extension set is loaded
    Then the repository module is not imported
    And a disabled-extension diagnostic is returned

  Scenario: Duplicate overwrite fails deterministically
    Given two repository modules overwrite the same expander
    When the trusted extension set is loaded
    Then extension loading fails with a collision diagnostic

  Scenario: Hook cannot mutate canonical output
    Given an after_expand hook that returns a canonical mutation
    When an annotation is expanded
    Then the mutation is rejected with a hook diagnostic

  Scenario: Built-in cancellation performs a context action
    Given a CANCEL annotation targeting an earlier decision
    When the CANCEL expander runs
    Then it calls cancel on the expansion context
    And it returns no dictionary or other expansion value

  Scenario: Hook failure does not erase expansion
    Given a valid expander and a failing after_index hook
    When indexing hooks are run
    Then the expanded entry remains in the response
    And the hook failure is diagnosed

  Scenario: Source changes alter extension identity
    Given a loaded extension set
    When one trusted module source changes
    Then the extension-set identity changes
