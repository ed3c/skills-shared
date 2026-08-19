# AGENTS.md — traceability and closure routing

Read this file before adding or changing repository-wide traceability, Tech Lead/Shadow closure, source-problem mappings, issue/PR graphs, Molecular Stack indexes, or external consumer snapshots.

## Read order

1. repository root `AGENTS.md`, `CONTEXT.md`, `ARCHITECTURE.md`;
2. `docs/INDEX.md` and `docs/architecture/STATE_MACHINES.md`;
3. `TRACEABILITY_INDEX.md`;
4. `TECH_LEAD_SHADOW_CLOSURE.md`;
5. `CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md` for the admitted #379 static/deterministic subject and exact merge provenance;
6. `CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md` for the pre-admission State Machine, denominator, rejected epochs and evidence ceilings;
7. `WAVE3_PARENT_ADMISSION.md` before current #464–#468 decisions, because it records fork-time #455 provenance, later Human Admit, and the current-main refresh boundary;
8. `WAVE3_LIVE_EVIDENCE.md` for the Wave‑3 State Machine, carriers, reversible canary, source compiler, immutable integration checkpoint and Local Handoff Queue;
9. `skills/agentic-tech-lead-orchestration/AGENTS.md`, README and SKILL;
10. selected control-plane execution packet/module/contracts when the trigger matches;
11. `skills/procedural-shadow-runtime/README.md`;
12. `skills/git-town-stacked-pr-worker/README.md`;
13. exact issue/PR/workflow/runtime/evidence subjects.

## Authority

Traceability documents are human projections. They may route to machine truth but must never replace schemas, current GitHub metadata, Git ancestry, runtime receipts, source readback, CI execution, or Human Admit.

`CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md` freezes the static/deterministic #379 admission subject. Current mutable repository/issue/runtime state must still be read from GitHub and owning runtime receipts.

A convergence branch may consume exact sibling candidate bytes for integration testing. Such ancestry proves byte consumption only; it does **not** promote an unadmitted sibling to `ADMITTED`, `MERGED`, or repository truth.

## Closure law

```text
SOURCE_PROPOSAL
→ METHOD_IMPLEMENTED
→ CONSUMER_MECHANISM_IMPLEMENTED
→ DETERMINISTIC_EVIDENCE_VERIFIED
→ LIVE_OR_PHYSICAL_EVIDENCE_VERIFIED
→ HUMAN_ADMITTED
→ RELEASED
```

Never equate issue closure, PR merge, workflow green, model agreement, article/PDF prose, Google/CodexDoc navigation, terminal `done`, historical receipts, or a documentation update with a later closure state.

## Writer law

Exactly one convergence writer owns each shared traceability/index subject. Parallel implementation lanes remain siblings unless a child consumes named unmerged parent bytes at its fork epoch. A convergence commit may have several sibling or refresh parents to make consumed bytes inspectable; those parents retain their semantic relation. Shadow reviewers do not mutate the Tech Lead's implementation branch.

## Codex control-plane program

Fork-time implementation graph:

```text
#375 / PR #451  Codex SDK controller/session adapter       SIBLING / CLOSED-UNMERGED / CONSUMED
#376 / PR #452  GitHub Issue DAG projection               SIBLING / CLOSED-UNMERGED / CONSUMED
#377 / PR #456  Herdr observer v3                         SIBLING / CLOSED-UNMERGED / CONSUMED
#378 / PR #457  problem-closure ledger v3                 SIBLING / CLOSED-UNMERGED / CONSUMED
PR #380         design/traceability foundation            DOCUMENTATION SIBLING / CLOSED-UNMERGED / CONSUMED
      ↓ exact candidate bytes
#379 / PR #455  control-plane convergence                 HUMAN_ADMITTED / MERGED
```

Admitted Wave‑2 implementation subject:

```text
#455 candidate  847e56c3418fce920c42d983e84ee44fdc6e8971
#455 merge      ca31e0b1e640f0dba2c3d94da9d9786fbed32f2c
shared tree     8a75271851f2e9dd47dd3a019c93e4a0f9272d24
```

The post-merge admission route was then landed through PR #475; its merge subject is recorded in `CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md`/GitHub metadata. Do not use a hard-coded historical `main` SHA as mutable current authority.

Historical closed-unmerged candidates remain part of the denominator. Human admission of #455 changes repository authority but does not convert any live Codex/GitHub/Herdr/source evidence lane into PASS.

Current deterministic denominator:

```text
Codex SDK       4 positive / 14 mutations
GitHub DAG      6 positive / 17 mutations
Herdr           4 positive / 18 mutations
problem closure 6 positive / 22 mutations
```

Current mechanism/evidence split:

```text
Wave‑2 control-plane mechanism             HUMAN_ADMITTED / MERGED
Codex SDK live execution                   NOT_EXERCISED
GitHub remote dependency mutation          NOT_EXERCISED
GitHub generic development-link ownership  RESIDUAL
Herdr live observation                     NOT_EXERCISED
real source/provider closure               EVIDENCE_DEPENDENT
Wave‑3 #473 Human Admit / merge / release  NOT_PERFORMED until exact current-head gates and Shadow readback
```

## Wave‑3 live-evidence extension

Historical fork relation and current convergence route:

```text
#455 exact head 847e56c3...  fork-time TRUE_PARENT; later admitted through #455 merge
├─ #464 / PR #469  Codex live acceptance carrier        TRUE_CHILD at fork / selected leaf
├─ #465 / PR #470  GitHub reversible dependency canary TRUE_CHILD at fork / selected leaf
├─ #466 / PR #471  Herdr lifecycle carrier             TRUE_CHILD at fork / selected leaf
└─ #467 / PR #472  immutable source-claim compiler     TRUE_CHILD at fork / selected leaf
          ↓ exact selected bytes
#468 / PR #473     CONVERGENCE; must also consume current `main` before final admission
```

#469–#472 are siblings of one another because they consumed #455 but not each other. `WAVE3_PARENT_ADMISSION.md` owns the current parent-state correction; `WAVE3_LIVE_EVIDENCE.md` owns the detailed Wave‑3 State Machine and immutable fork-time integration; PR #473 owns all shared route/index updates for this wave.

The live-evidence Local Handoff Queue is a continuation contract only. It may point to live Codex, Herdr and reversible GitHub canary commands, but the queue itself cannot prove those commands ran or promote their receipts.

## Completion report

Before declaring this directory synchronized, report current repository subject, selected/consumed parent subjects, candidate/admitted distinction, changed routes, issue/PR graph changes, exact evidence subjects, hosted workflow denominator, unresolved source/runtime items, stale external snapshots, rejected/superseded candidates, rollback subject, and all `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, `EVIDENCE_DEPENDENT`, and `HUMAN_ADMIT_REQUIRED` states.
