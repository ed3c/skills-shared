# Domain modules

`SKILL.md` owns the universal Constraint-First compiler. This directory owns only **triggered domain expansion**.

A domain module may add domain-specific unknowns, hard-law candidates, failure vectors, capability probes, and verification lanes. It may not replace or weaken:

- A/B/C/D complexity classification;
- source-claim classification;
- realm/authority/state/resource ownership analysis;
- Golden Invariant proof obligations;
- evidence ladder and exact evidence states;
- `BLOCKED | READY_FOR_PROTOTYPE | READY_FOR_IMPLEMENTATION` gating;
- three-failure escalation;
- Human acceptance boundaries.

The invariant is:

```text
Universal Constraint-First Method
        +
Triggered Domain Expansion
        =
Executable Spec
```

Never:

```text
Domain Module
→ bypass universal compiler
→ implementation
```

## Trigger routing

| Domain trigger | Expansion focus | Current module |
|---|---|---|
| Web/API | authz, rate limiting, validation, transaction boundaries, cache consistency, external side effects | core trigger profile; no dedicated module yet |
| Database/storage | durability, WAL, isolation, replication, migration, crash recovery | core trigger profile; no dedicated module yet |
| Distributed systems | partition, consensus/coordination, leases, retries, duplication, ordering | core trigger profile; no dedicated module yet |
| Agentic AI | tool authority, semantic failure, loop termination, trajectory state, context bounds, side-effect replay, model nondeterminism, Skill discovery/fork/grounding | [`agent-host-procedural-grounding.md`](agent-host-procedural-grounding.md) when external Skill search, host context isolation, or procedure-uptake evidence is material; otherwise core trigger profile |
| Mobile | process death, lifecycle, offline consistency, permissions, OS/background limits | core trigger profile; no dedicated module yet |
| Browser/device automation | session ownership, DOM/UI drift, navigation races, device state, anti-bot/platform constraints | core trigger profile; no dedicated module yet |
| Data pipeline | lineage, replay, deduplication, late events, schema evolution, backfills | core trigger profile; no dedicated module yet |
| ML | dataset/model identity, leakage, reproducibility, train/serve skew, evaluation contamination | core trigger profile; no dedicated module yet |
| Security | trust/capability boundaries, secrets, confused deputy, escalation, replay, TOCTOU | core trigger profile; no dedicated module yet |
| Systems/kernel/virtualization | syscall/process/memory/scheduler/filesystem/hardware/privilege semantics | [`linux-isolation-runtime.md`](linux-isolation-runtime.md) when Linux isolation/runtime triggers match |
| High performance | cache/layout/contention/allocation/syscalls/NUMA/tail latency/measurement identity | core trigger profile; no dedicated module yet |
| Financial/payment | immutable ledger, authorization, idempotency, reconciliation, duplicate/partial execution | core trigger profile; no dedicated module yet |

`core trigger profile` means the universal invariant families in `SKILL.md` are specialized for that domain without loading a separate implementation recipe. Add a dedicated module only when reusable domain-specific hard laws, probes, and oracles justify a stable decoupled contract.

## Module contract

Every dedicated module should declare:

```text
Trigger
Domain-specific realms
Likely hidden assumptions
Hard-law candidates
Required capabilities/probes
Failure/collision extensions
Verification/oracle extensions
Claims the module cannot establish
Evidence boundary
```

A module is design guidance, not runtime evidence. Consumer-specific repository paths, versions, credentials, hardware, kernel, privilege, environment, and live receipts remain outside `skills-shared`.
