# Domain Decoupling Contract

Document ID: `DOMAIN-DECOUPLING-V1`  
Document Role: `CANONICAL_METHOD`  
Repository Plane: `INSTRUCTION`  
Current-state authority: repository `CONTEXT.md`, exact issue/PR metadata, and consumer-owned machine state  
Machine authority: [`../../registry.json`](../../registry.json), consumer binding schemas, deterministic verifiers, receipts, and Git history

This document defines the stable boundary between a portable procedural core and a consumer-owned domain specialization. It is loaded only for Skill, module, binding, adapter, provider-profile, or cross-domain-boundary work. It is not passive context for unrelated tasks.

## 1. Purpose and scope

Domain decoupling preserves one reusable method while allowing each consumer to inject repository facts, terminology, runtime choices, privacy rules, acceptance policy, and stronger constraints.

```text
portable procedural core
→ declared domain ports
→ exact consumer binding
→ trigger-selected domain modules/adapters
→ consumer execution
→ consumer-owned evidence
```

The contract does not require repositories to share an identical physical directory tree. Repositories share route names and interface semantics; each repository maps those interfaces to its own existing directories.

## 2. Document responsibilities

| Route | Owns | Must not own |
|---|---|---|
| [`DOCUMENT_ROUTING.md`](DOCUMENT_ROUTING.md) | route names, loading triggers, hop rules | domain laws or current state |
| [`STATE_MACHINES.md`](STATE_MACHINES.md) | states, events, transitions, terminals | repository binding values |
| `DOMAIN_DECOUPLING.md` | core/port/module/adapter dependency laws | mutable consumer state |
| [`../integration/CROSS_REPO_INTEGRATION.md`](../integration/CROSS_REPO_INTEGRATION.md) | repository planes, binding and release flow | internal module procedure |
| [`../traceability/TRACEABILITY_INDEX.md`](../traceability/TRACEABILITY_INDEX.md) | source → decision → issue → PR → eval → receipt lineage | execution authority |
| nearest `README.md` | local owner, inputs, outputs, State Machine, DAG, data flow, evidence ceiling | machine schema duplication |
| machine contract/verifier/receipt | exact executable decision | explanatory navigation |

## 3. Procedural core

The procedural core belongs in `skills/<name>/SKILL.md` and reusable contracts in `references/`.

A portable core may define:

```text
workflow phases
proof obligations
state transitions
stop conditions
evidence vocabulary
allowed repair classes
domain-port interfaces
module-selection rules
```

A portable core must not contain:

```text
consumer branch or issue numbers
consumer-local paths
product topology
provider sessions or credentials
mutable queue state
consumer release status
live receipts copied from another repository
```

See [`../../skills/README.md`](../../skills/README.md) for the existing Skill directory contract.

## 4. Domain ports

A domain port states what a consumer must supply without naming one consumer implementation.

Example interface:

```yaml
domain_ports:
  - id: repository-context
    required: true
    supplied_by: consumer
  - id: terminology-profile
    required: false
    supplied_by: consumer
  - id: provider-routing
    required: false
    supplied_by: runtime-profile
  - id: acceptance-policy
    required: true
    supplied_by: consumer
```

A port definition includes:

```text
stable port ID
input and output shape
required evidence class
allowed effects
failure vocabulary
default-deny behavior
Human or trusted-operator boundary
```

## 5. Modules and adapters

`modules/` contains reusable, trigger-selected instances or interpretations. Consumer repositories own their concrete adapters, profiles, requirements, bindings, runtime configuration, current state, and receipts.

A module is loaded only when all declared triggers match:

```text
task class
target path or bounded context
repository plane
required port
profile or provider selection
evidence lane
```

Ambiguous routing fails closed. A module cannot become global passive context by directory presence alone.

## 6. Dependency direction

```text
shared procedure defines ports
        ↓
consumer resolves an immutable shared subject
        ↓
consumer supplies domain adapters and stricter policy
        ↓
consumer executes and verifies
        ↓
consumer stores the receipt
```

Forbidden reverse dependencies:

```text
shared core imports a consumer checkout
shared core reads a consumer's mutable queue
shared core depends on a consumer-local symlink
consumer copies and edits the canonical SKILL.md body
consumer reaches into another module's private internals
runtime/provider health is treated as correctness
```

## 7. Constraint monotonicity

A consumer specialization can only preserve or strengthen the shared contract.

```text
ConsumerConstraints       ⊇ SharedCoreConstraints
ConsumerRequiredEvidence  ⊇ SharedRequiredEvidence
ConsumerAllowedEffects    ⊆ SharedAllowedEffects
ConsumerAuthority         ⊆ SharedMaximumAuthority
```

A consumer module may:

```text
add or tighten a constraint
narrow read/write/network effects
add an evaluator or negative control
increase the required evidence class
add a Human Admit boundary
provide domain terminology
select an admitted runtime or provider profile
```

A consumer module must not:

```text
weaken a hard constraint
remove a negative or mutation control
turn deterministic FAIL into advisory success
expand merge, release, permission, or rollback authority
promote fixture evidence to live or production evidence
use mutable main/latest as release identity
```

## 8. Directory ownership map

The canonical shared pattern is:

```text
skills/<name>/
├── AGENTS.md       conditional local route and authority boundary
├── README.md       owner, State Machine, DAG, data flow, evidence ceiling
├── SKILL.md        portable procedure
├── references/     generic contracts and ports
├── modules/        trigger-selected reusable instances
├── scripts/        deterministic mechanisms
├── tests/          positive, hollow, mutation and integration controls
└── evals*/cases*   machine-readable evidence contracts
```

A consumer maps those interfaces to existing consumer-owned directories. It does not need to reproduce this tree.

## 9. State Machine

```text
CLASSIFY_TASK
→ RESOLVE_REPOSITORY_PLANE
→ LOAD_DOMAIN_DECOUPLING_CONTRACT
→ RESOLVE_EXACT_SHARED_BINDING
→ LOAD_NEAREST_DOMAIN_CONTEXT
→ SELECT_TRIGGERED_MODULES
→ VALIDATE_MODULE_MONOTONICITY
→ EXECUTE_PORTABLE_PROCEDURE
→ RUN_CONSUMER_ASSERTIONS
→ EMIT_CONSUMER_RECEIPT
→ CLASSIFY_LEARNING
    ├── DOMAIN_SPECIFIC → KEEP_IN_CONSUMER
    └── GENERIC         → PROPOSE_TO_SHARED
```

Terminal states:

```text
VERIFIED
BLOCKED_MISSING_BINDING
BLOCKED_AMBIGUOUS_MODULE
BLOCKED_POLICY
HUMAN_ADMIT_REQUIRED
FAIL
```

A documentation-only review cannot produce runtime `VERIFIED`.

## 10. End-to-end data flow

```text
task / issue / source proposal
→ root routing
→ nearest bounded-context README
→ exact shared binding
→ portable Skill core
→ selected consumer domain module
→ deterministic and semantic execution lanes
→ consumer assertions
→ consumer-owned receipt
→ completion decision
```

Current facts remain in `CONTEXT.md`, machine bindings, queues, receipts, and exact forge metadata. This stable document contains no current consumer inventory.

## 11. Evidence and receipt boundary

A consumer receipt binds at least:

```text
consumer repository, commit and tree
shared repository, commit/tree/artifact digest
selected Skill and module digests
consumer requirement and binding digests
runtime/profile identity when exercised
evaluator identities and results
evidence class and freshness
allowed effects and observed effects
rollback subject
```

A declaration, path, package installation, symlink, workflow definition, or provider-health check is not execution evidence.

## 12. Generic-learning upstream protocol

A consumer finding is classified before any shared change:

```text
finding
├── repository/domain-specific
│   └── keep in consumer module, context, tests and receipts
└── generic reusable law
    └── open a shared proposal
        → add shared controls
        → obtain shared admission
        → publish immutable shared subject
        → consumer explicitly updates its binding
```

Consumer execution never mutates shared core silently.

## 13. Forbidden couplings

Reject:

```text
consumer names or live issue tables in a portable SKILL.md
absolute host paths in portable documents
two independently editable canonical bodies
a consumer module overriding a shared hard gate
a shared document claiming consumer current state
a binding that resolves only through a local sibling checkout
a generated projection treated as source authority
a domain example loaded for unrelated work
```

## 14. Standard route profile for new repositories

A modular repository uses these same names:

```text
README.md
AGENTS.md
CONTEXT.md
ARCHITECTURE.md
docs/INDEX.md
docs/architecture/AGENTS.md
docs/architecture/DOCUMENT_ROUTING.md
docs/architecture/STATE_MACHINES.md
docs/architecture/DOMAIN_DECOUPLING.md
docs/integration/CROSS_REPO_INTEGRATION.md
docs/traceability/TRACEABILITY_INDEX.md
<governed-directory>/README.md
```

A route that does not apply is present as a thin declaration with `NOT_APPLICABLE` and a reason. Absence is not interpreted as non-applicability.

## 15. Current-state routes

For current implementation, admission, delivery, or runtime status, leave this document and read:

1. repository `CONTEXT.md`;
2. `docs/INDEX.md`;
3. the nearest governed-directory `README.md`;
4. the exact machine binding or manifest;
5. the exact issue/PR/workflow/receipt subject.

Do not refresh this stable contract merely because one consumer branch, issue, provider, or queue changed.
