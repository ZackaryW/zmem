# Annotation Vocabulary

## Grammar

Use one annotation per physical line. A leading `- ` or `* ` is accepted for plain entries, but a bare annotation line is preferred in commit bodies.

```text
zmem(DECISION): <non-empty text>
zmem(LESSON_LEARNT): <non-empty text>
zmem(DECAY)[<unique-sha-prefix>, <one-based-index>, <factor>]
zmem(CANCEL)[<unique-sha-prefix>, <one-based-index>]
zmem(META)[<from-commit-prefix>, <to-commit-prefix>, <operation>, ...]
```

Type identifiers are uppercase and may contain digits or underscores after the first letter. Each commit may contain multiple annotations. The parser examines lines independently and ignores ordinary lines that do not contain `zmem(`.

Every line containing `zmem(` consumes an annotation ordinal even when malformed. Keep examples and commentary that mention annotation syntax out of a real commit message unless they are intended annotations.

The first-line conventional-commit scope in `type(scope): ...` becomes the stored scope for plain entries.

## Built-in Semantics

### DECISION

Create a valid plain-text entry with default score `1.0`. Use it for an accepted choice whose rationale or constraint will help later work.

Good:

```text
zmem(DECISION): Cache eviction uses commit time so repository history determines age consistently across machines.
```

Avoid merely restating the change:

```text
zmem(DECISION): Updated the eviction query.
```

### LESSON_LEARNT

Create a valid plain-text entry with default score `1.0`. Use it for evidence-backed knowledge that should influence similar work.

```text
zmem(LESSON_LEARNT): Filesystem modification time changes during restore and cannot represent commit age.
```

### DECAY

Apply a multiplicative score factor from `0.0` through `1.0` to an earlier supported entry while leaving it valid. `DECAY` is an effect and is not stored as a standalone entry.

```text
zmem(DECAY)[a1b2c3d, 2, 0.4]
```

### CANCEL

Invalidate an earlier `DECISION` and reduce its effective score to zero. Cancelling another entry type is semantically invalid. `CANCEL` is an effect and is not stored as a standalone entry.

```text
zmem(CANCEL)[a1b2c3d, 1]
```

### META

Apply typed commit metadata to a complete inclusive ancestry range without creating an entry:

```text
zmem(META)[a1b2c3d, e4f5a6b, affected_areas=b/services, owner=platform, tags+=security]
zmem(META)[a1b2c3d, e4f5a6b, affected_areas=null]
```

The declared keys are `affected_areas`, `owner`, and `tags`. `key=value` replaces a value, `key+=value` adds a unique member to a set-valued key, and `key=null` resets it. Appending to scalar `owner`, using an unknown key, or attempting to change canonical entry fields is invalid. Null `affected_areas` means global applicability; adding an area does not narrow it until `=` supplies a bounded value.

Both endpoints must resolve uniquely in the selected trail, `from` must be an ancestor of `to`, and both must precede the META commit. The effect applies atomically to every selected commit in the complete reachable range. A descendant assignment overrides an ancestor assignment; incomparable conflicting assignments remain diagnostic until a descendant META resolves the key.

## Target Resolution

Find DECAY/CANCEL targets with `zmem search`, `zmem recall`, or `zmem show <sha>`. When branch, tag, or detached history matters, query with the intended `--ref` and confirm the returned trail's resolved OID. Copy the returned SHA and annotation index; confirm that the prefix resolves uniquely, the index is one-based, and the target predates the effect.

Resolve META endpoints from current Git ancestry and the same selected trail. Do not derive branch authority from a remembered alias, and do not submit a range when attention omits any required commit.

Before committing, validate and preview the complete message:

```text
zmem --repo <path> check --file <message-file>
```

For a proposed DECAY, CANCEL, or META, replay selected history before evaluating the file:

```text
zmem --repo <path> check --file <message-file> --deep
```

Repository attention defaults to 500 commits and 400 syntactically valid annotations. DECAY, CANCEL, META, custom, and unsupported annotations each consume one node even when they produce no stored entry. If deep checking reports incomplete attention, raise the global limits before `check` or explicitly request complete replay:

```text
zmem --repo <path> --commit-limit -1 --node-limit -1 check --file <message-file> --deep
```

`ZMEM_COMMIT_LIMIT` and `ZMEM_NODE_LIMIT` override defaults; explicit flags take precedence. To audit an existing effect once in its historical position, use `zmem --repo <path> check <commit-ref> --deep`.

Do not use the plain-entry form for `DECAY`, `CANCEL`, or `META`. Do not invent a target or range based on the visual order of prose in a commit.
