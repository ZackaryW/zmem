# Adaptive schema compatibility update

The native adaptive-prefetch follow-up moves the database to schema 6 while retaining protocol 5. Runtime selection and native-client fixtures now expect this pair; all 123 client unit tests pass. No release was published. The native-first compatible-pair release order and stopped-daemon rollback/rebuild requirement still apply. This does not close the separate supported-Unix process-reap CI task.

All eight client behavior features also passed against the adaptive schema-6 backend: 60 scenarios and 217 steps. The native change's `benchmarks/rollout_rehearsal.py` verified upgrade preservation, rejection by an incompatible older writer, and stopped-daemon backup restoration with the matching schema-5 binary. These checks used disposable homes only.

# Implementation verification (2026-09-25)

- `uv run --offline pytest`: 123 passed on Windows.
- The five affected behavior feature directories pass: 37 scenarios and 139 steps against the matching local native runtime.
- `uv run --offline ruff check .` and `uv build --offline` pass.
- The concurrent cold-index/deep-check timeout scenario confirms exact-HEAD cached lookup, typed timeout, and continued shared-daemon health.

After updating the schema-three migration scenario to assert the affected area reconstructed from the exact Git trail, all eight client behavior features pass against the matching native runtime (60 scenarios, 217 steps). `uv run --offline pytest -q` passes 123 tests, `uv run --offline ruff check .` passes, and strict OpenSpec validation passes. The migration scenario now verifies that a root-file memory has `<root>` provenance and does not match an unrelated-area filter.

The same eight-feature client suite passed again (60 scenarios, 217 steps) against the final native build after job-state, repository registration and parser-inspection writes moved to its canonical writer.

Task 2.3 remains open until the real-process timeout and reap behavior is exercised in supported Unix CI as well as the completed Windows run.

After the native pre-identity job and shared `add`/fast-check waiter changes, the matching client again passed 123 unit tests and all eight behavior features (60 scenarios, 217 steps). Strict OpenSpec validation also passes. Unix CI process-reap validation remains outstanding.
