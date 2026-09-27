# Spec Delta

## ADDED Requirements

### Requirement: Check timeouts remain service failures
The client SHALL bound fast and deep check execution by the configured request deadline and distinguish service timeout, overload, deferred real-history work and fatal service failures from semantic annotation invalidity. Such service outcomes SHALL preserve available native machine-readable error details and exit 4 without presenting a completed semantic check result. Actual completed semantic validation SHALL retain its existing outcome and exit behavior. Timeout cleanup SHALL NOT stop the shared service or persist hypothetical state.

#### Scenario: Deep history replay times out
- **WHEN** a deep check exceeds its request deadline while replaying valid annotations
- **THEN** the CLI reports a service timeout rather than claiming an annotation is invalid

#### Scenario: Completed semantic rejection
- **WHEN** a completed check conclusively rejects an invalid effect
- **THEN** the existing semantic failure result and exit 5 remain unchanged
