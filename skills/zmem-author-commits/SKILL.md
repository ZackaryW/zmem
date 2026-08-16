---
name: zmem-author-commits
description: Author or review Git commit messages that combine normal human-readable subjects and bodies with zmem DECISION, LESSON_LEARNT, DECAY, CANCEL, or custom annotations. Use when an agent needs to propose, validate, or, when separately authorized, create a commit carrying durable repository memory without confusing annotations with ordinary commit prose.
---

# Author zmem Commits

Write useful Git history for people first, then add only the durable repository memory that zmem should retain.

Read [references/annotation-vocabulary.md](references/annotation-vocabulary.md) before authoring or changing an annotation.

## Workflow

1. Inspect the repository's commit conventions, working tree, staged diff, and relevant tests or specifications. Do not infer intent from filenames alone.
2. When the work spans multiple responsibilities, plan dependency-ordered incremental commits. Make every commit independently coherent and verifiable, stage only its explicit paths or hunks, and preserve unrelated working-tree changes. Do not split a change where an intermediate commit would knowingly break the repository.
3. Decide whether each commit contains durable memory. Ordinary implementation detail, changelog prose, and diff narration need no annotation.
4. Preserve a normal subject and optional explanatory body. Place each zmem annotation on its own unwrapped body line; annotated and unannotated prose may coexist.
5. Select the narrowest built-in type:
   - `DECISION` for an adopted architecture, policy, constraint, or tradeoff and its reason.
   - `LESSON_LEARNT` for a verified, reusable lesson rather than a guess.
   - `DECAY` when an earlier entry remains valid but deserves less weight.
   - `CANCEL` when an earlier `DECISION` is fully invalid.
6. Resolve every effect target from zmem output. Use the target entry's SHA prefix and one-based annotation index; never guess either value.
7. Write each complete proposed message to a temporary file. For a plain entry, run `zmem --repo <path> check --file <message-file>`. Add `--conventional`, `--max-subject-length 72`, or `--require-annotation` only when those policies were requested.
8. For DECAY or CANCEL, run `zmem --repo <path> check --file <message-file> --deep` so selected history is replayed before the proposed effect. If the result reports incomplete attention, retry deliberately with `zmem --repo <path> --commit-limit -1 --node-limit -1 check --file <message-file> --deep`. Use `zmem --repo <path> check <ref> --deep` only when auditing an existing commit in its historical position.
9. Fix every validation diagnostic before presenting or committing the message. Malformed annotation-like lines still affect annotation indexing; every syntactically valid entry, custom type, DECAY, CANCEL, or unsupported type consumes node attention.
10. Return the proposed commit series, each check outcome, and a short explanation of every annotation choice. Run `git commit` only when the user has separately authorized committing.
11. When commits were authorized and created, inspect each resulting commit with `zmem show <sha>`. Do not amend merely to add or alter memory without authorization.

## Quality Bar

- Keep each entry atomic, specific, and understandable without the current chat.
- Record why a choice matters, not just what the diff already shows.
- Omit annotations when nothing durable was learned or decided.
- Use custom types only after confirming that a registered expander materializes them.
- Never place credentials, tokens, private keys, or other secrets in Git history.

## Mixed Commit Example

```text
feat(cache): protect recent commits during eviction

Evict by committer time while retaining the configurable recent window.

zmem(DECISION): Retention uses committer time because it is stable Git history data.
zmem(LESSON_LEARNT): Database modification time cannot represent historical age.
```
