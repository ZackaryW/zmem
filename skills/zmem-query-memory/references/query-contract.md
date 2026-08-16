# Query Contract

Place the global `--repo` and optional `--human` arguments before the subcommand. JSON is the default output and should be preserved for structured processing.

## Commands

```text
zmem --repo <path> recall --events
zmem --repo <path> recall --event DECISION --event LESSON_LEARNT --scope <scope> --since <git-ref-or-ISO-time> --limit <n>
zmem --repo <path> search <query> --event DECISION --limit <n>
zmem --repo <path> search <query> --regex --include-invalid
zmem --repo <path> show <sha> --diff-content
zmem --repo <path> links --from <entry-id> --to <entry-id> --min-score <score>
```

The query may demand-start the service and synchronizes the repository through its current `HEAD` before answering.

## Result Semantics

- `recall` returns valid entries only.
- `search` excludes invalid entries unless `--include-invalid` is given.
- Use `--include-invalid` only to audit superseded or cancelled history.
- `show` supplies commit metadata, commit message, annotations, changed paths, and optional diff content.
- `links` exposes relationships and can filter by source, target, and minimum score.
- `--since HEAD~50` is a useful Git-relative boundary; ISO timestamps are also accepted.
- Search literally first. Use `--regex` only when regex semantics are intentional.
- Although `search` accepts `--in`, the current implementation does not distinguish search domains. Do not claim that it narrows content.

Results follow stored insertion history rather than relevance or newest-first ranking, and the CLI applies `--limit` before custom ranking. Gather a sufficiently broad set, then sort or filter it locally.

For example:

```text
zmem --repo . search cache | jq '.results | sort_by(.commit_time, .score) | reverse'
```

Use `jq` with typed JSON fields and fail on invalid JSON when building automation. Confirm the exact response field names from actual output before relying on a reusable filter.

## Interpretation

Use score as one signal, not as truth. A high-score old entry may have lost applicability without an explicit effect. A newer entry may be less authoritative than a checked-in specification. Inspect origin and compare with the current repository before presenting a conclusion.
