# AGENTS.md — Spatial Loop #407 integration closeout

This directory is a status/handoff projection for issues #407–#411. It does not replace `../SKILL.md`, the ICPG schema/checker, GitHub metadata, exact Git subjects, workflow receipts, or live runtime receipts.

## Mandatory read order

1. [`README.md`](README.md) in this directory.
2. [`../AGENTS.md`](../AGENTS.md).
3. [`../README.md`](../README.md) and [`../SKILL.md`](../SKILL.md).
4. [`../references/intent-case-proof-graph.md`](../references/intent-case-proof-graph.md).
5. [`../references/architecture-watch-loop.md`](../references/architecture-watch-loop.md).
6. `../scripts/check_case_graph.py` and the owning tests/evals.
7. `../../agentic-tech-lead-orchestration/README.md` plus the current Spatial Local Handoff queue when admission/runtime work remains.
8. `../../git-town-stacked-pr-worker/molecular-indexes/spatial-407/README.md` for terminal atom lineage.
9. Current GitHub issues #407–#411, PR #412, current main, exact-head workflows and any later superseding subjects.

## Authority and writer law

- Shadow Architect is an independent reviewer/monitor, not a second implementation writer.
- Tech Lead owns task decomposition, exact case denominator, one case owner or convergence owner, writer/path/resource leases and handoff.
- GitHub/Git exact subjects, executable contracts and receipts beat this prose on mutable state.
- Do not close #408/#409/#410 from candidate evidence alone; main landing and exact-main readback are required.
- Do not close #411 from static tests, Builder self-report, same-context prose, or compatibility-only green.
- Do not close #407 while #411 remains a declared blocking program lane.
- Do not convert case dependencies into Git parentage unless unmerged parent bytes/contracts are actually consumed.
- Do not weaken golden-proof, commit-role, evidence, or provenance gates to make PR #412 green.

## Closeout State Machine

```text
SOURCE_CANDIDATE
→ CURRENT_MAIN_RECONCILED
→ STATIC_SUITES_GREEN
→ PROVENANCE_GREEN
→ READY_FOR_MAIN_ADMIT
→ MERGED_ON_MAIN
→ STATIC_CHILD_ISSUES_CLOSEABLE
→ LIVE_HANDOFF
→ #411 LIVE_CANARY
```

Any red load-bearing gate returns the subject to `HOLD`, records the exact failure, and updates the Local Handoff queue if the required runtime is unavailable.

## Current stop condition

The current connector may continue writing public source candidate bytes and GitHub issue/PR state, but it must stop before claiming repository admission if the repository-required provenance gate cannot be satisfied by the connector-authored history. In that state, preserve the exact candidate tree and hand off a provenance-compliant rebuild rather than adding rewritable connector commits to historical exception lists or weakening the gate.

Resolution (2026-08-22): this stop condition was honored and is now discharged for #407/#412 — the candidate tree is preserved on the closed PR #412 (head `e679aed9`), admission happened through a superseding replayed carrier (terminal merge `c27f8c3`) whose exact-head provenance gate is green, and no exception list or gate was touched. Receipt: `data/handoff/spatial-407/publication-provenance-receipt.json`. The law above remains in force for any future connector candidate in the same state.

## Evidence vocabulary

Use literal evidence states where applicable:

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
EVIDENCE_DEPENDENT
HUMAN_ADMIT_REQUIRED
```

`IMPLEMENTED_CANDIDATE` and `PENDING_MAIN_ADMISSION` are integration classifications only; they are not substitutes for runtime evidence states.