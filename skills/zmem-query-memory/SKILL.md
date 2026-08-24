---
name: zmem-query-memory
description: Query and rank zmem repository memory using recall, search, show, and links, then verify it against current repository evidence. Use when an agent needs the most relevant, recent, valid decision, lesson, relationship, or provenance before planning, coding, reviewing, or debugging.
---

# Query zmem Memory

Retrieve repository memory as evidence, rank it deliberately, and reconcile it with the repository's current authority.

Read [references/query-contract.md](references/query-contract.md) before constructing queries or interpreting their order.

## Workflow

1. Identify the repository, question, intended Git snapshot, likely event types, conventional scope, affected areas, keywords, and useful recency boundary.
2. Inspect current code, tests, and specifications enough to know what evidence must be corroborated. Memory informs this evidence; it does not override it.
3. Discover available event types with `zmem --repo <path> recall --events` when the vocabulary is uncertain.
4. Start with recent valid context using `zmem --repo <path> recall --since HEAD~50`. When an intended `--ref <commit-ish>` differs from HEAD, use that snapshot and its corresponding `<commit-ish>~50` lower bound. Add event, scope, or repeatable area filters only when the question supplies them.
5. Use `search` after the recent recall pass when the question needs topical text matching or the recalled context is insufficient. Search literally first and use regex only when it improves recall. Use repeatable `--area` when path applicability matters.
6. Avoid a small CLI `--limit` until enough candidates are collected. The CLI does not rank results by relevance or newest time.
7. Rank candidates by direct relevance, selected-snapshot applicability, affected-area overlap, valid state, score, commit time, and proximity to the current code. Use `jq` when JSON structure or sorting matters.
8. Inspect finalists with `zmem --repo <path> show <sha>` under the same `--ref` when one was selected, and add `--diff-content` only when the originating change is needed.
9. Traverse relationships with `links` when provenance or connected entries affect the answer. Add `--trail` to a snapshot command only when its immutable selected-trail identity is needed for provenance or branch verification.
10. If evidence is weak, broaden the recall boundary, synonyms, event types, scope, or affected areas, then repeat. Keep the default attention bounds for ordinary retrieval. When reported attention truncation leaves relevant evidence unresolved, increase one or both limits to finite positive values proportionally and retry. Do not use `--commit-limit -1 --node-limit -1` merely to broaden a query; reserve complete-history traversal for a question that explicitly requires it.
11. Report the answer, relevant SHA/index, typed metadata or conflicts that affected selection, any explicitly inspected trail provenance, and any conflict with current repository evidence. Treat invalid entries as historical audit data only.

## Selection Rules

Prefer, in order:

1. Current authoritative code, tests, and specifications.
2. Valid zmem entries directly answering the question in the intended trail.
3. Exact affected-area, event type, scope, and terminology matches.
4. Higher effective scores after trail-specific effects.
5. More recent commit time and closer applicability to the selected snapshot.
6. Entries whose origin, metadata, and relationships survive inspection.

Do not mutate repository memory, service configuration, or Git history while performing a query-only task.
