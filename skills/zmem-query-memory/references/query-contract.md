# Query Contract

Place the global `--repo` and optional `--human` arguments before the subcommand. JSON is the default output and should be preserved for structured processing.

## Commands

```text
zmem --repo <path> recall --events
zmem --repo <path> recall --since HEAD~50
zmem --repo <path> recall --event DECISION --event LESSON_LEARNT --scope <scope> --since <git-ref-or-ISO-time>
zmem --repo <path> recall --ref <commit-ish> --area b/sub --area c
zmem --repo <path> search <query> --ref <commit-ish> --area b --event DECISION --limit <n>
zmem --repo <path> search <query> --regex --include-invalid
zmem --repo <path> show <sha> --ref <commit-ish> --diff-content
zmem --repo <path> links --ref <commit-ish> --from <entry-id> --to <entry-id> --min-score <score>
zmem --repo <path> recall --ref <commit-ish> --trail
```

The query may demand-start the service. Without `--ref`, snapshot commands use the observed worktree `HEAD`. With `--ref`, they resolve that Git commit-ish live without checking it out and reject a race if it moved after client observation. Recall, search, show, and links omit the selected-trail identity by default while preserving attention and truncation metadata. Add command-local `--trail` only when the immutable trail, resolved OID, extension identity, or protocol/schema identity is required. A cached local-branch alias is only a hint, never authority.

## Result Semantics

- `recall` returns valid entries only.
- `search` excludes invalid entries unless `--include-invalid` is given.
- Use `--include-invalid` only to audit superseded or cancelled history.
- `show` supplies commit metadata, commit message, annotations, changed paths, and optional diff content.
- `links` exposes relationships and can filter by source, target, and minimum score.
- Queryable entries expose `affected_areas` as a bounded ordered array or null/global, `owner` as a string or null, `tags` as an ordered array, and metadata conflicts as typed data or diagnostics.
- Repeatable `--area` values are ORed with one another and ANDed with other recall/search filters. Equal, parent, and child repository-relative areas overlap hierarchically; `<root>` matches root-level provenance; null/global entries match every area.
- META is an effect rather than a queryable entry. Query results contain its effective trail-specific metadata, while unresolved concurrent assignments remain visible as conflicts.
- Start ordinary retrieval with `recall --since HEAD~50`; ISO timestamps are also accepted. When querying another `--ref`, derive the lower bound from that intended snapshot.
- Use search after recent recall for topical matching. Search literally first and use `--regex` only when regex semantics are intentional.
- Although `search` accepts `--in`, the current implementation does not distinguish search domains. Do not claim that it narrows content.

Results follow stored insertion history rather than relevance or newest-first ranking, and the CLI applies `--limit` before custom ranking. Gather a sufficiently broad set, then sort or filter it locally. Do not recompute changed paths or branch-to-trail mappings in the client; use the native trail and returned metadata as the query authority.

For example:

```text
zmem --repo . recall --since HEAD~50 | jq '.results | sort_by(.commit_time, .score) | reverse'
```

Use `jq` with typed JSON fields and fail on invalid JSON when building automation. Confirm the exact response field names from actual output before relying on a reusable filter.

## Interpretation

Use score as one signal, not as truth. A high-score old entry may have lost applicability without an explicit effect. A newer entry may be less authoritative than a checked-in specification. Inspect origin and compare with the current repository before presenting a conclusion.
