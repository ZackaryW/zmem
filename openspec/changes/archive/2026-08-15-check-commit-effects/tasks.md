## 1. Public Behavior Contract

- [x] 1.1 Shape independently runnable `features/commit-checking/` scenarios for ordinary, mixed, invalid-effect, policy, non-persistence, trusted-expander, and deep-ref behavior.
- [x] 1.2 Run the new feature root fail-first and record the expected missing-command failures.

## 2. Local Validation Utilities

- [x] 2.1 Add unit case matrices for proposed-message input selection and optional subject, length, and annotation-presence policies.
- [x] 2.2 Implement the minimum commit-message policy and result-composition utilities needed by the public scenarios.
- [x] 2.3 Add host unit coverage and implementation for expansion with hooks explicitly skipped while expanders remain active.

## 3. Public Command Wiring

- [x] 3.1 Extend the native service client request for fast proposed-message and deep proposed/ref checks with actionable compatibility errors.
- [x] 3.2 Add `zmem check` argument validation, stdin/file loading, native result composition, structured JSON output, and stable validation exit behavior.
- [x] 3.3 Update `zmem-author-commits` to invoke `zmem check` and explain when `--deep` is appropriate.

## 4. Verification and Reconciliation

- [x] 4.1 Run focused unit and `features/commit-checking/` GREEN verification.
- [x] 4.2 Run lock, supported-interpreter, lint, format, complete unit and independently runnable Behave roots, and clean package-build gates.
- [x] 4.3 Reconcile the mature behavior into canonical specs and validate the OpenSpec change strictly.
