## 1. Public Behavior and RED

- [x] 1.1 Create the independently runnable `features/service-management/` capability root with thin public CLI bindings
- [x] 1.2 Prove install/status, isolated paths, rollback, uninstall, and compatibility scenarios fail before implementation

## 2. Runtime Utilities

- [x] 2.1 Add unit-tested zmem-home and runtime-root resolution, binary discovery, checksum, and typed manifest validation
- [x] 2.2 Add unit-tested persistent host assembly and stable staging/previous/active swap behavior
- [x] 2.3 Add unit-tested Windows, macOS, and Linux per-user registration command and artifact generation

## 3. Service Management Wiring

- [x] 3.1 Add `zmem service install`, `start`, `status`, `stop`, `upgrade`, `uninstall`, and `doctor` command parsing and JSON envelopes
- [x] 3.2 Assemble and health-check the stable runtime from explicit, environment, packaged, or PATH native binaries
- [x] 3.3 Implement health-checked upgrade rollback and data-preserving uninstall
- [x] 3.4 Make ordinary memory commands prefer and compatibility-check the managed runtime while preserving development overrides
- [x] 3.5 Make the service-management capability root GREEN through the installed console entry point

## 4. Compatibility and Verification

- [x] 4.1 Run the established memory-cli root and compare recall/show/search/links behavior against the legacy repository target, treating DECAY and CANCEL as intentional additions
- [x] 4.2 Run the supported-interpreter, lock, Ruff lint/format, Python unit, complete service-management Behave, and uv package-build gates
- [x] 4.3 Strict-validate and reconcile the service-management OpenSpec capability
