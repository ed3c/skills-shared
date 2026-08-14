---
name: spatial-loop-systems-engineering
description: |
  Design or modify systems whose correctness depends on OS/kernel behavior,
  hardware, privilege, concurrency, resource ceilings, failure domains, or
  teardown. Use before implementing sandboxes, runtimes, schedulers, storage
  engines, network data planes, compilers, embedded/GPU systems, lock-free
  components, low-latency paths, or other substrate-bound software.
  Produces an exact-subject system contract: trust realms, boundaries, flows,
  state machine, hard invariants, capability probes, collision matrix,
  reconciliation loops, performance budgets, verification oracles, and a
  fail-closed implementation gate. After three qualifying failures on the same
  target, stops blind repair and escalates through an issue packet, fresh
  diagnosis, and a new isolated worktree. Do not use for ordinary CRUD work, as
  a security certification, or as a substitute for privileged/hardware evidence.
license: MIT
compatibility: Any Agent Skills-compatible coding agent with repository read/write access. Privileged or hardware execution is optional, but its absence blocks the corresponding claim.
metadata:
  version: "1.1.0"
  procedure: "spatial-loop-system-contract"
---

# spatial-loop-systems-engineering

Treat a system as a reachable state space constrained by authority, resources,
time, and evidence. The spatial metaphor is useful only when every term maps to
an artifact that can be inspected or tested.

```text
realm                 → trust/authority/resource domain
boundary surface      → enforcement mechanism and blast radius
flow vector           → data, event, resource, or ownership transfer
invariant manifold    → allowed states plus a falsifiable oracle
escape vector         → failure or attack path crossing a boundary
attractor             → declared healthy terminal state
reconciliation loop   → Observe → Diff → Reconcile → Verify
```

Do not call prose a proof. Do not call a diagram an isolation mechanism. Do not
call an unexecuted test a pass.

## Trigger boundary

Use this Skill when one or more of these conditions are true:

- behavior depends on kernel, hypervisor, firmware, device, filesystem, network,
  memory-model, ABI, FFI, signal, or scheduler semantics;
- correctness depends on global lifecycle, concurrency, ordering, ownership, or
  cleanup invariants;
- tests require root, KVM, special hardware, kernel modules, network topology,
  fault injection, load generation, or destructive execution;
- the request includes claims such as safe, isolated, lock-free, zero-copy,
  zero-leak, microsecond, high-throughput, deterministic, or production-grade.

Do not use it as extra ceremony for a normal application feature. Do not use it
to certify security, production readiness, or legal compliance.

## Owned state machine

```text
CLASSIFY
→ BIND_SUBJECT
→ MAP_REALMS
→ DECLARE_INVARIANTS
→ BIND_CAPABILITIES
→ MAP_COLLISIONS
→ DESIGN_ORACLES
→ IMPLEMENTATION_GATE
    ├── BLOCKED                 → HANDOFF
    ├── READY_FOR_PROTOTYPE     → SAFE_SCAFFOLD → VERIFY → HANDOFF
    └── READY_FOR_IMPLEMENTATION
                                → IMPLEMENT
                                → OBSERVE
                                → DIFF
                                → RECONCILE
                                → VERIFY
                                    ├── converged → HANDOFF
                                    ├── qualifying FAIL #1/#2 → bounded retry
                                    └── qualifying FAIL #3 → ESCALATION_REQUIRED
                                            → ISSUE_PACKET_BOUND
                                            → FRESH_DIAGNOSIS
                                            → ISOLATED_WORKTREE
                                            → REPAIR
                                            → VERIFY
                                            → forge-native PR / Human merge boundary
```

Probe code, verifier code, and disposable experiments may be written before the
gate. Core implementation may not.

## Required artifacts

Before core implementation, produce and bind:

1. **Exact subject** — repository/path or artifact, revision, and digest.
2. **Objective and non-goals** — including risk class and forbidden claims.
3. **Realm map** — trust, authority, entry/exit conditions, and blast radius.
4. **Boundary and flow map** — enforcement owner, transport, ordering,
   backpressure, ownership transfer, and failure semantics.
5. **Finite-state lifecycle** — valid and illegal transitions, terminal states,
   cancellation, crash, restart, and recovery.
6. **Hard invariant ledger** — every invariant has scope, owner, enforcement,
   oracle, and named failure state.
7. **Substrate capability matrix** — every required capability has a probe,
   evidence state, and exact receipt subject.
8. **Resource envelope** — numeric or finite ceilings, enforcement, observation,
   exceed action, and lifecycle owner.
9. **Failure/collision matrix** — fault, race window, detection, containment,
   reconciliation, and oracle.
10. **Teardown symmetry ledger** — every lifecycle-owned allocation has normal
    release, crash release, and leak oracle.
11. **Reconciliation loops** — observed state, desired state, diff, actuator,
    convergence condition, stop condition, and failure-attempt counter.
12. **Verification plan** — positive, hollow/negative, mutation, privileged,
    hardware, chaos, fuzz, security, and performance lanes as applicable.
13. **Implementation gate** — one of `BLOCKED`, `READY_FOR_PROTOTYPE`, or
    `READY_FOR_IMPLEMENTATION`. There is no Agent-declared
    `READY_FOR_PRODUCTION`.

Use [`references/spec-packet-template.md`](references/spec-packet-template.md)
for the human-readable packet and
`spatial-loop-system-contract/v1` for the machine-checkable contract.
Use [`references/three-failure-escalation.md`](references/three-failure-escalation.md)
when the same invariant or acceptance target fails three qualifying repair
attempts.

## Procedure

### 1. Classify the substrate

Name the system class and the physical surfaces that can falsify it. Separate:

```text
language/runtime semantics
OS/kernel semantics
hypervisor/firmware/device semantics
network/storage topology
concurrency and memory model
security authority
performance environment
```

Load a domain module only when its trigger matches. Linux isolation work loads
[`modules/linux-isolation-runtime.md`](modules/linux-isolation-runtime.md).

### 2. Bind claims, assumptions, and unknowns

Keep these distinct:

- **claim** — what the system promises;
- **assumption** — a dependency with a named owner and falsifier;
- **unknown** — a gap with a discovery method and impact;
- **evidence** — an observation bound to the exact subject and environment.

Unknown unknowns cannot be written into a specification in advance. Reduce
their surface through primary-source review, source inspection, capability
probes, minimal experiments, incident/postmortem review, differential tests,
fuzzing, and chaos. Discovery work changes `ABSENT` or `NOT_EXERCISED`; it does
not manufacture `PASS`.

### 3. Map space before behavior

For each realm, answer:

```text
Who has authority here?
What resources exist here?
How does anything enter or leave?
Which mechanism enforces the boundary?
What is the maximum blast radius when enforcement fails?
```

For each flow, answer:

```text
Who owns the payload before and after transfer?
What ordering and backpressure exist?
What happens on partial delivery, duplication, cancellation, or peer death?
```

### 4. Declare invariants before core code

An invariant without an oracle is a wish. Use this form:

```text
ID:
Statement:
Scope:
Owner:
Enforcement:
Oracle:
Named failure state:
```

Concurrency invariants additionally require an ownership model, synchronization
or message-passing rule, cancellation semantics, and a race/deadlock oracle.
A lock list is not a lock-order proof.

### 5. Close the capability matrix

Never assume root, `/dev/kvm`, cgroup delegation, a kernel feature, a device,
network reachability, clock properties, filesystem behavior, or load generator.
Probe each required capability.

```text
required + PASS            may support READY_FOR_IMPLEMENTATION
required + NOT_EXERCISED   may support only READY_FOR_PROTOTYPE
required + ABSENT/FAIL     blocks dependent implementation claims
```

A capability reported by package presence, documentation, or another machine is
not current-runtime evidence.

### 6. Design failure and teardown first

Enumerate signal races, cancellation, partial initialization, partial writes,
descriptor exhaustion, memory pressure, process/thread death, stale identity,
timeout, retry amplification, corrupt input, clock discontinuity, and peer
partition where relevant.

Every acquisition must have:

```text
normal release
initialization-failure release
cancellation release
crash/restart reconciliation
idempotent repeat behavior
leak oracle
```

RAII or `Drop` is an implementation technique, not proof that asynchronous
termination or kernel-owned resources were reclaimed.

### 7. Bind performance to a measurement contract

Words such as fast, low-latency, high-throughput, zero-copy, zero-overhead,
microsecond, millisecond, and instant require:

```text
metric and unit
target percentile
load model and concurrency
cold/warm definition
hardware/firmware/OS/kernel/runtime identity
configuration digest
measurement method and repetitions
error bars or variance
```

Vendor numbers and local anecdotes are hypotheses until reproduced on the exact
subject. Prefer the simplest data path that meets the measured budget; do not
default to zero-copy or lock-free designs when their ownership and pinning costs
are unproven.

### 8. Build oracles before core implementation

Each required verification lane must name preconditions, stimulus, oracle,
negative control, status, and evidence. A verifier that cannot detect a planted
defect is not an authority.

Mocks may validate pure logic. They cannot prove kernel isolation, hardware
behavior, exploit resistance, cleanup after `SIGKILL`, or tail latency.

### 9. Apply the implementation gate

Validate the contract:

```bash
python3 skills/spatial-loop-systems-engineering/scripts/check_system_contract.py \
  check path/to/system-contract.json
```

- `exit 0`: contract shape and gate consistency are valid.
- `exit 2`: a declared contract is hollow or internally inconsistent.
- `exit 64`: subject/file/JSON is absent or unreadable.

The checker validates closure and contradictions. It does not prove that an
evidence URI is truthful or that the designed system is safe.

### 10. Implement through bounded reconciliation

After the gate:

```text
Observe exact state
→ Diff against invariant and desired state
→ Reconcile one bounded change
→ Re-run the owning oracle
→ preserve the failure trajectory
→ converge, escalate, or stop
```

A **qualifying failed attempt** is a repair against the same invariant or
acceptance target where the implementation/configuration subject changed and the
owning oracle actually executed and returned subject-bound `FAIL`. `ABSENT`,
`NOT_EXERCISED`, and `SKIPPED_BY_POLICY` do not count as failed repairs.

After three consecutive qualifying failures, do not make a fourth speculative
patch in the same context. Enter the recovery contract in
[`references/three-failure-escalation.md`](references/three-failure-escalation.md):

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

For a normal consumer with an admitted local Forgejo binding, issue and PR
tracking route through `forgejo-delivery-loop`. For GitHub Actions or
GitHub-hosted CI incidents, use GitHub as the incident/publication authority and
compose `github-delivery-loop`; exact GitHub workflow/run/job/head evidence must
not be replaced by a Forgejo mirror.

The intended operator path may open a new ChatGPT Desktop question/session for
fresh diagnosis. A runtime that cannot launch ChatGPT Desktop must stop at a
fresh-diagnosis handoff with the exact issue packet; it must not claim that a
fresh session ran.

Do not repair a failing system by weakening the invariant, deleting the
negative control, expanding privilege, hiding an error, resetting the attempt
counter by renaming the same failure, or replacing physical execution with model
judgment.

## Hard laws

1. **Exact-subject law** — every result binds revision, digest, environment, and
   configuration. Old green evidence does not transfer to new bytes.
2. **Authority law** — documentation and Agent confidence never outrank an
   executed deterministic oracle for its declared subject.
3. **Absence law** — use only `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`,
   `NOT_EXERCISED`, and `SKIPPED_BY_POLICY`.
4. **Boundary law** — every boundary names its mechanism and enforcement owner.
5. **Invariant law** — every hard invariant has a falsifier and named failure.
6. **Symmetry law** — every owned resource has mirrored release and crash paths.
7. **Bounded-loop law** — retries, reconciliation, and recovery have budgets and
   terminal states.
8. **No-mock-only law** — physical claims require physical execution.
9. **No-silent-fallback law** — missing privilege or substrate becomes an
   evidence state, never a weaker hidden implementation.
10. **Human authority law** — threat-model acceptance, security sign-off,
    production promotion, permission widening, destructive testing, and
    rollback remain Human/trusted-operator decisions.
11. **Three-failure escalation law** — three qualifying failures against the
    same invariant/acceptance target force issue-bound fresh diagnosis and a new
    isolated worktree before another repair attempt. Commit/PR eligibility
    requires the owning oracle and required negative control to pass.

## Composition boundary

This Skill owns the pre-implementation system contract and its reconciliation
logic. Compose explicitly when needed:

- `unknown-discovery-composer` — widen discovery for poorly understood surfaces;
- `truth-verify-loop` — verify mutable external claims and primary sources;
- `loop-harness-standard` — build an executable bounded iteration Harness;
- `forgejo-delivery-loop` — normal local Forgejo incident/PR routing after an
  escalation when the consumer has an admitted Forgejo binding;
- `github-delivery-loop` — GitHub Actions/GitHub-hosted CI incident and
  publication authority;
- `git-town-stacked-pr-worker` — new isolated worktree/branch and bounded branch
  graph synchronization when admitted by the consumer.

No composition is implicit, and no downstream Skill may promote
`NOT_EXERCISED` to `PASS`.

## Evidence boundary

```text
portable procedure and copyable prompt        IMPLEMENTED
machine-checkable contract closure            IMPLEMENTED
positive/hollow/mutation controls             IMPLEMENTED
three-failure escalation contract             IMPLEMENTED
Linux isolation domain guidance               IMPLEMENTED
live root/KVM/cgroup/seccomp execution         NOT_EXERCISED
hardware-specific performance                 NOT_EXERCISED
chaos, exploit, and sandbox-escape testing    NOT_EXERCISED
fresh ChatGPT Desktop session execution        HOST_OPERATOR_BOUND
security acceptance and production promotion  HUMAN_ADMIT_REQUIRED
```
