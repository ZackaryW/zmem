## Context

`zmem` currently resolves one Git top-level, asks `zmem-cache` for the worktree HEAD projection, and applies event, scope, time, validity, and text filters in the Python client. Conventional scope is one scalar inherited by every annotation in a commit. The coordinated native change replaces the single projection with immutable trails and returns typed commit metadata and trail identity through a bumped protocol/schema pair.

## Goals / Non-Goals

**Goals:**

- Query any resolvable Git commit-ish without checking it out, while resolving moving branch names live.
- Filter `recall` and `search` by compact affected areas without hiding legacy null/global memory.
- Add a deterministic META effect that patches only declared commit metadata over a complete branch-aware ancestry range.
- Keep conventional scope, entry identity, content, score, and validity under their existing owners.
- Preserve JSON typing and machine-readable failures across the coordinated protocol bump.

**Non-Goals:**

- A `zmem(TRAIL)` annotation or trail-management CLI.
- Arbitrary metadata keys in the first release.
- Replacing DECAY/CANCEL or conventional commit scope with META.
- Client-side recomputation of changed paths or authoritative branch-to-trail mappings.

## Decisions

### Separate intrinsic scope, affected areas, and metadata overrides

Conventional `scope` remains the parsed commit-header value. `affected_areas` is a nullable set returned by the service: null means global and always matches. `owner` is a nullable string and `tags` is a set of strings. This preserves existing meaning while allowing monorepo provenance and semantic ownership to evolve independently.

### Use repeatable hierarchical area filters

`recall` and `search` accept repeatable `--area`. Repetitions are ORed, then combined with other filters by AND. A bounded stored area matches when it equals, contains, or is contained by the requested repository-relative area. `<root>` matches only root-level provenance; null/global matches every request.

### Make META a typed effect

The syntax is `zmem(META)[<from>, <to>, <operation>, ...]`, where operations are `key=value`, `key+=value`, or `key=null`. `=` replaces, `+=` adds a unique set member, and null resets the key. Only `affected_areas`, `owner`, and `tags` are initially valid; `+=` is invalid for scalar `owner`, and adding to global `affected_areas` leaves it global until `=` narrows it.

META changes metadata only. It never rewrites SHA, annotation index, event type/content, timestamp, conventional scope, score, or validity. META is not queryable as an entry.

### Resolve META ranges against the selected trail

Both endpoints must resolve uniquely, `from` must be an ancestor of `to`, and both must precede the META commit. The inclusive target is every selected commit that is both a descendant of `from` and an ancestor of `to`, including qualifying merged paths. An unavailable endpoint or attention-truncated range rejects the entire patch. A descendant META replaces an earlier value; concurrent conflicting replacements remain diagnostic until a descendant resolution is present.

### Treat refs as selectors and trails as typed query context

Snapshot commands accept `--ref`; omission selects the observed worktree HEAD. Any Git commit-ish is accepted. Local branch names may have cache aliases, but the client always sends the requested selector and observed resolved OID so the service can reject races. Query envelopes include a typed trail summary; no dedicated trail commands are added.

### Coordinate a strict compatibility bump

The Python protocol/schema constants advance with the native service. Install and upgrade continue selecting an exact compatible native release, and an old service is rejected rather than silently dropping META, ref, or affected-area behavior.

## Risks / Trade-offs

- [Broad null/global legacy metadata reduces filtering precision] → Preserve recall correctness and let later META patches narrow legacy ranges explicitly.
- [Hierarchical overlap can return broader results than exact paths] → Cap stored areas and document the conservative matching rule.
- [Git refs can move between client observation and native synchronization] → Send the observed OID and fail with a structured stale-ref result rather than querying a different trail.
- [Generic META syntax can become an unbounded metadata language] → Restrict the first release to three typed built-in keys and explicit operators.
- [Concurrent branch META patches have no natural total order] → Require ancestry or an explicit descendant resolution instead of using arbitrary topology order.

## Migration Plan

1. Publish the protocol/schema-compatible `zmem-cache` release.
2. Update the Python constants, host META parser/expander, client request fields, and typed envelope handling.
3. Verify old managed runtimes are rejected with the existing upgrade direction.
4. Publish the Python release only after the compatible native artifacts exist.

Rollback uses the retained previous runtime only before the new database schema is used. Database downgrade is not promised; recovery remains reconstruction from Git through the supported service version.

## Open Questions

None.
