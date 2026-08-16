---
name: loop-harness-standard
description: |
  Portable loop-harness procedure for turning an objective into bounded attempts with explicit state, checkpoints, evaluator ownership, negative controls, convergence criteria, rollback, and exact-subject receipts. Concrete drivers, providers, consumer loop layouts, seed profiles, and repository runtimes are domain modules.
---

# Loop Harness Standard

<!-- PORTABLE_CORE_START -->

## Contract

The core owns objective binding, loop state, attempt identity, evaluator separation, checkpoint/recovery, convergence, and terminal evidence. Concrete drivers and consumer runtimes live in `modules/domain-profile.md`.

## State machine

```text
OBJECTIVE_BOUND
→ LOOP_STATE_INITIALIZED
→ ATTEMPT_ADMITTED
→ ATTEMPT_EXECUTED
→ EVIDENCE_CAPTURED
→ EVALUATED
→ {CONVERGED | RETRY_ADMITTED | BLOCKED}
→ CHECKPOINTED
→ TERMINAL_RECEIPT
```

## Hard laws

- **CORE-LAW-001 — objective and attempt identity are explicit.** Every attempt binds objective, subject, budget, input state, and parent lineage where applicable.
- **CORE-LAW-002 — evaluator ownership is independent.** The worker/driver cannot silently redefine acceptance criteria or remove failed attempts.
- **CORE-LAW-003 — observable evidence outranks loop self-report.** Attempt prose, process exit zero, or driver success is not convergence proof without the owning assertions.
- **CORE-LAW-004 — modules cannot widen authority.** Domain modules may select drivers/runtime layouts but cannot override laws, change evaluators to get green, or widen runtime/secret/merge authority.
- **CORE-LAW-005 — convergence is bounded and replayable.** Retry, checkpoint, rollback, and terminal states remain explicit, and every terminal claim binds the exact subject and evidence set.

## Procedure

1. Bind objective, exact subject, invariants, evaluator, negative controls, budget, and rollback subject.
2. Initialize durable loop state and unique logical attempt identity.
3. Admit an attempt only when dependencies, leases/capabilities, and budget allow it.
4. Execute one bounded attempt through a selected domain/runtime adapter when needed.
5. Capture artifacts, commands, exits, diffs, traces, and relevant state transitions.
6. Evaluate independently against frozen acceptance and falsifying controls.
7. Converge, retry with explicit lineage, or block; never discard a failed attempt from the denominator.
8. Checkpoint enough state for deterministic resume and emit a terminal receipt when the loop stops.

## Module selection

Load `modules/domain-profile.md` only when a concrete driver, provider, repository harness layout, consumer loop topology, or seed profile must be bound.

## Executable assertion

```bash
python3 scripts/check_skill_core_boundaries.py --skill loop-harness-standard
```

## Evidence states

Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED`.

## Stop and handoff

Stop on verified convergence, budget exhaustion, unavailable required capability, evaluator failure requiring a new objective, unsafe/irreversible next action, or Human-owned admission. Handoff includes loop state, attempt lineage, evidence, controls, rollback subject, and next admissible action.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md).
