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
4. Query valid entries first. Use `--ref` when the question concerns a branch, tag, or detached commit, and use repeatable `--area` on recall/search when path applicability matters. Start with literal terms and relevant event filters; use regex only when it improves recall.
5. Avoid a small CLI `--limit` until enough candidates are collected. The CLI does not rank results by relevance or newest time.
6. Rank candidates by direct relevance, selected-trail applicability, affected-area overlap, valid state, score, commit time, and proximity to the current code. Use `jq` when JSON structure or sorting matters.
7. Inspect finalists with `zmem --repo <path> show <sha>` under the same `--ref` when one was selected, and add `--diff-content` only when the originating change is needed.
8. Traverse relationships with `links` when provenance or connected entries affect the answer.
9. If evidence is weak, broaden synonyms, event types, scope, or the `--since` boundary, then repeat.
10. Report the answer, relevant SHA/index and trail provenance, typed metadata or conflicts that affected selection, and any conflict with current repository evidence. Treat invalid entries as historical audit data only.

## Selection Rules

Prefer, in order:

1. Current authoritative code, tests, and specifications.
2. Valid zmem entries directly answering the question in the intended trail.
3. Exact affected-area, event type, scope, and terminology matches.
4. Higher effective scores after trail-specific effects.
5. More recent commit time and closer applicability to the selected snapshot.
6. Entries whose origin, metadata, and relationships survive inspection.

Do not mutate repository memory, service configuration, or Git history while performing a query-only task.
