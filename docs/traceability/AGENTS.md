# AGENTS.md — traceability and closure routing

Read this file before adding or changing repository-wide traceability, Tech Lead/Shadow closure, source-problem mappings, issue/PR graphs, Molecular Stack indexes, or external consumer snapshots.

## Read order

1. repository root `AGENTS.md`, `CONTEXT.md`, `ARCHITECTURE.md`;
2. `docs/INDEX.md` and `docs/architecture/STATE_MACHINES.md`;
3. `TRACEABILITY_INDEX.md`;
4. `TECH_LEAD_SHADOW_CLOSURE.md`;
5. `CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md` when issues #375–#379 or Codex SDK/GitHub DAG/Herdr/problem-closure work is involved;
6. `skills/agentic-tech-lead-orchestration/AGENTS.md`, README and SKILL;
7. selected control-plane execution packet/module/contracts when the trigger matches;
8. `skills/procedural-shadow-runtime/README.md`;
9. `skills/git-town-stacked-pr-worker/README.md`;
10. exact issue/PR/workflow/runtime/evidence subjects.

## Authority

Traceability documents are human projections. They may route to machine truth but must never replace schemas, current GitHub metadata, Git ancestry, runtime receipts, source readback, CI execution, or Human Admit.

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

Exactly one convergence writer owns each shared traceability/index subject. Parallel implementation lanes remain siblings unless a child consumes named unmerged parent bytes. A convergence commit may have several sibling parents to make the consumed bytes inspectable; those parents remain siblings of each other. Shadow reviewers do not mutate the Tech Lead's implementation branch.

## Codex control-plane program

```text
#375 / PR #451  Codex SDK controller/session adapter       SIBLING / STATIC_ADMITTED
#376 / PR #452  GitHub Issue DAG projection               SIBLING / STATIC_ADMITTED
#377 / PR #453  Herdr observer                            SIBLING / STATIC_ADMITTED
#378 / PR #454  problem-closure ledger                    SIBLING / STATIC_ADMITTED
PR #380         design/traceability foundation            SIBLING / DOCUMENTATION
      ↓ exact consumed bytes
#379             control-plane convergence                 CONVERGENCE
```

The canonical working trace is `CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md`. The #379 convergence branch consumes the exact sibling heads rather than copying their implementation from prose. The shared deterministic suite must execute all required control-plane selftests with no `if file exists` bypass.

Static/deterministic implementation and live evidence remain separate:

```text
Codex SDK mechanism                    implemented on convergence subject
Codex SDK live execution               NOT_EXERCISED
GitHub DAG mechanism                   implemented on convergence subject
GitHub remote dependency mutation      NOT_EXERCISED
Herdr observer mechanism               implemented on convergence subject
Herdr live observation                 NOT_EXERCISED
problem-closure mechanism              implemented on convergence subject
real source/provider closure           EVIDENCE_DEPENDENT
merge/release                          HUMAN_ADMIT_REQUIRED
```

## Completion report

Before declaring this directory synchronized, report current repository subject, consumed parent subjects, changed routes, issue/PR graph changes, exact evidence subjects, hosted workflow denominator, unresolved source/runtime items, stale external snapshots, rejected/superseded candidates, rollback subject, and all `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, `EVIDENCE_DEPENDENT`, and `HUMAN_ADMIT_REQUIRED` states.
