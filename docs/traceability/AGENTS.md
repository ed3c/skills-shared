# AGENTS.md — traceability and closure routing

Read this file before adding or changing repository-wide traceability, Tech Lead/Shadow closure, source-problem mappings, issue/PR graphs, Molecular Stack indexes, or external consumer snapshots.

## Read order

1. repository root `AGENTS.md`, `CONTEXT.md`, `ARCHITECTURE.md`;
2. `docs/INDEX.md` and `docs/architecture/STATE_MACHINES.md`;
3. `TRACEABILITY_INDEX.md`;
4. `TECH_LEAD_SHADOW_CLOSURE.md`;
5. `CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md` for the admitted #379 Wave‑2 static/deterministic subject and exact merge provenance;
6. `WAVE3_ADMISSION.md` for the admitted #468 Wave‑3 static/deterministic live-evidence infrastructure subject, actual merge race reconciliation, and remaining live evidence owners;
7. `CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md` for the pre-admission Wave‑2 State Machine, denominator, rejected epochs and evidence ceilings;
8. `WAVE3_PARENT_ADMISSION.md` for Wave‑3 fork/current-main transition history and rejected publication epochs;
9. `WAVE3_LIVE_EVIDENCE.md` for the Wave‑3 carrier contracts, State Machine, deterministic denominator, reversible canary, source compiler and Local Handoff Queue;
10. `skills/agentic-tech-lead-orchestration/AGENTS.md`, README and SKILL;
11. selected control-plane execution packet/module/contracts when the trigger matches;
12. `skills/procedural-shadow-runtime/README.md`;
13. `skills/git-town-stacked-pr-worker/README.md`;
14. exact issue/PR/workflow/runtime/evidence subjects.

## Authority

Traceability documents are human projections. They may route to machine truth but must never replace schemas, current GitHub metadata, Git ancestry, runtime receipts, source readback, CI execution, or Human Admit.

`CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md` freezes the admitted Wave‑2 static/deterministic subject. `WAVE3_ADMISSION.md` freezes the admitted Wave‑3 static/deterministic infrastructure subject and its post-merge reconciliation. Current mutable repository/issue/runtime state must still be read from GitHub and owning runtime receipts.

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

## Wave‑2 control-plane admission

```text
#375 / PR #451  Codex SDK controller/session adapter       SIBLING / CLOSED-UNMERGED / CONSUMED
#376 / PR #452  GitHub Issue DAG projection               SIBLING / CLOSED-UNMERGED / CONSUMED
#377 / PR #456  Herdr observer v3                         SIBLING / CLOSED-UNMERGED / CONSUMED
#378 / PR #457  problem-closure ledger v3                 SIBLING / CLOSED-UNMERGED / CONSUMED
PR #380         design/traceability foundation            DOCUMENTATION SIBLING / CLOSED-UNMERGED / CONSUMED
      ↓ exact candidate bytes
#379 / PR #455  control-plane convergence                 HUMAN_ADMITTED / MERGED
```

Admitted Wave‑2 subject:

```text
#455 candidate  847e56c3418fce920c42d983e84ee44fdc6e8971
#455 merge      ca31e0b1e640f0dba2c3d94da9d9786fbed32f2c
shared tree     8a75271851f2e9dd47dd3a019c93e4a0f9272d24
```

Historical closed-unmerged candidates remain part of the denominator. Human admission of #455 changes repository authority but does not convert any live Codex/GitHub/Herdr/source evidence lane into PASS.

Wave‑2 deterministic denominator:

```text
Codex SDK       4 positive / 14 mutations
GitHub DAG      7 positive / 23 mutations (#497 live_readback producer controls)
Herdr           4 positive / 18 mutations
problem closure 6 positive / 22 mutations
```

## Wave‑3 live-evidence infrastructure admission

Fork-time dependency and consumed leaf subjects:

```text
#455 checked head 847e56c3...  HISTORICAL_TRUE_PARENT
├─ #464 / PR #469  d239d17d...  TRUE_CHILD at fork / CLOSED-UNMERGED / CONSUMED
├─ #465 / PR #470  f4c3215b...  TRUE_CHILD at fork / CLOSED-UNMERGED / CONSUMED
├─ #466 / PR #471  9eb70b2b...  TRUE_CHILD at fork / CLOSED-UNMERGED / CONSUMED
└─ #467 / PR #472  44d779a0...  TRUE_CHILD at fork / CLOSED-UNMERGED / CONSUMED
          ↓ exact selected bytes + current-main reconciliation
#468 / PR #480              CONVERGENCE / HUMAN_ADMITTED / MERGED
```

Admitted Wave‑3 subject:

```text
checked candidate  8a33b9b3994a39e4ebb220a06fe17e33812661f0
checked tree       b2347bf0af8e0bb768abcf2fe847e8844caed228
merge commit       dd86861972f41f6d36c3de7ac156358ed5fae9d5
merge tree         b05ead21c60cfc459dac5f823bd3ce1ca17ff318
actual merge base  36932ca9f8266f17cfd15ee20fb2621f6ef0e437
```

The merge tree differs from the checked candidate tree only because independently admitted PR #482 advanced `main` before GitHub created the merge commit. Exact comparison shows `36932ca9... → dd868619...` contains exactly the Wave‑3 28-path delta, while `8a33b9b... → dd868619...` adds only two UCR post-merge trace files. Read `WAVE3_ADMISSION.md` for the complete reconciliation.

Rejected/stale publication epochs remain explicit:

```text
PR #473 / 87d00514...       REJECTED_BY_COMMIT_ROLE
PR #480 / 1eae9b47...       HISTORICAL_AFTER_MAIN_DRIFT
PR #480 / 8a33b9b3...       HUMAN_ADMITTED_CHECKED_HEAD
```

No force rewrite erased the failed or stale subjects.

Wave‑3 deterministic denominator:

```text
Codex live acceptance      1 positive / 12 mutations
GitHub DAG live canary     1 positive / 6 mutations
Herdr lifecycle            2 positive / 7 mutations
source claim compiler      4 source kinds / 11 mutations
10 control-plane schemas + problem-closure integration + Local Handoff Queue assertion
```

## Current mechanism / evidence split

```text
Wave‑2 control-plane mechanism                  HUMAN_ADMITTED / MERGED
Wave‑3 live-evidence infrastructure             HUMAN_ADMITTED / MERGED
#464 live Codex SDK/controller acceptance       NOT_EXERCISED
#465 live GitHub add/readback/remove canary      NOT_EXERCISED
#466 live Herdr lifecycle                        NOT_EXERCISED
#467 article/PDF/PRD truth                       SOURCE_PROPOSAL / EVIDENCE_DEPENDENT
#467 real source/provider closure                EVIDENCE_DEPENDENT
release / production promotion                   NOT_PERFORMED
```

The Wave‑3 Local Handoff Queue is a continuation contract only. It may route actual live Codex, Herdr and reversible GitHub canary commands, but queue presence, static validation, hosted CI or merge cannot prove those commands ran or promote their receipts.

## Completion report

Before declaring this directory synchronized, report current repository subject, selected/consumed parent subjects, candidate/admitted distinction, changed routes, issue/PR graph changes, exact evidence subjects, hosted workflow denominator, unresolved source/runtime items, stale external snapshots, rejected/superseded candidates, rollback subject, and all `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, `EVIDENCE_DEPENDENT`, and `HUMAN_ADMIT_REQUIRED` states.
