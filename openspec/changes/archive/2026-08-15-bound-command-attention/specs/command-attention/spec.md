## Purpose

Defines bounded, explicitly overridable attention windows for every repository command that gathers Git history or zmem annotations.

## ADDED Requirements

### Requirement: Repository attention is dual-bounded by default
Every repository command that gathers a reachable history range SHALL inspect at most the newest 500 Git commits and gather at most 400 syntactically valid zmem annotation occurrences by default. `--commit-limit` and `--node-limit` SHALL accept a positive integer or `-1`; `-1` SHALL disable only its corresponding bound. Commands that resolve one explicit object and commands that do not inspect repository history SHALL remain outside these traversal bounds.

#### Scenario: Default bounded query
- **WHEN** a repository command is invoked without attention overrides against history exceeding both defaults
- **THEN** it inspects no more than 500 commits, gathers no more than 400 annotation occurrences, and reports that its attention view is truncated

#### Scenario: Explicit complete-history attention
- **WHEN** a repository command is invoked with `--commit-limit -1 --node-limit -1`
- **THEN** neither attention dimension truncates its reachable-history view

### Requirement: Environment and command line resolve deterministically
`ZMEM_COMMIT_LIMIT` and `ZMEM_NODE_LIMIT` SHALL override the built-in defaults independently, and an explicitly supplied command-line option SHALL override its corresponding environment value. Zero, values below `-1`, non-integers, and malformed environment values SHALL produce structured invalid-usage or configuration failures rather than silently selecting another limit.

#### Scenario: One explicit limit overrides the environment
- **WHEN** both environment limits are set and the user supplies only `--node-limit 25`
- **THEN** the environment commit limit and explicit 25-node limit form the effective attention policy

### Requirement: Annotation occurrences consume node attention before expansion
Each syntactically valid zmem annotation occurrence SHALL consume one node-attention unit regardless of whether it is built in, custom, unsupported, an entry, DECAY, or CANCEL, and regardless of how many actions its expander emits. Plain prose and hook actions SHALL not consume node attention. Historical selection SHALL prefer the newest commits and SHALL exclude a boundary commit in full when including it would exceed the remaining node budget.

#### Scenario: Effects and unsupported annotations exhaust the node budget
- **WHEN** the newest selected commits contain entry, CANCEL, DECAY, and unsupported annotation occurrences reaching the node limit
- **THEN** every occurrence consumes one unit even though only supported entry annotations can become returned memory rows

#### Scenario: Boundary commit would exceed the node limit
- **WHEN** including the next older commit would make the gathered annotation count exceed the node limit
- **THEN** that entire commit and all older commits are omitted and the bounded view is reported as truncated

### Requirement: Proposed messages participate in node attention
A proposed message supplied to `check` SHALL not consume a historical commit-attention unit, but each of its syntactically valid annotations SHALL consume node attention before historical replay. A proposed message that itself exceeds the node limit SHALL fail without partial expansion.

#### Scenario: Proposed cancellation leaves a smaller history budget
- **WHEN** a proposed message contains one CANCEL under a node limit of 400
- **THEN** at most 399 historical annotation occurrences are selected before the proposed message is evaluated
