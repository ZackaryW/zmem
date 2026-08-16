Feature: Stable per-user service runtime management
  Scenario: Status does not create an absent runtime
    Given no managed runtime exists beneath the isolated paths
    When I run zmem service status
    Then status reports an absent runtime and stopped service
    And no runtime files or service state are created

  Scenario: Install into isolated paths without startup registration
    Given an available native zmem service binary
    When I install and start it without platform registration
    Then a healthy compatible runtime uses stable binary and host paths
    And runtime metadata records versions, checksum, protocol, schema, and installation identity

  Scenario: Install an exact-version release for the current platform
    Given an exact-version service release for the current platform
    When I install from the release without platform registration
    Then a healthy compatible runtime uses stable binary and host paths
    And the versioned manifest and selected platform artifact were requested

  Scenario: Corrupt release does not replace a healthy runtime
    Given a healthy isolated managed runtime
    And a corrupt exact-version service release for the current platform
    When I attempt to upgrade from the release
    Then the corrupt upgrade fails and the previous runtime remains healthy

  Scenario: Invalid replacement preserves the healthy runtime
    Given a healthy isolated managed runtime
    And an invalid replacement service artifact
    When I attempt to upgrade the managed runtime
    Then the upgrade fails and the previous runtime remains healthy

  Scenario: Uninstall preserves non-runtime data
    Given a healthy isolated managed runtime with cached user data
    When I uninstall it without removing data
    Then runtime artifacts are removed and cached user data remains

  Scenario: Memory commands reject an incompatible managed runtime
    Given managed runtime metadata with an unsupported protocol
    And an unregistered Git repository with a decision at its HEAD
    When I run zmem recall
    Then the client reports an actionable incompatible-runtime error
