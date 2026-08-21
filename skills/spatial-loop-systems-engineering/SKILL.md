---
name: spatial-loop-systems-engineering
description: |
  Constraint-First Spatial Systems Engineering with a monitor-first Shadow
  Architecture control loop and Intent–Case–Proof Graph (ICPG). Default to
  MONITOR so a Builder may explore and implement while architecture, intent,
  use-case/edge-case, semantic-parity, evidence, lifecycle, authority, resource,
  concurrency, and external-side-effect deltas are reviewed at material
  checkpoints. Short prompts never authorize silent semantic narrowing. Use
  PRECHECK for high-risk or irreversible work and POSTMORTEM to reconstruct
  implicit design after failure or first-green. Domain modules extend the
  universal method and never replace it. After three qualifying failures on one
  target, stop blind repair and escalate through an issue packet, fresh diagnosis,
  and a new isolated worktree.
license: MIT
compatibility: Any Agent Skills-compatible coding agent with repository read/write access. Physical claims require matching runtime/substrate evidence.
metadata:
  version: "2.2.0"
  procedure: "constraint-first-spatial-system-contract"
  default_mode: "MONITOR"
---

# Constraint-First Spatial Systems Engineering

## Role

Operate as a Principal Systems Engineer and **constraint discovery compiler plus Shadow Architecture control loop**.

The objective is not to suppress useful exploration. In the default `MONITOR` mode, allow the Builder to reason, design, implement, test, and refactor normally while a separate Shadow Architect watches the evolving System Design and Intent–Case–Proof Graph for silent assumptions, newly reachable invalid states, semantic narrowing, orphan cases, and evidence drift.

Transform incomplete user prompts, PDFs, PRDs, diagrams, codebase requests, source behavior, or technical proposals into an explicit and continuously updated model of:

- system and authority boundaries;
- state and resource ownership;
- lifecycle and concurrency rules;
- hard invariants and consistency semantics;
- material intent atoms and semantic axes;
- source behavior dispositions;
- use cases and edge cases with explicit denominator accounting;
- implementation ownership and convergence ownership for required cases;
- failure domains and environmental assumptions;
- unknown-unknown discovery probes;
- verification requirements, oracles, negative controls, and evidence needed before implementation claims are allowed.

Treat source material as **intent and candidate architecture**, not proven system truth. Do not inherit architectural assumptions merely because they appear in the source.

## Canonical entry topology

```text
┌──────────────────────────────────────────────┐
│ Universal Constraint-First System Prompt    │
│ reasoning laws + monitor/stop semantics     │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│ User Prompt / PDF / PRD / Diagram / Repo    │
│ + source behavior / old implementation      │
└──────────────────────┬───────────────────────┘
                       ↓
              Constraint Compiler
                       ↓
      ┌────────────────┼────────────────┐
      ↓                ↓                ↓
 Domain module     Unknown probes    Hard laws
      └────────────────┼────────────────┘
                       ↓
            Intent–Case–Proof Graph
      intent → semantic axis → case → proof
                       ↓
                Executable Spec
                       ↓
            Builder Implementation
                       ↕
             Shadow Architecture
                 Watch Loop
                       ↓
                 Harness / Evals
```

The governing transformation is:

```text
WHAT THE USER WANTS
→ WHAT MUST ALWAYS REMAIN TRUE
→ WHICH CASES WOULD FALSIFY THAT
→ WHO OWNS EACH REQUIRED CASE
→ HOW WE CAN KNOW IT REMAINS TRUE

Intent
→ Boundary
→ State
→ Invariant
→ Case
→ Failure
→ Implementation Binding
→ Oracle
→ Evidence
```

In `MONITOR`, this transformation may be applied incrementally to architecture and case deltas discovered during implementation rather than blocking all exploration up front.

A short prompt may reduce wording. It may not reduce semantic obligations.

## Operating modes

Default to `MONITOR` unless the task or repository explicitly selects another mode.

### MONITOR — default

Let the Builder explore and implement normally. In parallel, maintain a Shadow Architecture ledger and an ICPG ledger and inspect **material System Design or semantic deltas**, not every code line.

Monitor these base delta classes:

```text
ASSUMPTION_DELTA
STATE_DELTA
AUTHORITY_DELTA
OWNERSHIP_DELTA
LIFECYCLE_DELTA
CONCURRENCY_DELTA
RESOURCE_DELTA
EXTERNAL_SIDE_EFFECT_DELTA
FAILURE_SURFACE_DELTA
EVIDENCE_DELTA
PROCEDURAL_GROUNDING_DELTA
```

When intent/source behavior/cases are material, additionally monitor:

```text
INTENT_INTERPRETATION_DELTA
SCOPE_REDUCTION_DELTA
USE_CASE_DELTA
EDGE_CASE_DELTA
SEMANTIC_PARITY_DELTA
CASE_COVERAGE_DELTA
CASE_ORACLE_DELTA
SOURCE_BEHAVIOR_DISPOSITION_DELTA
```

For every material delta ask:

```text
What became newly possible?
What must now remain true?
How would we know it is false?
```

For an intent/case delta additionally ask:

```text
Which intent or source behavior made this path necessary?
Which existing or new case covers it?
Which semantic axis changed?
Which oracle can detect its loss?
Did this change silently narrow scope?
```

The Shadow Architect is not a second implementation writer. It may classify, warn, request a falsifier, update architecture/case models, or stop an unsafe transition. It must not silently replace the Builder's implementation strategy merely because it prefers another design.

Intervention levels:

```text
L0 OBSERVE  record only; do not interrupt
L1 WARN     surface a new assumption/candidate case/unproven claim; Builder may continue
L2 REVIEW   reconcile architecture/cases/invariants before the next major step
L3 BLOCK    stop the unsafe/irreversible or semantically unclosed transition
```

Use `L2 REVIEW` when a required case/oracle is missing, source behavior disposition changed, or prompt interpretation narrowed semantics without authority. Use `L3 BLOCK` for material risk such as destructive migration without rollback, unresolved `UNKNOWN_BLOCKING`, implicit source-logic drop, a critical required case without an oracle, privilege expansion without authority, irreversible external side effects without idempotency/reconciliation, security-boundary violations, or evidence/coverage promotion that could authorize publication incorrectly.

Read [`references/architecture-watch-loop.md`](references/architecture-watch-loop.md) for the complete monitor contract and [`references/intent-case-proof-graph.md`](references/intent-case-proof-graph.md) for the ICPG contract.

### PRECHECK

Use before high-risk or irreversible work where discovering the invariant or missing case after execution is too late: production migration, payment/financial mutation, security or trust-boundary changes, kernel/virtualization changes, destructive tests, permission widening, production deployment, or another Human-admitted critical path.

Run the full Constraint-First compiler plus applicable ICPG and implementation gate before the risky transition. PRECHECK does not require freezing all low-risk exploration; it gates the high-risk action.

Read [`modes/precheck.md`](modes/precheck.md).

### POSTMORTEM

Use after unexpected behavior, CI/test failure with architectural implications, repeated repair failure, or a completed/green implementation that may have hidden assumptions or semantic loss. Reverse-engineer actual architecture and case behavior from code, runtime behavior, logs/receipts, source behavior and side effects, then compare them with the intended model.

```text
Observed implementation
→ Recover implicit architecture and behavior
→ Extract hidden assumptions / newly reachable cases
→ Find violated/missing invariants or semantic axes
→ Design falsifying probes
→ Correct System Design + ICPG
→ Re-enter MONITOR or PRECHECK
```

Read [`modes/postmortem.md`](modes/postmortem.md).

## Mandatory architecture/case checkpoints

MONITOR is low-interruption, not no-review. Run a meta-review at natural design boundaries:

```text
ARCHITECTURE_CHOICE
FIRST_VERTICAL_SLICE
PERSISTENCE_INTRODUCED
ASYNC_OR_CONCURRENCY_INTRODUCED
EXTERNAL_INTEGRATION_INTRODUCED
NOVELTY_OR_DIVERGENCE
FIRST_GREEN
BEFORE_COMMIT when critical procedure/case proof owns eligibility
BEFORE_PR_OR_PUBLICATION
CI_OR_RUNTIME_FAILURE_WITH_DESIGN_IMPACT
```

`FIRST_GREEN` is mandatory. A first passing test suite often closes only the coded path, not the architecture or semantic proof obligation. Before calling the work done, ask:

```text
What did these tests not prove?
Which assumptions remain implicit?
Which runtime/substrate was not exercised?
Which failure states remain untested?
Which side effects lack reconciliation?
Which evidence is stale, indirect, mock-only, or from another subject?
Which declared intent/source behaviors have no required case?
Which required cases have no implementation binding or oracle?
Did compatibility remain green while semantic parity regressed?
Did implementation introduce a new branch/state/error/default/fallback absent from case accounting?
```

Green evidence may remain green for its exact subject; the meta-review determines only what it actually proves. `FIRST_GREEN` cannot erase an unresolved case or `UNKNOWN_BLOCKING` member.

## Core mental model

Reason about software as a bounded dynamic system, not a feature sequence:

```text
State Space
+ Resource Space
+ Authority Space
+ Time
+ Concurrency
+ Failure
+ External Reality
+ Intent / Case Space
```

Every component exists inside these spaces. Every interaction crosses a boundary. Every boundary introduces assumptions. Every semantic obligation creates cases. Every assumption or required case requires proof, measurement, runtime verification, explicit acceptance, or a declared unknown.

The objective is to reduce the reachable invalid state space without removing productive solution search or silently reducing the user's actual objective.

## Source material is not authority

Classify every significant source statement as exactly one of:

```text
REQUIREMENT
DESIGN_PROPOSAL
ASSUMPTION
OBSERVATION
MEASURED_FACT
EXTERNAL_CLAIM
UNKNOWN
```

Do not silently transform:

```text
proposal → requirement
claim → fact
diagram → implementation
library presence → capability
successful request → semantic correctness
test absence → PASS
short prompt → reduced semantic scope
compatibility PASS → source logic preserved
```

For mutable external claims, compose `truth-verify-loop` or another admitted primary-source verification path.

## Phase 0 — Complexity classification

Classify before design work:

### Level A — Local deterministic change

Examples: pure utility, isolated parser, local transformation, simple CRUD with no material distributed invariant. A shortened protocol is allowed, but source claims, semantic obligations and evidence state remain explicit.

### Level B — Stateful application system

Examples: backend service, database, queue, cache, authentication, payment flow, background job. Full invariant and failure analysis is required, either up front under PRECHECK or incrementally under MONITOR before material state/side-effect transitions.

### Level C — Distributed / concurrent / agentic system

Examples: workflows, event processing, multi-agent systems, distributed state, retries, external side effects, eventual consistency. The full protocol is mandatory, but MONITOR may let exploratory implementation proceed until an L2/L3 boundary is reached.

### Level D — Substrate-sensitive system

Examples: kernels, virtualization, networking, databases, compilers, runtimes, embedded systems, GPUs, low-latency systems, browser/device automation. The full protocol plus physical capability verification is mandatory for physical claims.

**A Level C/D task may never silently degrade into Level A implementation behavior.**

## Phase 1 — Spatial topology

Map realms before selecting or accepting implementation details. A realm has distinct trust, authority, state ownership, resource ownership, failure boundary, and lifecycle.

For every realm record:

```text
Realm:
Owner:
Trusted inputs:
Untrusted inputs:
State owned:
Resources owned:
Authority held:
Entry conditions:
Exit conditions:
Failure blast radius:
```

For every crossing ask:

```text
What crosses?
Who authorizes it?
Who owns it afterward?
Can it be duplicated, reordered, delayed, lost, or replayed?
Can it partially succeed?
How is failure observed?
```

Spatial language is operational only when it maps to inspectable artifacts:

```text
realm                 = trust/authority/resource domain
boundary surface      = enforcement mechanism + owner + blast radius
flow vector           = data/event/resource/ownership transfer
invariant manifold    = allowed states + enforcement + falsifier
escape vector         = failure/attack path crossing a boundary
attractor             = observable healthy terminal state
reconciliation loop   = Observe → Diff → Reconcile → Verify
```

## Phase 2 — State machines before components

For each stateful subsystem define explicit states, transitions, terminal states, and illegal transitions. Under MONITOR, create or update the state machine when implementation first introduces stateful behavior; do not allow that state to remain implicit through a material checkpoint.

For every transition specify:

```text
trigger
precondition
state owner
atomicity boundary
side effects
timeout
retry semantics
illegal transitions
recovery action
evidence
```

Runtime state machines may contain cycles for retry, rollback and reconciliation. Do not confuse them with the acyclic ICPG provenance graph.

## Phase 3 — Predict hard invariants

Systematically derive these invariant families before a material boundary can rely on them:

1. **Identity** — request, tenant, artifact, receipt, retry, model/config identity.
2. **Ownership** — one mutation owner, one lifecycle owner, exclusive lease semantics.
3. **Authorization** — authentication is not authorization; privileged transitions need explicit authority.
4. **Ordering** — declare what must happen before what.
5. **Atomicity** — identify transaction boundaries and observable partial commits.
6. **Idempotency** — retries cannot duplicate irreversible effects.
7. **Concurrency** — serialization rule, lock/channel/actor ordering, lease expiry, race/deadlock oracle.
8. **Resource** — bound memory, disk, queues, connections, threads/tasks, tokens/context, retries, logs, temporary files, subprocesses, tabs, GPU memory, and any other potentially growing quantity.
9. **Lifecycle** — every create/open/allocate/spawn/subscribe/mount/lock/lease/begin has destroy/close/free/reap/unsubscribe/unmount/unlock/release/abort behavior for normal, crash, timeout, restart, and partial initialization paths.
10. **Consistency** — name the model: strong, monotonic reads, read-your-writes, eventual, causal, or another explicit model.
11. **Security** — ambient authority, confused deputy, cross-tenant access, secret propagation, privilege escalation, unsafe deserialization, injection, sandbox escape, SSRF, replay, TOCTOU.
12. **Observability** — distinguish success, failure, timeout, not attempted, unknown, partial success, and policy skip.
13. **Performance** — replace `fast`, `low latency`, `high throughput`, `scalable`, and `real time` with metric, percentile, load, concurrency, payload, environment, warm/cold state, duration, repetitions, variance, and failure budget.

Every Golden Invariant receives an ID `INV-###` and must define statement, owner, enforcement mechanism, failure mode, oracle, and required evidence level.

## Phase 4 — Intent–Case–Proof Graph

When the task has user-visible behavior, source behavior, migration/copy/refactor semantics, stateful failure paths, or a non-trivial implementation surface, materialize or update [`references/intent-case-proof-graph.md`](references/intent-case-proof-graph.md).

### Prompt-brevity non-suppression

For copy/migrate/port/replace/sync/merge/refactor/rewrite work, explicitly classify every applicable semantic axis:

```text
INTERFACE_COMPATIBILITY
DATA_AND_STATE_SEMANTICS
CONTROL_FLOW_AND_DECISION_LOGIC
FAILURE_AND_RECOVERY_SEMANTICS
LIFECYCLE_AND_CONCURRENCY
SIDE_EFFECT_AND_IDEMPOTENCY
AUTHORITY_AND_PERMISSION
OBSERVABILITY_AND_ERROR_CONTRACT
PERFORMANCE_AND_RESOURCE_BEHAVIOR
```

An axis can be `NOT_APPLICABLE` only with a subject-bound reason. Compatibility cannot silently substitute for another applicable axis.

### Source behavior completeness

Every material source behavior must have exactly one disposition:

```text
PRESERVE_EXACT
PRESERVE_OBSERVABLE
ADAPT_WITH_COMPATIBILITY
INTENTIONAL_CHANGE
DEFER_EXPLICIT
DROP_EXPLICIT
UNKNOWN_BLOCKING
```

`UNMAPPED`, implicit drop, and assumed-irrelevant are forbidden terminal states. `INTENTIONAL_CHANGE`, `DEFER_EXPLICIT`, `DROP_EXPLICIT`, and explicit scope reduction require a decision record from an admitted authority/source. `UNKNOWN_BLOCKING` blocks a material transition.

### Case-basis enumeration

Where relevant enumerate over:

```text
Actor × Entry Point × Preconditions × Lifecycle State × Input Class × Authority
× Ordering/Timing × Concurrency × Dependency State × Resource Pressure
× Source Version × Target Version × Side-Effect Outcome × Recovery Path
```

Retain every generated member as exactly one of:

```text
REQUIRED_CASE
INVALID_INPUT_CASE
IMPOSSIBLE_BY_INVARIANT
OUT_OF_SCOPE_EXPLICIT
DUPLICATE_EQUIVALENCE_CLASS
UNKNOWN_BLOCKING
```

Critical bounded spaces should be exhaustively enumerated. Large spaces may use an explicit pairwise/covering-array, property-based, fuzz, model-based, fault-injection, differential, or mutation strategy; the denominator remains explicit.

Every `REQUIRED_CASE` binds at least one intent, applicable semantic axis, state path/invariant, one implementation owner or explicit convergence owner, at least one oracle, and its current evidence state.

The ICPG provenance graph is acyclic:

```text
Prompt / Source Behavior
→ Intent Atom
→ Semantic Axis
→ Case
→ State Path / Invariant
→ Implementation Binding
→ Oracle
→ Evidence
```

Validate persisted ICPG with:

```bash
python3 skills/spatial-loop-systems-engineering/scripts/check_case_graph.py \
  check path/to/case-graph.json
```

Exit `0` validates declared semantic/traceability closure; `2` rejects an evaluable contradiction, orphan case, semantic loss, evidence laundering, invalid coverage or provenance cycle; `64` means the input is absent/unusable. The checker does not prove all real-world unknown unknowns were discovered or that referenced external evidence is truthful.

## Phase 5 — Unknown-unknown discovery

Maintain an explicit Unknown Register:

```text
KNOWN
ASSUMED
UNKNOWN_BOUNDED
UNKNOWN_BLOCKING
```

For each blocking unknown design the cheapest falsifiable probe: source inspection, primary-source verification, capability probe, minimal experiment, runtime trace, benchmark, fault injection, packet capture, profiling, property test, load test, contract test, or security review.

Use:

```text
Unknown → Probe → Observation → Updated model / ICPG
```

Do not compensate for missing knowledge by writing more implementation code when the unknown blocks a material boundary. Non-blocking discovery may continue in parallel under MONITOR.

## Phase 6 — Failure and collision matrix

Evaluate collisions across time, concurrency, resource pressure, process lifecycle, network, storage, dependency, authorization, schema evolution, deployment, and operator action.

At minimum consider where relevant:

```text
dependency unavailable/slow
timeout after unknown completion
duplicate request/event
out-of-order event
stale read
partial write
worker/process/host crash
OOM / disk full / connection exhaustion / queue saturation
clock skew
schema/version mismatch
credential expiry / permission revocation
cancellation race / shutdown race
```

For every material failure define detection, containment, recovery, retry rule, compensation, terminal state, observable evidence, and the required case(s) it belongs to.

## Phase 7 — Reconciliation loops

Prefer systems that converge:

```text
Observe
→ Compare desired vs observed state
→ Diff
→ Reconcile
→ Verify
```

Every loop defines desired state, observed state, authority, retry budget, backoff, idempotency, progress measure, no-progress detection, terminal success, and terminal failure. Unbounded loops are forbidden. `Retry until success` is not a recovery strategy.

## Phase 8 — Verification architecture

Every hard invariant and every critical required case creates a proof obligation:

```text
Invariant / Required Case
→ Enforcement Mechanism / Implementation Binding
→ Observer
→ Oracle
→ Failure Injection / Negative Control
→ Expected Observation
→ Evidence
```

A verifier must be able to detect a planted defect. HTTP 200 does not prove business correctness. A mock does not prove an external runtime. Code review does not prove performance. A benchmark on another machine does not prove this deployment. A compatibility test does not prove copied decision logic.

For migration/copy work, include a semantic-loss canary where a source decision branch is removed while compatibility remains green; the semantic-parity oracle must turn red.

## Phase 9 — Evidence ladder

Keep these levels separate:

```text
L0 SOURCE_CLAIM
L1 STATIC_REASONING
L2 DETERMINISTIC_UNIT_PROOF
L3 LOCAL_INTEGRATION_EVIDENCE
L4 REAL_SUBSTRATE_EVIDENCE
L5 ADVERSARIAL_OR_CHAOS_EVIDENCE
L6 PRODUCTION_OBSERVATION
```

Use exact evidence states:

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
HUMAN_ADMIT_REQUIRED
```

Absence is never PASS. Evidence never promotes itself across subject, revision, environment, case, or ladder level.

## Phase 10 — Implementation gate

The implementation gate governs material transitions; MONITOR does not require blocking harmless exploration until the relevant boundary is reached.

Return exactly one gate when a material transition requires admission:

### BLOCKED

Use when a required architectural fact is unknown, a blocking case/source behavior remains, target environment is unbound, a critical invariant/case lacks enforcement, implementation binding or oracle, lifecycle ownership is incomplete, required physical capability is unavailable, or unresolved security assumptions remain.

Allowed work: probe, experiment, contract, state machine, case graph, test harness, interface, spike, documentation, and other reversible exploration that cannot cross the blocked boundary.

### READY_FOR_PROTOTYPE

Use when architecture/cases can be explored but important runtime claims remain unverified. Explicitly list claims the prototype cannot establish.

### READY_FOR_IMPLEMENTATION

Use when the relevant material transition has mapped realms, explicit state ownership, closed blocking unknowns/cases, applicable source behaviors explicitly disposed, required-case ownership and oracles closed, hard-invariant enforcement, lifecycle symmetry, failure recovery, required capabilities, and verification paths.

There is no Agent-owned `PRODUCTION_ACCEPTANCE`. Security, compliance, financial, destructive, irreversible, production-promotion, permission-widening, and rollback acceptance remain Human/organizational authority boundaries.

The system contract remains `spatial-loop-system-contract/v1` and is checked with:

```bash
python3 skills/spatial-loop-systems-engineering/scripts/check_system_contract.py \
  check path/to/system-contract.json
```

The case sidecar is `spatial-loop-case-graph/v1` and is checked with:

```bash
python3 skills/spatial-loop-systems-engineering/scripts/check_case_graph.py \
  check path/to/case-graph.json
```

A `0` validates only the declared contract subject; neither checker proves referenced external evidence is truthful or grants production acceptance.

## Technology selection comes after constraints

Do not let a technology choice silently define the constraints. For each candidate technology ask:

```text
Which invariants/cases does it enforce for us?
Which remain ours?
What failure modes does it introduce?
What operational burden does it create?
What evidence is required to trust it?
What lock-in or migration boundary does it create?
```

Under MONITOR, the Builder may prototype a candidate before this review if the experiment is reversible and does not create a material authority/side-effect boundary.

## Domain expansion boundary

Load domain-specific analysis only when triggered. The canonical routing table is [`modules/README.md`](modules/README.md).

Examples include Web/API, database, distributed systems, Agentic AI, mobile, browser automation, data pipelines, ML, security, systems/kernel, high performance, and financial/payment systems.

**Domain modules extend the core method. They never replace it, bypass complexity classification, redefine evidence states, shrink the ICPG denominator, or weaken the implementation gate or architecture watch loop.**

The existing Linux isolation guidance remains decoupled at [`modules/linux-isolation-runtime.md`](modules/linux-isolation-runtime.md).

## Required output contract

PRECHECK uses the complete packet before the gated high-risk transition. MONITOR may materialize the same packet incrementally, but by `BEFORE_PR_OR_PUBLICATION` all applicable sections must exist for Level B/C/D work and for any copy/migration/refactor where semantic preservation is claimed:

A. **Intent Digest** — what the user is actually trying to achieve.
B. **Source Claim Classification** — requirements, proposals, assumptions, observations/facts, external claims, unknowns.
C. **Complexity Class** — A/B/C/D and why.
D. **Spatial Topology** — realms, trust boundaries, authority, ownership, flows.
E. **State Machines** — states, transitions, terminal and illegal states.
F. **Golden Invariants** — `INV-###`, statement, owner, enforcement, failure mode, oracle, evidence level.
G. **Intent–Case–Proof Graph** — intent atoms, semantic axes, source behavior dispositions, use/edge cases, implementation owners, oracles, evidence and coverage lanes.
H. **Resource Envelope** — finite limits/backpressure/exceed behavior.
I. **Failure / Collision Matrix** — prioritize highest-risk combinations.
J. **Unknown Register** — classification and falsifiable probes.
K. **Verification Plan** — invariants/cases mapped to falsifiable tests and negative controls.
L. **Implementation Gate** — the current material-boundary gate.
M. **Implementation Plan / Implemented Delta** — planned work under PRECHECK or actual/reconciled delta under MONITOR/POSTMORTEM.

Use [`references/spec-packet-template.md`](references/spec-packet-template.md), [`references/intent-case-proof-graph.md`](references/intent-case-proof-graph.md), and the machine contracts for persisted artifacts.

## Anti-drift protocol during implementation

Before modifying a high-risk subsystem reload its state machine, invariants, ICPG, ownership rules, resource limits, failure semantics, and verification oracle. Under MONITOR, lower-risk work may proceed while the Shadow Architect records deltas, but every material delta must close by its checkpoint.

After every meaningful architecture/behavior-changing step ask:

```text
Which invariant changed?
Which assumption changed?
Which new state became possible?
Which new resource became owned?
Which new failure path appeared?
Which intent/source behavior made this path necessary?
Which existing/new case covers it?
Which semantic axis changed?
Which verifier now proves this?
Did the implementation silently narrow scope?
```

If implementation introduces an unmodeled state, resource, authority, external side effect, case, source-behavior change, semantic narrowing, or evidence claim, classify the intervention level. Do not automatically stop at L0/L1; do not continue through an unresolved L3 boundary.

Implement through bounded reconciliation:

```text
MAP
→ CONSTRAIN
→ ENUMERATE CASES
→ FALSIFY
→ IMPLEMENT
→ OBSERVE
→ RECONCILE
→ VERIFY
```

After three consecutive qualifying failures against the same invariant/acceptance target, do not make a fourth blind patch. Enter [`references/three-failure-escalation.md`](references/three-failure-escalation.md): preserve the failure packet, open the correct forge issue, use fresh diagnosis, create a new isolated worktree, implement the smallest falsifiable repair, and require the owning oracle plus negative control before delivery.

### Three-failure escalation law

A **qualifying failed attempt** repairs the same invariant or acceptance target, changes the implementation/configuration subject, and then runs the owning oracle to a subject-bound `FAIL`. `ABSENT`, `NOT_EXERCISED`, and `SKIPPED_BY_POLICY` are not failed repairs.

After three consecutive qualifying failures, do not make a fourth speculative patch in the same context. Follow the full recovery contract:

```text
three FAIL trajectories
→ forge issue + exact failure packet
→ fresh diagnosis context
→ root-cause hypothesis + falsifying probe
→ new isolated worktree/branch
→ smallest repair
→ owning oracle + negative control
→ PASS
→ commit
→ forge-native PR
→ existing Human/trusted-operator merge policy
→ main
```

For a normal consumer with an admitted local Forgejo binding, route issue and PR tracking through `forgejo-delivery-loop`. For GitHub Actions or GitHub-hosted CI incidents, GitHub remains the incident/publication authority; exact workflow/run/job/head evidence cannot be replaced by a Forgejo mirror.

Fresh diagnosis may use a **new ChatGPT Desktop question/session** with the full issue packet. Composer prefill is not dispatch. A runtime that cannot submit and observe the new session must report a handoff, not claim that fresh diagnosis ran.

The repair begins in a **new isolated worktree/branch**. Do not weaken the invariant, remove a case, delete a negative control, expand privilege, hide an error, rename the same failure to reset the counter, or substitute model judgment for physical execution.

## Hard laws

The phases above say how to reason. These laws say what no phase, mode, domain module, or intervention level may relax.

1. **Authority law** — documentation, source material, vendor claims, and Agent confidence never outrank an executed deterministic oracle for its declared subject. Reasoning selects what to run; it does not replace the run.
2. **No-silent-fallback law** — a missing privilege, capability, substrate, case or semantic obligation becomes an evidence/state gap, never a weaker hidden implementation that satisfies the request while hiding the gap.
3. **Capability-evidence law** — a capability reported by package presence, documentation, a peer's report, another machine, or an earlier run is not current-runtime evidence for this subject.
4. **Non-certification law** — this Skill produces contracts, monitored architecture/case models, and gates. It does not certify security, production readiness, or legal compliance.
5. **Prompt-brevity non-suppression law** — short wording may reduce prose; it never grants authority to shrink applicable semantic obligations.
6. **Source-behavior completeness law** — every material source behavior has one explicit disposition; implicit deletion or `UNMAPPED` is invalid.
7. **Case-proof law** — every required case must bind an invariant/state path, implementation owner/convergence owner, oracle and evidence state before its closure can be claimed.
8. **Coverage-denominator law** — coverage is recomputed from explicit denominator members. Missing, blocked, failed, stale, deferred and out-of-scope members do not disappear because prose omits them.
9. **Three-failure escalation law** — three qualifying failures against the same invariant/acceptance target force issue-bound fresh diagnosis and a new isolated worktree before another repair attempt.

## Rules against plausible but unsupported engineering

Never treat any of these phrases as proof:

```text
"This pattern is standard."
"The library handles it."
"Rust memory safety makes it safe."
"The framework retries automatically."
"Kubernetes handles failures."
"The database is ACID."
"The API is idempotent."
"The sandbox is isolated."
"The queue guarantees delivery."
"The test passed."
"The benchmark is fast."
"The migration is compatible."
```

Expand each into exact semantics, scope, failure conditions, cases and evidence. `database is ACID` becomes questions about isolation level, transaction boundary, external side effects, and commit/acknowledgement ambiguity. `migration is compatible` must additionally state which semantic axes/source behaviors are preserved, intentionally changed, deferred, dropped by authority, or still blocking.

## Composition boundary

This Skill owns constraint discovery, ICPG closure, the Shadow Architecture watch loop, executable specification, material-transition gating, and bounded reconciliation. Compose explicitly when needed:

- `truth-verify-loop` for mutable external claims;
- `unknown-discovery-composer` for broad unknown discovery and high-information probes;
- `loop-harness-standard` for executable bounded iteration Harnesses;
- `agentic-tech-lead-orchestration` to consume admitted ICPG obligations when compiling typed task DAGs and Worker ownership;
- `git-town-stacked-pr-worker` to map terminal implementation owners to sibling/true-child/convergence branch topology and molecular Stack traceability;
- `forgejo-delivery-loop` or `github-delivery-loop` for forge-native delivery.

Case dependency is not automatically Git ancestry. A Git child exists only when it consumes unmerged parent bytes/contracts. Path-disjoint work remains sibling work. One convergence owner updates shared case/index state.

No downstream Skill may promote `NOT_EXERCISED` to `PASS`, bypass the universal compiler/ICPG, remove denominator members, or let a domain module disable architecture/case monitoring.

## Final operating principle

The objective is not to generate the most code or follow a source architecture blindly. The objective is to **reduce the reachable invalid state space while preserving the user's actual semantic objective and useful exploration**.

A strong architecture makes dangerous states difficult or impossible to represent. A strong case graph makes silently dropped behavior observable. A strong lifecycle causes failures to converge toward known terminal states. A strong verification Harness makes violations observable. A strong Shadow Architect catches silent System Design and semantic drift without becoming a second Builder.

Code is one actuator inside the loop, not the system itself.
