# Spec Delta

## MODIFIED Requirements

### Requirement: CLI reaches a fresh local index
The `zmem` client SHALL connect to or start the per-user service, register the selected repository when needed, and resolve the optional `--ref` commit-ish or observed worktree HEAD within its request budget. It SHALL answer a snapshot query successfully only from a compatible published immutable trail through that resolved commit. If the trail is unavailable and indexing is admitted or already pending, the command SHALL return structured `not_ready` promptly with job/retry guidance rather than wait for history reconstruction. It SHALL NOT substitute a stale/partial trail, report successful empty results for pending work, or automatically poll/retry.

#### Scenario: BDD target — First query in an unregistered repository
- **WHEN** executable behavior is covered by `features/memory-cli/memory-cli.feature::First query in an unregistered repository`
- **THEN** that exact feature scenario is the executable authority and this specification does not repeat its steps

#### Scenario: Explicit retry after indexing completes
- **WHEN** a query returned not_ready and the user issues it again after its job completes with the same observed OID
- **THEN** the compatible result uses the existing success envelope and exact selected-trail provenance

### Requirement: Failures are machine-readable
The CLI SHALL distinguish invalid usage, non-Git repositories, missing targets, unavailable service, and internal failures with structured error output and stable nonzero exit categories. It SHALL preserve typed native `not_ready`, `busy`, `timeout`, and `stale_ref` codes, retryability, and applicable job identity, retry delay, requested OID, and failure stage. Deferred, busy, timeout and stale-ref outcomes SHALL exit through service exit code 4, distinct from semantic check validation exit code 5. Unknown or malformed native failures SHALL remain service/protocol errors and SHALL NOT be inferred from annotation content or returned as successful empty results.

#### Scenario: Query outside Git
- **WHEN** a repository-scoped command runs outside a Git repository
- **THEN** it emits a structured repository error without registering a path

#### Scenario: Native indexing is pending
- **WHEN** the native response reports not_ready with job and retry metadata
- **THEN** CLI output retains that metadata and exits 4 without automatic retry or an invalid-annotation claim

## ADDED Requirements

### Requirement: Repository command waits are bounded
Repository commands SHALL accept a positive global `--timeout-ms`, defaulting to 2000 ms for snapshot commands and 120000 ms for checks. One monotonic execution budget SHALL span repository discovery, live ref observation, native execution, and subsequent request-owned work without resetting between phases. Expiry SHALL produce a structured service timeout, terminate and reap owned subprocesses with bounded cleanup grace of at most 1000 ms, and leave the shared daemon running. The client SHALL pass only the remaining budget to the native command.

#### Scenario: Ref observation consumes most of the budget
- **WHEN** live ref observation uses most of a query's timeout
- **THEN** native execution receives only the remaining budget rather than a new full timeout

#### Scenario: Native subprocess stalls
- **WHEN** the native client fails to return inside its remaining execution budget and cleanup grace
- **THEN** the Python command reaps that client, returns a structured timeout and does not stop the shared daemon

#### Scenario: Invalid timeout
- **WHEN** the user supplies zero, negative or non-integer timeout milliseconds
- **THEN** argument validation fails before service or Git work starts
