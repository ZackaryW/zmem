## 1. Protocol and Metadata Utilities

- [x] 1.1 Add fail-first unit matrices for META parsing, typed operations, declared-key validation, area normalization, hierarchical overlap, null/global behavior, and ancestry-conflict interpretation.
- [x] 1.2 Implement the minimum Python metadata value types, META parser model, area matcher, and protocol/schema constant bump needed to satisfy the focused tests.
- [x] 1.3 Extend extension-context journaling with the typed metadata-patch action while preserving META as a node-consuming non-entry effect and canonical-field ownership.

## 2. Reference-Aware Native Client

- [x] 2.1 Add fail-first client tests for observed ref/OID transmission, typed trail decoding, stale-ref errors, and incompatibility with pre-trail native services.
- [x] 2.2 Extend the native query client boundary to send optional commit-ish selection and preserve the returned trail and metadata fields without coercing JSON types.
- [x] 2.3 Update managed-runtime compatibility and release-selection fixtures for the coordinated protocol/schema identities.

## 3. Public Query Surface

- [x] 3.1 Add fail-first CLI tests for repeatable `--area`, `--ref`, OR-within-area/AND-with-other-filter composition, `<root>`, hierarchy, and global legacy matches.
- [x] 3.2 Implement `--ref` for snapshot queries and repeatable `--area` for recall/search, using the native trail as the authority and leaving conventional `--scope` unchanged.
- [x] 3.3 Extend JSON and human envelopes with typed trail provenance and commit metadata, including structured stale-ref, incomplete-META, and metadata-conflict diagnostics.

## 4. Public Behavior Contracts

- [x] 4.1 Create independently runnable `features/memory-metadata/` and `features/memory-trails/` roots with capability feature files, delegated lifecycle, support entry points, and thin scenario-selected bindings.
- [x] 4.2 Extend the established `features/annotation-vocabulary/` and `features/memory-cli/` roots only for their modified public requirements, retaining focused pure case matrices in unit tests.
- [x] 4.3 Prove RED through the exact affected capability scenarios, implement the smallest public-boundary composition, and run each affected Behave root independently to GREEN.

## 5. Documentation and Complete Verification

- [x] 5.1 Document META syntax and precedence, declared keys, null/global compatibility, affected-area matching, live refs, trail provenance, and the coordinated native release prerequisite.
- [x] 5.2 Run the supported Python lock/sync check, formatter and lint gates, complete unit suite, every capability-owned Behave root independently, and a clean `uv build`.
- [x] 5.3 Verify the installed runtime rejects incompatible protocol/schema pairs and passes an end-to-end query against the paired `zmem-cache` build.
