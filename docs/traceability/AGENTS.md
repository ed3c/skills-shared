# AGENTS.md — traceability and closure routing

Read this file before changing repository-wide traceability, Tech Lead/Shadow closure, source-problem mappings, issue/PR graphs, Molecular Stack indexes, or external consumer snapshots.

## Mandatory read order

1. repository root `AGENTS.md`, `CONTEXT.md`, `ARCHITECTURE.md`;
2. `docs/INDEX.md` and `docs/architecture/STATE_MACHINES.md`;
3. [`CURRENT_PUBLIC_REPOSITORY_STATE.md`](CURRENT_PUBLIC_REPOSITORY_STATE.md) — current public closure/evidence/handoff projection;
4. [`TRACEABILITY_INDEX.md`](TRACEABILITY_INDEX.md) — terminal lineage and historical programme index;
5. [`TECH_LEAD_SHADOW_CLOSURE.md`](TECH_LEAD_SHADOW_CLOSURE.md) — closure/evidence law;
6. `CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md` — immutable Wave-2 admission history;
7. `WAVE3_ADMISSION.md` — immutable/admitted Wave-3 infrastructure plus later #465 bounded remote receipt;
8. `CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md`, `WAVE3_PARENT_ADMISSION.md`, `WAVE3_LIVE_EVIDENCE.md` only for historical design/failure/fork details;
9. `skills/agentic-tech-lead-orchestration/AGENTS.md`, README, SKILL and selected contracts/modules;
10. `skills/procedural-shadow-runtime/README.md`;
11. `skills/git-town-stacked-pr-worker/README.md`;
12. exact current issue/PR/workflow/runtime/evidence subjects.

If a historical file conflicts with current GitHub metadata, exact Git subjects, executable contracts, or runtime receipts, the external/machine subject wins.

## Authority

Traceability Markdown is a human projection. It may route to truth but must never replace:

```text
GitHub issue/PR/workflow metadata
Git commit/tree/blob identity
schema/script/verifier output
runtime/provider receipt
source readback
Human/trusted admission
```

Open PR heads are mutable and must not be embedded as durable authority. Failed, stale, rejected, superseded and closed-unmerged subjects remain denominator history.

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

Issue closure, PR merge, workflow green, model agreement, article/PDF prose, Google/CodexDoc navigation, terminal `done`, a historical receipt, or another evidence lane cannot substitute for a later transition.

## Writer / DAG law

Exactly one writer owns each shared current-state/index subject.

```text
SIBLING             path/resource-disjoint work
TRUE_CHILD          consumes named unmerged parent bytes
CONVERGENCE         one owner consumes selected prerequisites / writes shared indexes
PROCESS_DEPENDENCY  ordering without Git ancestry
EXTERNAL_EVIDENCE   independent receipt lane
HISTORICAL          immutable prior subject; not current mutable authority
```

Shadow is read-only on the Tech Lead implementation subject. A multi-parent convergence records byte consumption, not automatic admission of its parents.

## Admitted control-plane lineage

```text
Wave-2 #375/#376/#377/#378 siblings
        ↓ exact selected bytes
#379 / PR #455
        → HUMAN_ADMITTED / MERGED

Wave-3 #464/#465/#466/#467 siblings at fork
        ↓ exact selected bytes
#468 / PR #480
        → HUMAN_ADMITTED / MERGED
        → post-merge closure #484
```

Historical admission denominators remain historical:

```text
Wave-2 at admission
  Codex SDK        4 / 14
  GitHub DAG       6 / 17
  Herdr            4 / 18
  problem closure  6 / 22

Wave-3 at admission
  Codex live binder   1 / 12
  GitHub canary       1 / 6
  Herdr lifecycle     2 / 7
  source compiler     4 source kinds / 11 mutations
```

Post-admission repairs do not rewrite those historical counts. Current GitHub DAG producer controls are `7 positive / 23 mutations` after #497/#504.

## Current mechanism / evidence split

```text
Wave-2 control-plane mechanism                  ADMITTED / MERGED
Wave-3 live-evidence infrastructure             ADMITTED / MERGED
#465 bounded GitHub Issue Dependencies canary   LIVE_GITHUB_DEPENDENCY_CANARY_PASS
                                                 REMOTE_CANARY_EDGE_ONLY
#464 signed-in Codex v2 acceptance              NOT_EXERCISED after #505/#507
#466 real Herdr lifecycle                        NOT_EXERCISED
#467 article/PDF/PRD truth                       SOURCE_PROPOSAL / EVIDENCE_DEPENDENT
#467 source/provider closure                     EVIDENCE_DEPENDENT
#376 generic Development-sidebar ownership       RESIDUAL / MANUAL_OR_UNEXPOSED_API
release / production promotion                  NOT_PERFORMED
```

#465 exact bounded receipt:

```text
workflow run      32296935756
receipt sha256    da227e94215a1b28a9e550546242c8a482bd718f7b35d67f159ccaa95f23efe5
before            []
applied           [486]
cleanup           []
semantic_authority false
```

That receipt cannot satisfy #376's generic Development-link surface.

## Post-admission repairs and public-consumer evidence

```text
#485 / PR #503  Wave-2 → Wave-3 sole live-owner transfer       MERGED
#497 / PR #504  generic blockedBy producer readback repair     MERGED / 7×23
#505 / PR #507  Codex result-tree false-PASS repair            MERGED
#366             real public consumer bootstrap                 CLOSED
consumer PR #53  exact reviewed tree landed unchanged          MERGED
```

The public-consumer closure proves only the hosted `consumer-bootstrap-verification/v1` path and independent consumer-native CI. It does not prove local Codex/Claude discovery, Agent/model/provider execution, release or production safety.

## Source / PDF / article handling

Every source-derived programme must be classified in `CURRENT_PUBLIC_REPOSITORY_STATE.md`. `SOURCE_PROPOSAL` remains the maximum state for source prose itself. Stronger states require exact applicability, implementation and evidence subjects.

Examples of still-open higher lanes include:

```text
#115 STE100/CTL           official pack/Human semantics/live integrated A/B
#362 Dual-Agent C         local executable contract/gates
#316 behavioural A/B      physical matched Agent/runtime repetitions
#368 provider chain       exact causal grepai→SCIP→SQLite→Tree-sitter→Serena run
#357–#373 Product Reverse implementation/user/paid/session evidence
#386 Entropy              current-main C/K/A/E/X/D publication and live deletion/adoption
```

## Local Handoff law

Do not mutate an old queue after its exact subject changes. Historical `wave3-live-handoff-queue.json` remains history.

Current local queue epoch:

[`../../skills/agentic-tech-lead-orchestration/references/public-main-local-handoff-queue-2026-08-20.json`](../../skills/agentic-tech-lead-orchestration/references/public-main-local-handoff-queue-2026-08-20.json)

It contains only the true serial current local item (#464 signed-in Codex v2 acceptance). Independent #376 manual UI, #466 Herdr and #467 external-source lanes remain on their own issues rather than being falsely serialized.

## Completion report

Before declaring this directory synchronized, report:

```text
current repository subject
selected/consumed parent subjects
candidate/admitted/merged distinction
changed routes and index ownership
issue/PR graph changes
exact evidence subjects and denominator
source/PDF/article closure state
stale Stack reconstruction requirements
Local Handoff queue subject
rejected/superseded candidates
remaining ABSENT / NOT_IMPLEMENTED / NOT_EXERCISED /
SKIPPED_BY_POLICY / EVIDENCE_DEPENDENT / HUMAN_ADMIT_REQUIRED
rollback subject
```
