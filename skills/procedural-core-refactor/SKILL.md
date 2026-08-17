---
name: procedural-core-refactor
description: |
  Portable procedure for refactoring a shared Skill into a provider-neutral procedural core plus trigger-selected domain modules without losing executable assertions, causal runtime transitions, old strengths, matched real-task behavior, evidence ceilings, or issue/PR/evidence traceability.
---

# Procedural Core Refactor

<!-- PORTABLE_CORE_START -->

## Contract

Use this Skill before changing the ownership boundary of another shared `SKILL.md`.

The core owns the refactor procedure, state transitions, hard laws, evidence classes, stop conditions, and proof-admission rules. It does not own the target Skill's provider, host, consumer, renderer, repository, product, credential, or runtime implementation. Those details remain target-owned modules or consumer/runtime artifacts.

A refactor is not complete because the new body is shorter, provider-neutral, or linked to `modules/`. Completion requires both separation and executable closure:

```text
portable ownership boundary
+ entry and module reachability
+ hard-law assertion wiring
+ trigger/predecessor/receipt causality
+ old/new structural A/B
+ matched real-task A/B where behavior is claimed
+ global objective and cleanup
+ exact traceability and evidence ceilings
```

## State machine

```text
REQUEST_BOUND
→ BASELINE_FROZEN
→ OWNERSHIP_CLASSIFIED
→ CORE_EXTRACTED
→ DOMAIN_MODULED
→ ROUTES_WIRED
→ ASSERTIONS_BOUND
→ STRUCTURAL_AB
→ REAL_TASK_AB
→ GOLDEN_PROOF_ADMITTED
→ REGISTRY_INDEXED
→ DELIVERY_HANDOFF
```

A state advances only from its declared predecessor evidence. Missing evidence remains explicit; it is never inferred from file presence or prose.

## Hard laws

- **PCR-LAW-001 — freeze before editing.** Bind the target Skill, exact repository/commit/tree, current `SKILL.md` bytes, module bytes, executable owners, tests, known strengths, known failures, open issues, and authority boundaries before mutation.
- **PCR-LAW-002 — historical treatments are immutable evidence.** Old, refactor-as-landed, repaired, and current treatment bytes are content-addressed. Do not rewrite a historical arm to improve its score.
- **PCR-LAW-003 — preserve strengths and expose regressions.** The comparison must name what the old version did correctly and retain any observed regression in intermediate refactors; a final aggregate score may not hide either.
- **PCR-LAW-004 — portable core owns method only.** `SKILL.md` may own procedure, state, hard laws, evidence ceilings, stop/handoff, typed module-selection rules, and assertion routing. Provider/host/consumer/product instances belong in `modules/` or consumer/runtime repositories.
- **PCR-LAW-005 — modules activate only from frozen triggers.** A module cannot self-activate because a tool is installed, previously used, preferred by a model, or linked from Markdown. Selection binds trigger evidence, exact module, predecessor states, input/output contract, fallback, evidence ceiling, and authority ceiling.
- **PCR-LAW-006 — every hard law reaches executable proof.** Each law binds an executable owner, command, success/refusal/mechanism result, positive control, and planted negative control. Markdown explanation is not an assertion.
- **PCR-LAW-007 — reachability and causality are separate gates.** Entry-to-script/module reachability proves only that a route exists. Runtime contribution additionally requires selected predecessors, identity-matched invocation/receipt evidence, predecessor-output consumption, and downstream-state admission.
- **PCR-LAW-008 — evidence cannot self-promote.** Static schema, fixture, mock, synthetic canary, provider hit, process exit zero, issue state, or Skill prose cannot become live runtime/model/delivery `PASS` without the corresponding exact-subject receipt.
- **PCR-LAW-009 — behavioral A/B must be matched.** When a refactor claims runtime or behavioral parity/uplift, all arms use the same task, base/tree, contracts, immutable tests, budgets, carrier policy, repetitions, outcome denominator, and global objective. Unequal arms are `INSUFFICIENT_EVIDENCE`.
- **PCR-LAW-010 — local success cannot replace global closure.** Candidate/local oracles, convergence, repository/system invariants, cleanup, residual states, rollback, and Human-owned operations remain separately visible.
- **PCR-LAW-011 — proof must be traceable.** Every state binds issue, branch, PR, exact head/tree, CI run/job, contract/receipt digest, evidence scope, and unresolved lane. Merge, publication, provider activation, permission change, semantic-conflict resolution, release, and promotion remain Human/repository authority.

## Procedure

1. **Bind request and authority.** Record target Skill, refactor objective, non-goals, exact repository subject, allowed write paths, read-only proof artifacts, Human-owned operations, and rollback subject.
2. **Freeze baseline.** Copy or address the old `SKILL.md`, related module profile, executable scripts, tests, and known runtime receipts without editing them. Record content digests and known strengths/failures.
3. **Classify ownership.** For every load-bearing statement or artifact, assign one owner:

   ```text
   portable procedural law       → SKILL.md
   domain/provider/host instance → modules/
   typed stable contract         → references/
   executable assertion          → scripts/
   positive/hollow/mutation/A-B  → tests/
   runnable claim routing        → evals.json / cases.json
   repository navigation/state   → README.md / AGENTS.md
   live bytes/credentials/index  → consumer or runtime repository
   ```
4. **Extract the core.** Preserve method, ordering, evidence boundaries, stop conditions, and old strengths. Remove instance-specific nouns only when an equivalent typed slot and executable route remain.
5. **Create domain modules.** Each module declares trigger, non-trigger, assumptions, inputs, outputs, executable owner, fallback, evidence ceiling, forbidden overrides, and authority ceiling. A module may specialize but never replace a core law.
6. **Wire routes.** Make the entry document route to required schemas, module router, executable assertions, tests, and receipts. Record non-selected modules as `NOT_APPLICABLE`, not silently absent.
7. **Bind assertions.** Create a law-to-assertion manifest. Every law must have a real checker and a planted violation that turns red. Missing mechanism is distinct from semantic failure.
8. **Run structural A/B.** Compare immutable old, refactor-as-landed, and repaired/current treatments. Preserve old strengths, expose intermediate regressions, and report only dimensions the deterministic rubric actually measures.
9. **Run matched real-task A/B when behavior is claimed.** Use real worktrees/processes or the admitted carrier, the same frozen task/base/tests/budgets, retained failures, convergence owner, global oracle, and cleanup. Label deterministic/synthetic results separately from live model/provider behavior.
10. **Admit golden proof.** Validate treatment identities, structural results, real-task results, evidence classes, non-claims, residual lanes, and exact trace links. A proof with missing live evidence can still be valid when it says `NOT_EXERCISED`; it cannot claim live dominance.
11. **Converge repository integration.** Update registry, entry-route/eval-plane manifests, owning CI, `AGENTS.md`, and README state/DAG/data-flow indexes only after the proof contracts exist.
12. **Deliver molecularly.** Use one PR per independently reviewable leaf. A child branch is justified only when it consumes unmerged parent bytes/contracts. Record the Stack and terminal live lanes in `git-town-stacked-pr-worker/README.md`.

## Module contract

Load only modules whose target-specific trigger is frozen in the refactor contract. The runtime path is:

```text
frozen target need
→ trigger evidence
→ selected module
→ predecessor proof
→ exact invocation/assertion owner
→ identity-bound receipt
→ next refactor state
```

Modules may add target examples, adapter commands, or provider/runtime bindings. They may not delete or renumber core law IDs, weaken evidence or authority ceilings, rewrite historical treatments, change matched-arm budgets, hide failed arms, or promote fixture/synthetic evidence.

## Assertion manifest

The refactor contract names, for every `PCR-LAW-*`:

```text
law id
→ executable owner
→ command
→ success code
→ refusal code
→ mechanism/absence code
→ positive control
→ planted negative control
→ proof state admitted
```

`check_refactor_contract.py` and the Tech Lead golden-proof module are introduced by the executable-proof child tracked in issue #328. Until that child lands, executable proof for this new standard is `NOT_IMPLEMENTED`; this contract leaf does not pretend otherwise.

## Evidence states

Keep these mechanically distinct:

```text
IMPLEMENTED
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
INSUFFICIENT_EVIDENCE
CONTESTED
HUMAN_ADMIT_REQUIRED
```

Recommended evidence classes:

```text
STATIC_CONTRACT
DETERMINISTIC_FIXTURE
SYNTHETIC_RUNTIME
ADMITTED_CONSUMER_RUNTIME
MATCHED_LIVE_MODEL
DELIVERY_PROVIDER
HUMAN_ADMISSION
```

A lower class cannot satisfy a higher-class claim.

## Stop and handoff

Stop on unfrozen treatment bytes, ambiguous ownership, deleted old strength, hidden regression, dead entry/assertion/module route, self-activating module, missing law assertion, surviving planted mutation, mismatched A/B arm, omitted failed candidate, failed global objective, residue, stale subject, authority widening, missing trace identity, or unsupported evidence promotion.

Handoff includes the exact baseline and candidate subjects, ownership map, state receipt, module selections, assertion manifest, A/B matrix, golden-proof state, residual lanes, issue/branch/PR/CI index, rollback subject, and next Human/repository authority.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/README.md](modules/README.md). Target-specific golden proofs and worked refactor instances live there; they cannot redefine the portable laws above.
