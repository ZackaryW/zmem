## MODIFIED Requirements

### Requirement: Check reports semantic outcomes
Check SHALL emit JSON containing its command, success state, mode, evaluated parent or target, annotation count, projected actions, resolved effect outcomes, diagnostics, hook-execution state, and effective attention limits and usage. Effect outcomes SHALL identify the target and its score and validity before and after simulation. Parser errors, unsupported types, invalid or unresolved effects, requested message-policy failures, and attention truncation that prevents a conclusive effect evaluation SHALL make the result unsuccessful and exit through a stable nonzero validation category while retaining available preview detail.

#### Scenario: Cancellation preview
- **WHEN** a proposed CANCEL uniquely targets a reachable valid decision inside the effective attention view
- **THEN** check succeeds and reports that the target would change from valid to invalid with score `0.0`

#### Scenario: Invalid effect preview
- **WHEN** a proposed effect has a conclusive ambiguous, missing, forward, invalid-index, invalid-factor, or disallowed target
- **THEN** check fails without changing the target and reports a diagnostic identifying the rejected effect

#### Scenario: Effect target may be outside attention
- **WHEN** a proposed effect is unresolved after history selection stopped at an attention boundary
- **THEN** check fails with an incomplete-history diagnostic instead of claiming the target is absent from complete history

### Requirement: Deep checking replays history in isolation
`zmem check --file <path> --deep` and the corresponding standard-input form SHALL select the newest reachable history within the effective commit/node attention policy, replay the selected commits parent-before-child in isolated storage using the current active extension set, and then evaluate the proposed message as a hypothetical successor to `HEAD`. An existing commit reference MAY be checked as an additional deep mode after its selected ancestors and SHALL be evaluated exactly once. With both limits `-1`, the selected view SHALL be complete reachable history. Deep checking SHALL NOT read projected state from or write projected state to the persistent cache.

#### Scenario: Deep proposed-file effect check
- **WHEN** a proposed message file contains a CANCEL whose target is inside the selected attention view and check is run with `--deep`
- **THEN** isolated replay resolves the target and reports the projected cancellation without creating a commit or persistent row

#### Scenario: Deep historical check
- **WHEN** check receives `--deep <ref>` for an existing effect-bearing commit
- **THEN** it replays the commit's selected reachable ancestors, evaluates that commit once, and reports whether attention was complete
