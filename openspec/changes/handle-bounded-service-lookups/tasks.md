# Tasks

## 1. Typed native contract

- [x] 1.1 Synchronize protocol/schema expectations and versioned native-error fixtures with `../zmem-cache/openspec/changes/isolate-lookups-and-tier-history-indexing` and its `adapt-history-prefetch-to-demand` follow-up (protocol 5/schema 6); verify host-journal, runtime-manifest and release-selection compatibility tests reject mismatches.
- [x] 1.2 Extend ServiceError and native stderr decoding to preserve validated code/retry/job/OID/stage fields; verify tests for not_ready, busy, timeout, stale_ref, failed jobs and malformed errors without string-based classification.
- [x] 1.3 Preserve current CLI error string/category plus structured details and existing service/semantic exit codes; verify JSON-output tests and unchanged successful envelopes including --trail, and document error fields in README.

## 2. End-to-end client budgets

- [x] 2.1 Add positive global --timeout-ms parsing with command-specific defaults and a monotonic remaining-budget utility; verify invalid values and sequential phases cannot reset the budget.
- [x] 2.2 Apply the remaining budget to repository discovery, ref observation, native query/check execution and request-owned show/diff subprocesses; verify stalled Git/native helpers return timeout within execution budget plus bounded cleanup grace.
- [ ] 2.3 Terminate and reap only owned client subprocesses on timeout/interruption while preserving the shared daemon; verify real-process tests on Windows and supported Unix CI plus fast/deep-check timeout classification tests.
- [x] 2.4 Document timeout placement/defaults, cleanup grace and explicit retry semantics; verify example argv parsing and no production polling, attention expansion or hidden retry.

## 3. Behavioral integration and guidance

- [x] 3.1 Update cold-query feature scenarios/helpers to assert not_ready and explicitly await/retry jobs only in test orchestration; verify first registration, moved refs and later exact-trail success against the matching native runtime.
- [x] 3.2 Extend check features to distinguish native delay/overload from completed invalid effects; verify service failures exit 4, conclusive validation exits 5, and hypothetical state remains absent.
- [x] 3.3 Update README and memory-query skill/reference guidance for typed pending/busy/timeout outcomes and native job-status inspection without retry storms; verify references and examples match the implemented CLI contract.

## 4. Coordinated verification

- [x] 4.1 Run uv run pytest and affected behavior suites for memory-cli, commit-checking, command-attention, memory-trails and service-management with the matching backend; record results and resolve regressions.
- [x] 4.2 Validate simultaneous cold indexing, cached lookups and a cancelled deep check in an isolated home; verify user-visible deadline bounds, exact-head provenance, no automatic retry and continued daemon health.
- [x] 4.3 Run uv build and runtime/release compatibility tests; verify native-first release selection and compatible-pair rollback documentation agree with the native companion plan.
