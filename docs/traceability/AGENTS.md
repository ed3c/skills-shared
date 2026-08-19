# AGENTS.md — traceability and closure routing

Read this file before adding or changing repository-wide traceability, Tech Lead/Shadow closure, source-problem mappings, issue/PR graphs, Molecular Stack indexes, or external consumer snapshots.

## Read order

1. repository root `AGENTS.md`, `CONTEXT.md`, `ARCHITECTURE.md`;
2. `docs/INDEX.md` and `docs/architecture/STATE_MACHINES.md`;
3. `TRACEABILITY_INDEX.md`;
4. `TECH_LEAD_SHADOW_CLOSURE.md`;
5. `CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md` when issues #375–#379 or the admitted Codex control-plane convergence is involved;
6. `CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md` for the pre-admission State Machine, denominator, rejected epochs, and evidence ceilings;
7. `skills/agentic-tech-lead-orchestration/AGENTS.md`, README and SKILL;
8. selected control-plane execution packet/module/contracts when the trigger matches;
9. `skills/procedural-shadow-runtime/README.md`;
10. `skills/git-town-stacked-pr-worker/README.md`;
11. exact issue/PR/workflow/runtime/evidence subjects.

## Authority

Traceability documents are human projections. They may route to machine truth but must never replace schemas, current GitHub metadata, Git ancestry, runtime receipts, source readback, CI execution, or Human Admit.

`CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md` records the immutable static/deterministic admission subject for #379. Current mutable issue/runtime state must still be read from GitHub and owning runtime receipts.

A convergence branch may consume exact unmerged sibling candidate bytes for integration testing. Such ancestry proves byte consumption only; it does **not** promote the sibling PR itself to `MERGED`. After #455 admission, the consumed sibling PRs remain closed-unmerged publication lineage while their exact bytes are present on `main` through the convergence merge.

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

Exactly one convergence writer owns each shared traceability/index subject. Parallel implementation lanes remain siblings unless a child consumes named unmerged parent bytes. A convergence commit may have several sibling parents to make consumed bytes inspectable; those parents remain siblings of each other. Shadow reviewers do not mutate the Tech Lead's implementation branch.

## Codex control-plane program

```text
#375 / PR #451  Codex SDK controller/session adapter       SIBLING / CLOSED-UNMERGED / CONSUMED
#376 / PR #452  GitHub Issue DAG projection               SIBLING / CLOSED-UNMERGED / CONSUMED
#377 / PR #456  Herdr observer v3                         SIBLING / CLOSED-UNMERGED / CONSUMED
#378 / PR #457  problem-closure ledger v3                 SIBLING / CLOSED-UNMERGED / CONSUMED
PR #380         design/traceability foundation            DOCUMENTATION SIBLING / CLOSED-UNMERGED / CONSUMED
      ↓ exact consumed bytes
#379 / PR #455  control-plane convergence                 HUMAN_ADMITTED / MERGED
      ↓
main@ca31e0b1e640f0dba2c3d94da9d9786fbed32f2c
```

The admitted candidate is `847e56c3418fce920c42d983e84ee44fdc6e8971`; the merge commit is `ca31e0b1e640f0dba2c3d94da9d9786fbed32f2c`. Both resolve to tree `8a75271851f2e9dd47dd3a019c93e4a0f9272d24`. The admission record owns this historical fact; current `main` must still be read before acting.

Historical rejected/closed-unmerged implementation candidates remain part of the denominator, including #444/#451, #445/#452, #446/#453/#456 lineage, and #447/#454/#457 lineage. They are not alternate merge candidates.

The pre-admission design trace is `CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md`. The shared deterministic suite must execute all required control-plane selftests with no `if file exists` bypass.

Current deterministic denominator:

```text
Codex SDK       4 positive / 14 mutations
GitHub DAG      6 positive / 17 mutations
Herdr           4 positive / 18 mutations
problem closure 6 positive / 22 mutations
```

Static/deterministic implementation and live evidence remain separate:

```text
Codex SDK mechanism                    ADMITTED_ON_MAIN
Codex SDK live execution               NOT_EXERCISED
GitHub DAG mechanism                   ADMITTED_ON_MAIN
GitHub remote dependency mutation      NOT_EXERCISED
GitHub generic development-link scope  RESIDUAL
Herdr observer mechanism               ADMITTED_ON_MAIN
Herdr live observation                 NOT_EXERCISED
problem-closure mechanism              ADMITTED_ON_MAIN
real source/provider closure           EVIDENCE_DEPENDENT
#451/#452/#456/#457/#380 PRs            CLOSED_UNMERGED / CONSUMED
#455 convergence                        MERGED / HUMAN_ADMITTED_STATIC_SCOPE
release / production promotion         NOT_PERFORMED
```

Issues #375–#378 remain open owners for their live/residual evidence lanes. Do not close them merely because their static mechanism bytes landed through #455.

## Completion report

Before declaring this directory synchronized, report current repository subject, admitted/consumed parent subjects, candidate/admitted distinction, changed routes, issue/PR graph changes, exact evidence subjects, hosted workflow denominator, unresolved source/runtime items, stale external snapshots, rejected/superseded candidates, rollback subject, and all `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, `EVIDENCE_DEPENDENT`, and `HUMAN_ADMIT_REQUIRED` states.
