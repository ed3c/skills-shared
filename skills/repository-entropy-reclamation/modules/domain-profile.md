# Domain profile

This module defines the ports a consumer resolves when the portable procedure reaches repository-specific facts. It is a routing contract, not passive context and not a catalog of mandatory tools.

## Selection State Machine

```text
TASK_AND_SUBJECT_BOUND
→ REQUIRED_PORTS_DERIVED
→ AVAILABLE_ADAPTERS_OBSERVED
→ TRIGGERS_EVALUATED
    ├── NOT_APPLICABLE
    ├── AMBIGUOUS → BLOCKED
    └── SELECTED
→ CONSTRAINT_MONOTONICITY_CHECKED
→ ADAPTER_IDENTITY_BOUND
→ ADAPTER_EXECUTED
→ RECEIPT_READ_BACK
→ PORT_OUTPUT_ADMITTED
```

An installed tool, repository language, package name, or prior successful run cannot select an adapter by itself.

## Ports

| Port | Consumer supplies | Minimum output | Failure behavior |
|---|---|---|---|
| `repository-instructions` | nearest Agent/architecture/contribution/test rules | exact files and digests read | missing instructions block mutation |
| `corpus-classifier` | production, non-production, generated, vendored, examples, migrations, public packages | path/symbol classification with evidence | ambiguous remains ambiguous |
| `dynamic-entrypoint-resolver` | routes, reflection, registries, DI, plugins, loaders, codegen, serialization, queues/workers/processes | exact reachability findings | unproved reachability blocks change |
| `contract-policy` | public API, persisted data, wire formats, compatibility and migration policy | mutation policy per boundary | product decision becomes Human-owned |
| `safety-policy` | authorization, trust, accessibility, data-loss and resource-quiescence obligations | protected boundary set | protected boundaries fail closed |
| `history-provider` | Git history, ADR/RFC/decision notes, issue provenance | current rationale and supersession evidence | missing rationale lowers confidence |
| `analyzer-set` | compiler/linter/dead-code/dependency/graph tools | candidate evidence only | never self-promotes to deletion proof |
| `verification-carrier` | exact commands, runtime, budgets, fixtures and receipts | decisive/narrow/broad/residue/global evidence | unavailable lane stays `NOT_EXERCISED` |
| `proposal-destination` | Agent Note, ADR, issue, TODO, review comment or another governed route | one durable owner or explicit none | duplicate/superseded proposals are coalesced |
| `delivery-binding` | Tech Lead task DAG, Git Town profile, forge publication and local handoff | exact task/Stack/queue subject | no inferred branches or authority |

## Adapter record

A selected adapter is recorded as consumer-owned data, for example:

```yaml
adapter_id: kotlin-gradle-symbol-and-runtime-profile/v1
subject:
  repository: owner/name
  commit: 40-hex
port: analyzer-set
trigger:
  task_class: repository-simplification
  languages: [kotlin]
  paths: [app/, core/]
implementation:
  commands:
    - [./gradlew, compileKotlin]
    - [rg, -n, candidateSymbol, .]
allowed_effects: [read_repository, write_declared_receipt]
forbidden_effects: [network_egress, mutate_source, publish, merge]
output_contract: entropy-candidate-evidence/v1
evidence_lane: LOCAL
```

The portable core never requires this exact adapter or command.

## Language and framework examples

Examples are discovery hints, not default selections:

```text
TypeScript / Node
  compiler, package exports, runtime registries, route strings, package manager graph,
  installed dead-code/dependency tools

Python
  import graph, entry points, decorators/registries, dynamic imports, migrations,
  type/lint output and repository-native tests

Kotlin / Gradle / Android
  source sets, reflection/serialization, manifest components, ServiceLoader,
  generated code, resources, JNI, build variants and instrumentation/runtime tests

Rust / Cargo
  feature gates, public crate surface, macros/generated code, trait implementations,
  cargo metadata and target-specific compilation
```

Every result is reclassified through production/non-production/ambiguous consumer evidence. Tool output alone never satisfies the consumer proof.

## Note and proposal adapters

A consumer may use:

```text
Agent Note
ADR / RFC / decision record
GitHub or Forgejo issue
inline TODO / FIXME / XXX
review comment
no durable proposal because the candidate was rejected or too small
```

The adapter must preserve unique rationale, strongest counterargument, capability effect, acceptance criteria, risks, current owner, and inbound links. It must not copy one repository's note taxonomy into the portable core.

## Dependency substitution adapter

When replacing hand-rolled infrastructure with a library or platform feature, require:

```text
exact semantic surface covered
residual glue and uncovered behavior
maintenance/adoption/release health
transitive and supply-chain footprint
license and redistribution boundary
implementation + dedicated tests + docs removed
wrapper/migration/tests/docs/dependency burden added
```

A substitution passes only when it removes more obligations than it introduces. A wrapper that relocates the same state machine fails the core's conceptual-reduction law.

## Constraint monotonicity

```text
ConsumerConstraints       ⊇ SharedCoreConstraints
ConsumerRequiredEvidence  ⊇ SharedRequiredEvidence
ConsumerAllowedEffects    ⊆ SharedAllowedEffects
ConsumerAuthority         ⊆ SharedMaximumAuthority
```

Reject an adapter that weakens a protected boundary, changes a `FAIL`/`NOT_EXERCISED` state, hides an ambiguous consumer, omits failed attempts, broadens network/filesystem/secret/forge authority, or makes its own installation proof of applicability.
