## 1. Behavior contracts

- [x] 1.1 Add independently runnable Behave roots for annotation vocabulary, Python extensions, and memory CLI with shared lifecycle support and thin bindings
- [x] 1.2 Prove RED through the public extension-host and CLI boundaries

## 2. Utility seams

- [x] 2.1 Add unit case matrices for annotation parsing, target references, score validation, envelopes, and error mapping
- [x] 2.2 Add unit case matrices for expansion-context actions, journal validation, deterministic discovery, registration precedence, trust, hashing, and typed protocol validation
- [x] 2.3 Implement the minimum utilities under `zmem/utils` and make focused unit tests GREEN

## 3. Expansion and hooks

- [x] 3.1 Implement `ExpansionContext`, its private typed action journal, and `expand(context) -> None` contracts and registry under `zmem/ext/expander`
- [x] 3.2 Implement read-only hook contracts and registry under `zmem/ext/hooks`
- [x] 3.3 Implement built-in text, DECAY, and CANCEL expanders as context actions plus default read-only hooks under `zmem/builtin`
- [x] 3.4 Implement trusted global and repository extension loading with deterministic extend/overwrite rules
- [x] 3.5 Implement and verify the extension host that executes context actions and serializes the completed private journal through the versioned JSON boundary

## 4. Public CLI wiring

- [x] 4.1 Implement service discovery/startup, automatic repository registration, and fresh-HEAD requests
- [x] 4.2 Implement common JSON/human output and structured exit handling
- [x] 4.3 Implement recall, show, search, and links command arguments and service request mapping
- [x] 4.4 Make each capability-owned Behave root GREEN through the installed command entry points

## 5. Verification and packaging

- [x] 5.1 Run format and lint gates, focused and complete unit tests, and every capability Behave root independently
- [x] 5.2 Build a clean wheel through the declared backend and validate the coordinated protocol fixtures
- [x] 5.3 Update README usage and extension documentation after executable behavior is green
