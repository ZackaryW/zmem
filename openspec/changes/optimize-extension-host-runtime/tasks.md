## 1. Public behavior contracts

- [ ] 1.1 Extend the independently runnable python-extensions feature with a scenario-selected public batch-inspection contract
- [ ] 1.2 Extend the independently runnable service-management feature with scenario-selected newest-compatible discovery, incompatible-newer fallback, no-match preservation, and independent-version status behavior

## 2. Batch inspection utilities

- [ ] 2.1 Add fail-first unit cases for strict batch request validation, ordered parser results, and whole-batch failure
- [ ] 2.2 Implement protocol-3 batch inspection by reusing the existing parser without loading extensions or hooks

## 3. Compatible release discovery utilities

- [ ] 3.1 Add fail-first unit case matrices for stable semantic tag parsing, paginated inventory traversal, compatibility/platform filtering, and greatest-version selection
- [ ] 3.2 Implement standard-library GitHub release inventory discovery and feed the selected version into existing manifest and artifact verification
- [ ] 3.3 Add fail-first runtime-manifest cases for independent host/binary versions and version-1 read compatibility
- [ ] 3.4 Implement runtime manifest version 2 without a shared release version and preserve version-1 replacement/upgrade reads

## 4. Public service composition

- [ ] 4.1 Replace Python-package-version remote lookup with compatible release discovery while preserving every local binary precedence path
- [ ] 4.2 Report selected binary and host versions independently and retain exact protocol/schema health checks
- [ ] 4.3 Run the python-extensions and service-management feature roots independently and complete supported-interpreter, lock, Ruff lint/format, pytest, and clean wheel/sdist build gates

## 5. Documentation and release coordination

- [ ] 5.1 Update install, upgrade, compatibility, and runtime metadata documentation without asserting prose through tests
- [ ] 5.2 Coordinate protocol/schema identities and publish the compatible native service before the Python package release
