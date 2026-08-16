## Purpose

Defines how users and agents validate proposed or historical commit messages through zmem's active annotation and effect semantics without creating commits or hypothetical cache state.

## ADDED Requirements

### Requirement: Proposed messages can be checked before commit
The `zmem check` command SHALL accept exactly one proposed message from `--file <path>` or `--stdin`, SHALL treat it as a hypothetical successor to the selected repository's current `HEAD`, and SHALL accept an ordinary message containing zero zmem annotations unless annotation presence is explicitly required.

#### Scenario: Mixed proposed message
- **WHEN** a proposed message contains an ordinary subject and body plus supported entry and effect annotations
- **THEN** check reports the parsed annotations and their projected actions without creating a Git commit

#### Scenario: Ordinary proposed message
- **WHEN** a proposed message contains no zmem annotation and annotation presence was not required
- **THEN** check succeeds with zero annotations and zero projected actions

### Requirement: Check reports semantic outcomes
Check SHALL emit JSON containing its command, success state, mode, evaluated parent or target, annotation count, projected actions, resolved effect outcomes, diagnostics, and hook-execution state. Effect outcomes SHALL identify the target and its score and validity before and after simulation. Parser errors, unsupported types, invalid or unresolved effects, and requested message-policy failures SHALL make the result unsuccessful and exit through a stable nonzero validation category while retaining available preview detail.

#### Scenario: Cancellation preview
- **WHEN** a proposed CANCEL uniquely targets a reachable valid decision
- **THEN** check succeeds and reports that the target would change from valid to invalid with score `0.0`

#### Scenario: Invalid effect preview
- **WHEN** a proposed effect has an ambiguous, missing, forward, invalid-index, invalid-factor, or disallowed target
- **THEN** check fails without changing the target and reports a diagnostic identifying the rejected effect

### Requirement: Commit policy checks are opt-in
Check SHALL support `--conventional`, `--max-subject-length <positive-integer>`, and `--require-annotation` independently. Without those options, a nonempty ordinary subject and body SHALL remain valid regardless of conventional-commit shape or subject length.

#### Scenario: Requested conventional policy fails
- **WHEN** `--conventional` is supplied for a message whose subject is not a conventional commit
- **THEN** check fails with a message-policy diagnostic without suppressing annotation diagnostics

#### Scenario: Required annotation is absent
- **WHEN** `--require-annotation` is supplied for an otherwise valid ordinary message
- **THEN** check fails and reports that no zmem annotation was present

### Requirement: Deep checking replays history in isolation
With `--deep`, check SHALL rebuild reachable zmem state in isolation using the current active extension set before evaluating either the proposed successor message or one existing commit supplied as a Git reference. Existing commits SHALL be evaluated after their reachable ancestors and in their historical position. Deep checking SHALL NOT read projected state from or write projected state to the persistent cache.

#### Scenario: Deep proposed-message check
- **WHEN** a proposed effect targets an older reachable entry and check is run with `--deep`
- **THEN** the target is resolved from isolated full-history replay before the proposed message is simulated

#### Scenario: Deep historical check
- **WHEN** check receives `--deep <ref>` for an existing effect-bearing commit
- **THEN** it replays the commit's reachable ancestors, evaluates that commit once, and reports the historical effect outcome

### Requirement: Preview extension execution is side-effect bounded
Check SHALL use supported built-ins and the active trusted expander set, SHALL skip `after_expand` and `after_index` hooks, and SHALL report that hooks were skipped. Repository extensions SHALL remain subject to the repository's persisted extension-trust decision; check SHALL NOT grant trust from a command-line preview option.

#### Scenario: Custom expander preview
- **WHEN** a trusted active expander supports a custom annotation in a proposed message
- **THEN** check includes its context actions while invoking no registered hook

### Requirement: Hypothetical state is not persisted
Check SHALL NOT modify Git, persist its hypothetical commit, actions, effects, relationships, or diagnostics, or advance a repository anchor. A fast check MAY perform the same real-HEAD synchronization that precedes a normal query.

#### Scenario: Query after fast check
- **WHEN** a successful fast check is followed by a query without any new Git commit
- **THEN** the query contains no entry, relationship, diagnostic, or anchor change from the hypothetical message
