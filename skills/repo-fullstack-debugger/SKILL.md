---
name: repo-fullstack-debugger
description: |
  Portable trace-driven diagnosis procedure for repeated dynamic failures: refuse unnecessary deep debugging when direct evidence is sufficient, bind the failing subject and trace, classify the failure, test the cheapest falsifiable hypothesis, preserve rollback, and promote only verified fixes into reusable playbooks. Concrete browser, provider, automation, repository-runtime, and output profiles are domain modules.
---

# Trace-Driven Full-Stack Diagnosis

<!-- PORTABLE_CORE_START -->

## Contract

Use after a cheaper deterministic/direct-source path has failed or the defect exists only at runtime. The core owns admission, trace binding, hypothesis discipline, bounded experiments, rollback, verification, and playbook handoff. Concrete runtime/tool profiles live in `modules/domain-profile.md`.

## State machine

```text
ADMISSION_CHECKED
→ FAILURE_SUBJECT_BOUND
→ TRACE_BOUND
→ FAILURE_CLASSIFIED
→ HYPOTHESES_RANKED
→ MINIMAL_EXPERIMENT_RUN
→ {REJECT | REVISE | VERIFY_FIX}
→ PLAYBOOK_CANDIDATE
→ HANDOFF
```

## Hard laws

- **CORE-LAW-001 — diagnose observed failure.** Bind the exact failing subject, trace, environment, and terminal symptom before proposing fixes.
- **CORE-LAW-002 — cheapest sufficient evidence first.** Do not enter an expensive loop when direct source, compiler/test output, or one deterministic probe can answer the question.
- **CORE-LAW-003 — hypothesis requires falsification.** Tool/model prose is not verification; each material hypothesis must map to an observable probe or assertion.
- **CORE-LAW-004 — modules cannot widen authority.** Domain modules may interpret specialized traces or execute admitted probes but cannot weaken laws, modify owning tests to hide failure, or widen runtime/secret/merge authority.
- **CORE-LAW-005 — fixes become playbooks only after replay.** A fix is reusable only after the original failure is closed on the exact subject and regression/rollback evidence is preserved.

## Procedure

1. Decide whether deep diagnosis is admitted; return to a cheaper owner when evidence is already sufficient.
2. Bind exact repository/runtime subject, failing command/action, environment identity, and trace artifacts.
3. Separate observation from inference and classify the failure family without pretending coverage outside observed lanes.
4. Rank hypotheses by information gain, cost, reversibility, and evidence strength.
5. Run one minimal bounded experiment; preserve before/after state and rollback.
6. Reject or refine hypotheses based on observed evidence rather than narrative plausibility.
7. Verify the fix with the owning assertion and a regression/falsifying control.
8. Promote only stable, scoped knowledge to a playbook owner; keep unresolved runtime facts explicit.

## Module selection

Load `modules/domain-profile.md` only when specialized runtime traces, automation stacks, provider adapters, repository commands, or artifact formats are necessary.

## Executable assertion

```bash
python3 scripts/check_skill_core_boundaries.py --skill repo-fullstack-debugger
```

## Evidence states

Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED`.

## Stop and handoff

Stop when the defect is verified closed, the next probe lacks authority/capability, the budget is exhausted, rollback cannot be guaranteed, or evidence shows another owner is responsible. Handoff includes exact failure subject, observations, rejected hypotheses, remaining hypotheses, and verified playbook candidate when any.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md).
