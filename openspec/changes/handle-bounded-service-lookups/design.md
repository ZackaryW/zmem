# Design

## Context

See proposal.md and the native companion design. `client.query` and `client.check` call the native executable through `subprocess.run` with no timeout. Query currently recognizes stale refs by substring matching stderr. CLI service failures use exit 4; semantic check failures use exit 5. `observe_ref` and other CLI Git subprocesses also have no timeout. Successful envelopes and strict trail-summary validation are already covered by tests and remain intact.

## Goals / Non-Goals

**Goals:** Keep the user-visible wait bounded, preserve typed service outcomes, and release request-owned client resources.

**Non-Goals:** Retry loops, stale-success fallback, changing attention defaults, native job scheduling, or treating deep checks as cache lookups.

## Decisions

### One remaining budget across client phases

Add global `--timeout-ms` for repository commands, resolved to 2000 ms for recall/show/search/links and 120000 ms for check; reject nonpositive values. Start a monotonic deadline after argument validation and before repository discovery/ref observation. Pass remaining milliseconds to the native query/check command rather than starting a new full budget. Apply remaining time to every request-owned Git subprocess, including show/diff postprocessing, and check the budget before expensive client filtering/output preparation.

Bound native subprocess waiting by remaining time plus at most 1000 ms cleanup grace. Native expiry should ordinarily produce its structured error; the outer timeout is a last-resort bound for a stalled or broken native executable. On outer timeout terminate/reap the client subprocess and its owned children without stopping the shared daemon. Never kill all processes by executable name. Resolve the native executable before spawning and retain existing runtime mismatch errors. Managed service install/upgrade operations retain their separate lifecycle controls; this flag governs repository commands.

### Preserve typed failures with existing exit categories

Parse a native nonzero exit's single JSON stderr error object and validate required types. Retain existing CLI `command`, `category`, and human-readable `error` string; add `code`, `retryable`, and applicable `job_id`, `retry_after_ms`, `requested_oid`, and `stage`. Use category `service` and exit 4 for not_ready/busy/timeout; preserve stale_ref category with exit 4. Malformed/unknown native failures remain service/protocol errors and never fall through to semantic validation or success. Remove substring-based classification for the new compatible protocol; incompatible runtimes get explicit upgrade guidance.

Return not_ready immediately without sleeping, polling, widening attention or retrying. Include the native job reference/retry guidance so callers can retry explicitly or inspect `zmem-svc job-status <id>`. A known failed job is surfaced as failure, not relabeled as indexing. Preserve success envelopes and --trail behavior exactly. Check timeout/service failure returns exit 4 without a fabricated `ok: false` annotation-validation result; conclusive semantic validation continues to use exit 5.

### Coordinated compatibility and verification

Update protocol/schema expectations and native error fixtures with the companion service change. A shared protocol constant also versions Python host journals, so synchronize host/runtime fixtures rather than changing only CLI parsing. End-to-end tests must use a matching native binary in an isolated home. Rewrite existing cold-query setup helpers to explicitly wait for job completion/retry as test orchestration; production commands do not poll.

## Risks / Trade-offs

- Cold commands now exit before an answer exists -> clear job/retry metadata and updated README/query guidance.
- Windows process startup and cleanup add latency -> distinguish configured execution deadline from the bounded cleanup grace; test real subprocess hangs as well as mocked timeout paths.
- Slow caller stdin or output pipes are outside service latency guarantees -> document budget start and avoid claiming hard real-time behavior for terminal I/O; bound all owned computation/subprocess waits.
- Native and Python releases can drift -> matching protocol/schema selection tests and native-first publication; no silent legacy fallback.

## Migration Plan

Implement against `../zmem-cache/openspec/changes/isolate-lookups-and-tier-history-indexing`, then validate both in a disposable home. Publish the matching native release before the Python release selecting it. Document the cold-query behavior change and explicit retries. Rollback requires a compatible client/native pair and the native plan's cache rollback/rebuild procedure.
