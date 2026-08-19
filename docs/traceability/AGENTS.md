# AGENTS.md — traceability and closure routing

Read this file before adding or changing repository-wide traceability, Tech Lead/Shadow closure, source-problem mappings, issue/PR graphs, Molecular Stack indexes, or external consumer snapshots.

## Read order

1. repository root `AGENTS.md`, `CONTEXT.md`, `ARCHITECTURE.md`;
2. `docs/INDEX.md` and `docs/architecture/STATE_MACHINES.md`;
3. `TRACEABILITY_INDEX.md`;
4. `TECH_LEAD_SHADOW_CLOSURE.md`;
5. `CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md` for the admitted #379 static/deterministic convergence, merge provenance, consumed sibling publication state and remaining live evidence owners;
6. `CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md` for the pre-admission State Machine, denominator, rejected epochs and evidence ceilings;
7. `WAVE3_PARENT_ADMISSION.md` before #464–#468 decisions; it records the transition of #455 from fork-time unmerged true parent to Human-admitted `main` history;
8. `WAVE3_LIVE_EVIDENCE.md` for the Wave-3 State Machine, carriers, reversible GitHub canary, source compiler, immutable integration checkpoint and Local Handoff Queue;
9. `skills/agentic-tech-lead-orchestration/AGENTS.md`, README and SKILL;
10. selected control-plane execution packet/module/contracts when the trigger matches;
11. `skills/procedural-shadow-runtime/README.md`;
12. `skills/git-town-stacked-pr-worker/README.md`;
13. exact issue/PR/workflow/runtime/evidence subjects.

## Authority

Traceability documents are human projections. They may route to machine truth but must never replace schemas, current GitHub metadata, Git ancestry, runtime receipts, source readback, CI execution, or Human Admit.

`CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md` records the immutable static/deterministic admission subject for #379. `WAVE3_PARENT_ADMISSION.md` records the later fork/admission transition needed to interpret Wave 3. Current mutable issue/runtime/main state must still be read from GitHub and owning runtime receipts.

A convergence branch may consume exact sibling candidate bytes for integration testing. Such ancestry proves byte consumption only; it does **not** promote an unadmitted sibling PR itself to `MERGED`. After #455 admission, its consumed sibling PRs remain closed-unmerged publication lineage while their exact bytes are present on `main` through the convergence merge.

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

Exactly one convergence writer owns each shared traceability/index subject. Parallel implementation lanes remain siblings unless a child consumes named unmerged parent bytes at its fork epoch. A convergence commit may have several sibling parents to make consumed bytes inspectable; those parents remain siblings of each other. Shadow reviewers do not mutate the Tech Lead's implementation branch.

## Codex control-plane program

```text
#375 / PR #451  Codex SDK controller/session adapter       SIBLING / CLOSED-UNMERGED / CONSUMED
#376 / PR #452  GitHub Issue DAG projection               SIBLING / CLOSED-UNMERGED / CONSUMED
#377 / PR #456  Herdr observer v3                         SIBLING / CLOSED-UNMERGED / CONSUMED
#378 / PR #457  problem-closure ledger v3                 SIBLING / CLOSED-UNMERGED / CONSUMED
PR #380         design/traceability foundation            DOCUMENTATION SIBLING / CLOSED-UNMERGED / CONSUMED
      ↓ exact consumed bytes
#379 / PR #455  control-plane convergence                 HUMAN_ADMITTED / MERGED
```

Admitted Wave-2 subjects:

```text
candidate head  847e56c3418fce920c42d983e84ee44fdc6e8971
merge commit    ca31e0b1e640f0dba2c3d94da9d9786fbed32f2c
shared tree     8a75271851f2e9dd47dd3a019c93e4a0f9272d24
```

Post-merge admission documentation was itself admitted through PR #475. Current `main` must always be read live; at the Wave-3 v2 reconciliation epoch it was observed at `4be4d6744fe432e4be24d94750bb4fc034aab189`.

Historical rejected/closed-unmerged implementation candidates remain part of the denominator. They are not alternate merge candidates.

Current deterministic denominator already admitted on `main`:

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
#455 convergence                        MERGED / HUMAN_ADMITTED_STATIC_SCOPE
release / production promotion         NOT_PERFORMED
```

Issues #375–#378 remain open owners for their live/residual evidence lanes. Do not close them merely because their static mechanism bytes landed through #455.

## Wave-3 live-evidence extension

Fork-time provenance and current replacement convergence are distinct facts:

```text
#455 exact head 847e56c3...  fork-time TRUE_PARENT; now admitted on main
├─ #464 / PR #469  Codex live acceptance carrier         TRUE_CHILD at fork / selected leaf
├─ #465 / PR #470  GitHub reversible dependency canary  TRUE_CHILD at fork / selected leaf
├─ #466 / PR #471  Herdr lifecycle carrier              TRUE_CHILD at fork / selected leaf
└─ #467 / PR #472  immutable source-claim compiler      TRUE_CHILD at fork / selected leaf
          ↓ exact selected bytes
#468 / PR #473     REJECTED convergence lineage; functional/document gates passed, commit-role provenance rejected one accidental noop ancestor
#468 / PR #479     CURRENT replacement convergence candidate
```

#469–#472 are siblings of one another because they consumed #455 but not each other. PR #479 reuses the exact final Wave-3 semantic tree while excluding the rejected accidental `3fe0a79...` noop ancestry, then reconciles current admitted #475 routes instead of overwriting them.

Wave-3 static infrastructure does not itself prove live effects:

```text
Codex live acceptance carrier       deterministic mechanism; runtime NOT_EXERCISED
GitHub reversible canary            deterministic mechanism; remote NOT_EXERCISED
Herdr lifecycle carrier             deterministic mechanism; runtime NOT_EXERCISED
source-claim compiler               deterministic binding; truth/provider EVIDENCE_DEPENDENT
Wave-3 Local Handoff Queue          continuation contract; commands NOT_EXECUTED by queue validation
#479 Human Admit / merge / release  NOT_PERFORMED
```

## Completion report

Before declaring this directory synchronized, report current repository subject, selected/consumed parent subjects, candidate/admitted distinction, changed routes, issue/PR graph changes, exact evidence subjects, hosted workflow denominator, unresolved source/runtime items, stale external snapshots, rejected/superseded candidates, rollback subject, and all `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, `EVIDENCE_DEPENDENT`, and `HUMAN_ADMIT_REQUIRED` states.
