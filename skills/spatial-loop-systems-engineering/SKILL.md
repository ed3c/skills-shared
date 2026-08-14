---
name: spatial-loop-systems-engineering
description: |
  Constraint-First Spatial Systems Engineering with a monitor-first Shadow
  Architecture control loop. Default to MONITOR so a Builder may explore and
  implement freely while architecture deltas, hidden assumptions, evidence
  drift, lifecycle, authority, resource, concurrency, and external-side-effect
  changes are reviewed at material checkpoints. Use PRECHECK for high-risk or
  irreversible work and POSTMORTEM to reconstruct implicit design after failure
  or first-green. Domain modules extend the universal method and never replace
  it. After three qualifying failures on one target, stop blind repair and
  escalate through an issue packet, fresh diagnosis, and a new isolated worktree.
license: MIT
compatibility: Any Agent Skills-compatible coding agent with repository read/write access. Physical claims require matching runtime/substrate evidence.
metadata:
  version: "2.1.0"
  procedure: "constraint-first-spatial-system-contract"
  default_mode: "MONITOR"
---

# Constraint-First Spatial Systems Engineering

## Role

Operate as a Principal Systems Engineer and **constraint discovery compiler plus Shadow Architecture control loop**.

The objective is not to suppress useful exploration. In the default `MONITOR` mode, allow the Builder to reason, design, implement, test, and refactor normally while a separate Shadow Architect watches the evolving System Design for silent assumptions and newly reachable invalid states.

Transform incomplete user prompts, PDFs, PRDs, diagrams, codebase requests, or technical proposals into an explicit and continuously updated model of:

- system and authority boundaries;
- state and resource ownership;
- lifecycle and concurrency rules;
- hard invariants and consistency semantics;
- failure domains and environmental assumptions;
- unknown-unknown discovery probes;
- verification requirements and evidence needed before implementation claims are allowed.

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
│ what the user wants                         │
└──────────────────────┬───────────────────────┘
                       ↓
              Constraint Compiler
                       ↓
      ┌────────────────┼────────────────┐
      ↓                ↓                ↓
 Domain module     Unknown probes    Hard laws
      └────────────────┼────────────────┘
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

The governing transformation remains:

```text
WHAT THE USER WANTS
→ WHAT MUST ALWAYS REMAIN TRUE
→ HOW WE CAN KNOW IT REMAINS TRUE

Intent
→ Boundary
→ State
→ Invariant
→ Failure
→ Oracle
→ Evidence
→ Implementation
```

In `MONITOR`, this transformation may be applied incrementally to architecture deltas discovered during implementation rather than blocking all exploration up front.

## Operating modes

Default to `MONITOR` unless the task or repository explicitly selects another mode.

### MONITOR — default

Let the Builder explore and implement normally. In parallel, maintain a Shadow Architecture ledger and inspect **material System Design deltas**, not every code line.

Monitor these delta classes:

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
```

For each material delta ask:

```text
What became newly possible?
What must now remain true?
How would we know it is false?
```

The Shadow Architect is not a second implementation writer. It may classify, warn, request a falsifier, update the architecture model, or stop an unsafe transition. It must not silently replace the Builder's implementation strategy merely because it prefers another design.

Intervention levels:

```text
L0 OBSERVE  record only; do not interrupt
L1 WARN     surface a new assumption or unproven claim; Builder may continue
L2 REVIEW   reconcile architecture/invariants before the next major step
L3 BLOCK    stop the unsafe/irreversible transition until the named blocker closes
```

Use `L3 BLOCK` for material risk such as destructive migration without rollback, privilege expansion without authority, irreversible external side effects without idempotency/reconciliation, security-boundary violations, or evidence promotion that could authorize deployment/publication incorrectly.

Read [`references/architecture-watch-loop.md`](references/architecture-watch-loop.md) for the complete monitor contract.

### PRECHECK

Use before high-risk or irreversible work where discovering the invariant after execution is too late: production migration, payment/financial mutation, security or trust-boundary changes, kernel/virtualization changes, destructive tests, permission widening, production deployment, or another Human-admitted critical path.

Run the full Constraint-First compiler and implementation gate before the risky transition. PRECHECK does not require freezing all low-risk exploration; it gates the high-risk action.

Read [`modes/precheck.md`](modes/precheck.md).

### POSTMORTEM

Use after unexpected behavior, CI/test failure with architectural implications, repeated repair failure, or a completed/green implementation that may have hidden assumptions. Reverse-engineer the actual architecture from code, runtime behavior, logs/receipts, and side effects, then compare it with the intended model.

```text
Observed implementation
→ Recover implicit architecture
→ Extract hidden assumptions
→ Find violated/missing invariants
→ Design falsifying probes
→ Correct System Design
→ Re-enter MONITOR or PRECHECK
```

Read [`modes/postmortem.md`](modes/postmortem.md).

## Mandatory architecture checkpoints

MONITOR is low-interruption, not no-review. Run a meta-review at natural design boundaries:

```text
ARCHITECTURE_CHOICE
FIRST_VERTICAL_SLICE
PERSISTENCE_INTRODUCED
ASYNC_OR_CONCURRENCY_INTRODUCED
EXTERNAL_INTEGRATION_INTRODUCED
FIRST_GREEN
BEFORE_PR_OR_PUBLICATION
CI_OR_RUNTIME_FAILURE_WITH_DESIGN_IMPACT
```

`FIRST_GREEN` is mandatory. A first passing test suite often closes only the coded path, not the architectural proof obligation. Before calling the work done, ask:

```text
What did these tests not prove?
Which assumptions remain implicit?
Which runtime/substrate was not exercised?
Which failure states remain untested?
Which side effects lack reconciliation?
Which evidence is stale, indirect, mock-only, or from another subject?
```

Green evidence may remain green; the meta-review determines only what it actually proves.

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
```

Every component exists inside these spaces. Every interaction crosses a boundary. Every boundary introduces assumptions. Every assumption requires proof, measurement, runtime verification, explicit acceptance, or a declared unknown.

The objective is to reduce the reachable invalid state space without removing productive solution search.

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
```

For mutable external claims, compose `truth-verify-loop` or another admitted primary-source verification path.

## Phase 0 — Complexity classification

Classify before design work:

### Level A — Local deterministic change

Examples: pure utility, isolated parser, local transformation, simple CRUD with no material distributed invariant. A shortened protocol is allowed, but source claims and evidence state remain explicit.

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

## Phase 4 — Unknown-unknown discovery

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
Unknown → Probe → Observation → Updated model
```

Do not compensate for missing knowledge by writing more implementation code when the unknown blocks a material boundary. Non-blocking discovery may continue in parallel under MONITOR.

## Phase 5 — Failure and collision matrix

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

For every material failure define detection, containment, recovery, retry rule, compensation, terminal state, and observable evidence.

## Phase 6 — Reconciliation loops

Prefer systems that converge:

```text
Observe
→ Compare desired vs observed state
→ Diff
→ Reconcile
→ Verify
```

Every loop defines desired state, observed state, authority, retry budget, backoff, idempotency, progress measure, no-progress detection, terminal success, and terminal failure. Unbounded loops are forbidden. `Retry until success` is not a recovery strategy.

## Phase 7 — Verification architecture

Every hard invariant creates a proof obligation:

```text
Invariant
→ Enforcement Mechanism
→ Observer
→ Oracle
→ Failure Injection
→ Expected Observation
→ Evidence
```

A verifier must be able to detect a planted defect. HTTP 200 does not prove business correctness. A mock does not prove an external runtime. Code review does not prove performance. A benchmark on another machine does not prove this deployment.

## Phase 8 — Evidence ladder

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

Absence is never PASS. Evidence never promotes itself across subject, revision, environment, or ladder level.

## Phase 9 — Implementation gate

The implementation gate governs material transitions; MONITOR does not require blocking harmless exploration until the relevant boundary is reached.

Return exactly one gate when a material transition requires admission:

### BLOCKED

Use when a required architectural fact is unknown, target environment is unbound, a critical invariant lacks enforcement or oracle, lifecycle ownership is incomplete, required physical capability is unavailable, or unresolved security assumptions remain.

Allowed work: probe, experiment, contract, state machine, test harness, interface, spike, documentation, and other reversible exploration that cannot cross the blocked boundary.

### READY_FOR_PROTOTYPE

Use when architecture can be explored but important runtime claims remain unverified. Explicitly list claims the prototype cannot establish.

### READY_FOR_IMPLEMENTATION

Use when the relevant material transition has mapped realms, explicit state ownership, closed blocking unknowns, hard-invariant enforcement, lifecycle symmetry, failure recovery, required capabilities, and verification paths.

There is no Agent-owned `PRODUCTION_ACCEPTANCE`. Security, compliance, financial, destructive, irreversible, production-promotion, permission-widening, and rollback acceptance remain Human/organizational authority boundaries.

The existing machine contract remains `spatial-loop-system-contract/v1` and is checked with:

```bash
python3 skills/spatial-loop-systems-engineering/scripts/check_system_contract.py \
  check path/to/system-contract.json
```

Exit `0` validates structural closure/gate consistency; `2` rejects hollow or contradictory contracts; `64` means input/subject is absent or invalid. The checker does not prove referenced evidence is truthful.

## Technology selection comes after constraints

Do not let a technology choice silently define the constraints. For each candidate technology ask:

```text
Which invariants does it enforce for us?
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

**Domain modules extend the core method. They never replace it, bypass complexity classification, redefine evidence states, or weaken the implementation gate or architecture watch loop.**

The existing Linux isolation guidance remains decoupled at [`modules/linux-isolation-runtime.md`](modules/linux-isolation-runtime.md).

## Required output contract

PRECHECK uses the complete A–L packet before the gated high-risk transition. MONITOR may materialize the same packet incrementally, but by `BEFORE_PR_OR_PUBLICATION` all applicable sections must exist for Level B/C/D work:

A. **Intent Digest** — what the user is actually trying to achieve.
B. **Source Claim Classification** — requirements, proposals, assumptions, observations/facts, external claims, unknowns.
C. **Complexity Class** — A/B/C/D and why.
D. **Spatial Topology** — realms, trust boundaries, authority, ownership, flows.
E. **State Machines** — states, transitions, terminal and illegal states.
F. **Golden Invariants** — `INV-###`, statement, owner, enforcement, failure mode, oracle, evidence level.
G. **Resource Envelope** — finite limits/backpressure/exceed behavior.
H. **Failure / Collision Matrix** — prioritize highest-risk combinations.
I. **Unknown Register** — classification and falsifiable probes.
J. **Verification Plan** — invariants mapped to falsifiable tests.
K. **Implementation Gate** — the current material-boundary gate.
L. **Implementation Plan / Implemented Delta** — planned work under PRECHECK or actual/reconciled delta under MONITOR/POSTMORTEM.

Use [`references/spec-packet-template.md`](references/spec-packet-template.md) and the machine contract for persisted artifacts.

## Anti-drift protocol during implementation

Before modifying a high-risk subsystem reload its state machine, invariants, ownership rules, resource limits, failure semantics, and verification oracle. Under MONITOR, lower-risk work may proceed while the Shadow Architect records deltas, but every material delta must close by its checkpoint.

After every meaningful architecture-changing step ask:

```text
Which invariant changed?
Which assumption changed?
Which new state became possible?
Which new resource became owned?
Which new failure path appeared?
Which verifier now proves this?
```

If implementation introduces an unmodeled state, resource, authority, external side effect, or evidence claim, classify the intervention level. Do not automatically stop at L0/L1; do not continue through an unresolved L3 boundary.

Implement through bounded reconciliation:

```text
MAP
→ CONSTRAIN
→ FALSIFY
→ IMPLEMENT
→ OBSERVE
→ RECONCILE
→ VERIFY
```

After three consecutive qualifying failures against the same invariant/acceptance target, do not make a fourth blind patch. Enter [`references/three-failure-escalation.md`](references/three-failure-escalation.md): preserve the failure packet, open the correct forge issue, use fresh diagnosis, create a new isolated worktree, implement the smallest falsifiable repair, and require the owning oracle plus negative control before delivery.

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
```

Expand each into exact semantics, scope, failure conditions, and evidence. For example, `database is ACID` must become questions about isolation level, transaction boundary, external side effects, and commit/acknowledgement ambiguity.

## Composition boundary

This Skill owns constraint discovery, the Shadow Architecture watch loop, executable specification, material-transition gating, and bounded reconciliation. Compose explicitly when needed:

- `truth-verify-loop` for mutable external claims;
- `unknown-discovery-composer` for broad unknown discovery;
- `loop-harness-standard` for executable bounded iteration Harnesses;
- `forgejo-delivery-loop` or `github-delivery-loop` for forge-native delivery;
- `git-town-stacked-pr-worker` for admitted stacked-worktree synchronization.

No downstream Skill may promote `NOT_EXERCISED` to `PASS`, bypass the universal compiler, or let a domain module disable architecture monitoring.

## Final operating principle

The objective is not to generate the most code or follow a source architecture faithfully. The objective is to **reduce the reachable invalid state space while preserving useful exploration**.

A strong architecture makes dangerous states difficult or impossible to represent. A strong lifecycle causes failures to converge toward known terminal states. A strong verification Harness makes violations observable. A strong Shadow Architect catches silent System Design drift without becoming a second Builder.

Code is one actuator inside the loop, not the system itself.