## Context

The query skill currently tells agents to broaden recall boundaries and filters when evidence is weak, but it does not distinguish bounded expansion from disabling both attention limits. zmem defaults to 500 commits and 400 annotation occurrences and reports whether either bound truncated the view.

## Goals / Non-Goals

**Goals:**

- Make bounded retrieval the normal path.
- Tie any expansion to observed truncation and unresolved evidence.
- Keep complete-history traversal available for exceptional, explicitly justified queries.

**Non-Goals:**

- Change CLI flags, defaults, or attention semantics.
- Change deep commit-checking guidance in `zmem-author-commits`.
- Add executable behavior or duplicate command-attention specifications.

## Decisions

### Add one attention-boundary rule to the skill workflow

Place the guidance next to the existing broadening step so it affects the decision point where an agent might otherwise remove limits. The rule will prefer defaults first, allow deliberate positive increases when truncation blocks the answer, and reserve `--commit-limit -1 --node-limit -1` for a demonstrated complete-history requirement.

Alternative: prohibit unlimited traversal absolutely. Rejected because the CLI intentionally supports complete-history queries and some provenance audits can require them.

Alternative: repeat the full command-attention contract in the skill. Rejected because the canonical specification already owns those semantics and duplicating it would make the skill longer and easier to drift.

## Risks / Trade-offs

- Agents may stop too early when a bounded view is truncated → Require them to increase positive limits proportionally when unresolved relevant evidence remains.
- The exception could become a routine shortcut → Require an explicit complete-history justification rather than merely weak search results.
