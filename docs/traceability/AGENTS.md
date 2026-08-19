# AGENTS.md — traceability and closure routing

Read this file before adding or changing repository-wide traceability, Tech Lead/Shadow closure, source-problem mappings, issue/PR graphs, Molecular Stack indexes, or external consumer snapshots.

## Read order

1. repository root `AGENTS.md`, `CONTEXT.md`, `ARCHITECTURE.md`;
2. `docs/INDEX.md` and `docs/architecture/STATE_MACHINES.md`;
3. `TRACEABILITY_INDEX.md`;
4. `TECH_LEAD_SHADOW_CLOSURE.md`;
5. `CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md` when issues #375–#379 or Codex SDK/GitHub DAG/Herdr/problem-closure work is involved;
6. `WAVE3_LIVE_EVIDENCE.md` when #464–#468, runtime carriers, reversible GitHub canaries, source compilation, or the live-evidence Local Handoff Queue is involved;
7. `skills/agentic-tech-lead-orchestration/AGENTS.md`, README and SKILL;
8. selected control-plane execution packet/module/contracts when the trigger matches;
9. `skills/procedural-shadow-runtime/README.md`;
10. `skills/git-town-stacked-pr-worker/README.md`;
11. exact issue/PR/workflow/runtime/evidence subjects.

## Authority

Traceability documents are human projections. They may route to machine truth but must never replace schemas, current GitHub metadata, Git ancestry, runtime receipts, source readback, CI execution, or Human Admit.

A convergence branch may consume exact unmerged sibling candidate bytes for integration testing. Such ancestry proves byte consumption only; it does **not** promote the sibling to `ADMITTED`, `MERGED`, or repository truth.

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
#375 / PR #451  Codex SDK controller/session adapter       SIBLING / UNMERGED CANDIDATE
#376 / PR #452  GitHub Issue DAG projection               SIBLING / UNMERGED CANDIDATE
#377 / PR #456  Herdr observer v3                         SIBLING / UNMERGED CANDIDATE
#378 / PR #457  problem-closure ledger v3                 SIBLING / UNMERGED CANDIDATE
PR #380         design/traceability foundation            DOCUMENTATION SIBLING
      ↓ exact candidate bytes
#379 / PR #455  control-plane convergence                 CONVERGENCE CANDIDATE
```

Historical closed-unmerged implementation candidates remain part of the denominator: #446/#453 for #377 and #447/#454 for #378. They are not current merge candidates.

The canonical working trace is `CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md`. The #379 convergence branch consumes exact sibling heads rather than reconstructing implementation from prose. The shared deterministic suite must execute all required control-plane selftests with no `if file exists` bypass.

Current deterministic denominator:

```text
Codex SDK       4 positive / 14 mutations
GitHub DAG      6 positive / 17 mutations
Herdr           4 positive / 18 mutations
problem closure 6 positive / 22 mutations
```

Static/deterministic implementation and live evidence remain separate:

```text
Codex SDK mechanism                    convergence-candidate bytes present
Codex SDK live execution               NOT_EXERCISED
GitHub DAG mechanism                   convergence-candidate bytes present
GitHub remote dependency mutation      NOT_EXERCISED
Herdr observer mechanism               convergence-candidate bytes present
Herdr live observation                 NOT_EXERCISED
problem-closure mechanism              convergence-candidate bytes present
real source/provider closure           EVIDENCE_DEPENDENT
sibling merge/admission                 HUMAN_ADMIT_REQUIRED
#455 merge/release                      HUMAN_ADMIT_REQUIRED
```

## Wave-3 live-evidence extension

```text
#455 / #379
├─ #464 / PR #469  Codex live acceptance carrier         TRUE_CHILD
├─ #465 / PR #470  GitHub reversible dependency canary  TRUE_CHILD
├─ #466 / PR #471  Herdr lifecycle carrier              TRUE_CHILD
└─ #467 / PR #472  immutable source-claim compiler      TRUE_CHILD
          ↓
#468 / PR #473     CONVERGENCE
```

#469–#472 are siblings of one another because they consume #455 but not each other. `WAVE3_LIVE_EVIDENCE.md` owns the detailed State Machine, immutable integration checkpoint, deterministic denominator, queue state and live evidence ceiling. PR #473 owns all shared route/index updates for this wave.

The live-evidence Local Handoff Queue is a continuation contract only. It may point to live Codex, Herdr and reversible GitHub canary commands, but the queue itself cannot prove those commands ran or promote their receipts.

## Completion report

Before declaring this directory synchronized, report current repository subject, selected/consumed parent subjects, candidate/admitted distinction, changed routes, issue/PR graph changes, exact evidence subjects, hosted workflow denominator, unresolved source/runtime items, stale external snapshots, rejected/superseded candidates, rollback subject, and all `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, `EVIDENCE_DEPENDENT`, and `HUMAN_ADMIT_REQUIRED` states.
