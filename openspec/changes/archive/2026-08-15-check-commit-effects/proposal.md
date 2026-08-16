## Why

The existing shell validators duplicate only part of zmem's grammar and cannot prove what active expanders, DECAY, or CANCEL would do. Agents and commit hooks need one JSON-first zmem command that validates a proposed message through the same extension and service semantics used by indexing, without creating a commit or persisting hypothetical memory.

## What Changes

- Add `zmem check` for a proposed next-commit message read from a file or standard input.
- Return structured annotation, action, effect, diagnostic, and projected before/after state while treating zero annotations as valid by default.
- Add opt-in conventional-subject, maximum-subject-length, and required-annotation policies.
- Add `--deep` to replay reachable history in isolation before checking a proposed message or an existing commit in its historical position.
- Run the active trusted expanders but skip hooks so validation cannot trigger hook side effects.
- Update the repository-local commit-authoring skill to validate proposed messages with the product command.
- Coordinate the non-persistent effect simulation with the `zmem-cache` service; do not change the separate `zpp` repository.

## Capabilities

### New Capabilities

- `commit-checking`: Defines proposed-message and historical commit validation, structured previews, optional message policies, deep replay, extension behavior, and non-mutating guarantees.

### Modified Capabilities

None.

## Impact

- Affects the Python CLI, service client protocol, extension host invocation, output rendering, public Behave surface, unit tests, and the `zmem-author-commits` skill.
- Requires a compatible `zmem-cache` release that provides fast and deep check operations.
- Does not mutate Git and does not persist the hypothetical commit or run hooks.
