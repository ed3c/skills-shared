# Cross-Skill adoption audit — issue #322

<!-- GENERATED FILE — do not edit by hand. -->

Rendered from [`skills/skill-refactor-proof-loop/references/skill-adoption-ledger.json`](../../skills/skill-refactor-proof-loop/references/skill-adoption-ledger.json) by [`skills/skill-refactor-proof-loop/scripts/render_adoption_audit.py`](../../skills/skill-refactor-proof-loop/scripts/render_adoption_audit.py).
Regenerate with `python3 skills/skill-refactor-proof-loop/scripts/render_adoption_audit.py`; `--check` re-renders and byte-compares this file.
`skills/skill-refactor-proof-loop/tests/run-all.sh` runs that `--check`, so a stale report is a red suite.

The standard this audit applies was admitted by [`skills/skill-refactor-proof-loop/evals/proof-standard-admission.json`](../../skills/skill-refactor-proof-loop/evals/proof-standard-admission.json):
approver `ed3c (repository owner)`, decided `2026-08-17`, `ADMITTED_FOR_BOUND_SCOPE`,
subject `ed3c/skills-shared@ce68a05` landed via PR #338.
That record is a decision. It reports no run, no receipt and no measurement, and it promoted no
Skill's proof level. Every state below is as measured by
[`skills/skill-refactor-proof-loop/scripts/check_skill_adoption_ledger.py`](../../skills/skill-refactor-proof-loop/scripts/check_skill_adoption_ledger.py)
against current repository bytes.

## Headline

| Measure | Value |
|---|---|
| Skills classified | 10 |
| Criteria per Skill | 10 |
| Classification cells | 100 |
| `PASS` cells | 32 |
| Non-`PASS` gaps | 68 |
| Gaps carrying an owning issue | 68 |
| Distinct owning issues | 14 |
| Golden proofs registered | 1 |
| Migration leaves ordered | 10 |

Highest proof layer reached, per Skill:

| Layer | Skills |
|---|---|
| `L2_EXECUTABLE_CONTRACT` | 9 |
| `L3_HERMETIC_REAL_TASK` | 1 |

Every classification cell, by state:

| State | Cells |
|---|---|
| `PASS` | 32 |
| `PARTIAL` | 8 |
| `ABSENT` | 50 |
| `NOT_IMPLEMENTED` | 4 |
| `NOT_EXERCISED` | 6 |
| `NOT_APPLICABLE` | 0 |
| `HUMAN_ADMIT_REQUIRED` | 0 |

## Per-Skill classification

Column keys, in the order the standard asserts them:

```text
FROZEN_A   old_canonical_treatment_frozen
FROZEN_B0  refactor_as_landed_treatment_frozen
STRENGTHS  old_strengths_asserted
ROUTES     route_reachable
GATES      schema_and_semantic_gates_executable
CONTROLS   hollow_dead_route_controls
HERMETIC   matched_hermetic_task
GOLDEN     golden_proof_registered
LIVE_AB    live_model_runtime_ab
DELIVERY   molecular_traceability
```

| Skill | Layer | Proof | FROZEN_A | FROZEN_B0 | STRENGTHS | ROUTES | GATES | CONTROLS | HERMETIC | GOLDEN | LIVE_AB | DELIVERY |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `agentic-tech-lead-orchestration` | `L3_HERMETIC_REAL_TASK` | `agentic-tech-lead-real-task-ab-v1` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `NOT_EXERCISED` | `PARTIAL` |
| `controlled-technical-language-harness` | `L2_EXECUTABLE_CONTRACT` | none | `ABSENT` | `ABSENT` | `ABSENT` | `PASS` | `PARTIAL` | `PASS` | `PARTIAL` | `ABSENT` | `NOT_EXERCISED` | `ABSENT` |
| `dual-forge-repository-loop` | `L2_EXECUTABLE_CONTRACT` | none | `ABSENT` | `ABSENT` | `ABSENT` | `PASS` | `PASS` | `PASS` | `PARTIAL` | `ABSENT` | `NOT_EXERCISED` | `ABSENT` |
| `forgejo-delivery-loop` | `L2_EXECUTABLE_CONTRACT` | none | `ABSENT` | `ABSENT` | `ABSENT` | `PASS` | `PASS` | `PASS` | `ABSENT` | `ABSENT` | `NOT_IMPLEMENTED` | `ABSENT` |
| `git-town-stacked-pr-worker` | `L2_EXECUTABLE_CONTRACT` | none | `ABSENT` | `ABSENT` | `ABSENT` | `PASS` | `PASS` | `PASS` | `ABSENT` | `ABSENT` | `NOT_EXERCISED` | `ABSENT` |
| `github-delivery-loop` | `L2_EXECUTABLE_CONTRACT` | none | `ABSENT` | `ABSENT` | `ABSENT` | `PASS` | `PARTIAL` | `PASS` | `ABSENT` | `ABSENT` | `NOT_IMPLEMENTED` | `ABSENT` |
| `knowledge-continuity` | `L2_EXECUTABLE_CONTRACT` | none | `ABSENT` | `ABSENT` | `ABSENT` | `PASS` | `PARTIAL` | `PASS` | `ABSENT` | `ABSENT` | `NOT_IMPLEMENTED` | `ABSENT` |
| `procedural-shadow-runtime` | `L2_EXECUTABLE_CONTRACT` | none | `ABSENT` | `ABSENT` | `ABSENT` | `PASS` | `PASS` | `PASS` | `PARTIAL` | `ABSENT` | `NOT_EXERCISED` | `ABSENT` |
| `repository-capability-audit` | `L2_EXECUTABLE_CONTRACT` | none | `ABSENT` | `ABSENT` | `ABSENT` | `PASS` | `PASS` | `PASS` | `PARTIAL` | `ABSENT` | `NOT_EXERCISED` | `ABSENT` |
| `spatial-loop-systems-engineering` | `L2_EXECUTABLE_CONTRACT` | none | `ABSENT` | `ABSENT` | `ABSENT` | `PASS` | `PASS` | `PASS` | `ABSENT` | `ABSENT` | `NOT_IMPLEMENTED` | `ABSENT` |

## Gaps by owner issue

Every non-`PASS` cell above appears exactly once below, under the issue that owns it.
An issue listed here is not a duplicate of the audit: it already exists in the ledger's
`known_issues` (#231, #232, #234, #256, #312, #318, #322, #343, #344, #345, #346, #347, #348, #349, #350, #351, #352).

### #231 — 1 gap

| Skill | Criterion | State | Why |
|---|---|---|---|
| `agentic-tech-lead-orchestration` | `live_model_runtime_ab` | `NOT_EXERCISED` | Deterministic carrier only; matched live receipts are owned by #231. |

### #232 — 1 gap

| Skill | Criterion | State | Why |
|---|---|---|---|
| `procedural-shadow-runtime` | `live_model_runtime_ab` | `NOT_EXERCISED` | Independent Shadow receipts are owned by #232. |

### #234 — 3 gaps

| Skill | Criterion | State | Why |
|---|---|---|---|
| `dual-forge-repository-loop` | `live_model_runtime_ab` | `NOT_EXERCISED` | Requires two provider binaries and real spend; delivery receipts are owned by #234. |
| `git-town-stacked-pr-worker` | `live_model_runtime_ab` | `NOT_EXERCISED` | A live canary exists behind an admission file; no admitted run is registered. |
| `github-delivery-loop` | `live_model_runtime_ab` | `NOT_IMPLEMENTED` | Publication receipts are delivery evidence, not a matched model/runtime comparison. |

### #256 — 2 gaps

| Skill | Criterion | State | Why |
|---|---|---|---|
| `repository-capability-audit` | `matched_hermetic_task` | `PARTIAL` | The matrix is preregistered and scored deterministically, but every cell needs a real host binary. |
| `repository-capability-audit` | `live_model_runtime_ab` | `NOT_EXERCISED` | Same-subject adapter receipts are owned by #256. |

### #343 — 1 gap

| Skill | Criterion | State | Why |
|---|---|---|---|
| `agentic-tech-lead-orchestration` | `molecular_traceability` | `PARTIAL` | Nodes name their issues and PRs, but their state is declared READ_FROM_GITHUB and cannot be closed by a zero-network audit. |

### #344 — 8 gaps

| Skill | Criterion | State | Why |
|---|---|---|---|
| `controlled-technical-language-harness` | `old_canonical_treatment_frozen` | `ABSENT` | No pre-refactor treatment bytes are frozen anywhere in the Skill. |
| `controlled-technical-language-harness` | `refactor_as_landed_treatment_frozen` | `ABSENT` | — |
| `controlled-technical-language-harness` | `old_strengths_asserted` | `ABSENT` | Without a frozen old treatment there is nothing to assert preservation against. |
| `controlled-technical-language-harness` | `schema_and_semantic_gates_executable` | `PARTIAL` | Semantic and deterministic gates are executable; no machine shape contract (*.schema.json) exists. |
| `controlled-technical-language-harness` | `matched_hermetic_task` | `PARTIAL` | Matched-task fairness is enforced over recorded A/B bundles, not over frozen refactor treatments. |
| `controlled-technical-language-harness` | `golden_proof_registered` | `ABSENT` | — |
| `controlled-technical-language-harness` | `live_model_runtime_ab` | `NOT_EXERCISED` | The scorer consumes live-run bundles; no live bundle is registered as evidence. |
| `controlled-technical-language-harness` | `molecular_traceability` | `ABSENT` | — |

### #345 — 6 gaps

| Skill | Criterion | State | Why |
|---|---|---|---|
| `dual-forge-repository-loop` | `old_canonical_treatment_frozen` | `ABSENT` | — |
| `dual-forge-repository-loop` | `refactor_as_landed_treatment_frozen` | `ABSENT` | — |
| `dual-forge-repository-loop` | `old_strengths_asserted` | `ABSENT` | — |
| `dual-forge-repository-loop` | `matched_hermetic_task` | `PARTIAL` | The cross-stack case set is frozen and checked, but the comparison itself is never executed in the suite. |
| `dual-forge-repository-loop` | `golden_proof_registered` | `ABSENT` | — |
| `dual-forge-repository-loop` | `molecular_traceability` | `ABSENT` | — |

### #346 — 7 gaps

| Skill | Criterion | State | Why |
|---|---|---|---|
| `forgejo-delivery-loop` | `old_canonical_treatment_frozen` | `ABSENT` | — |
| `forgejo-delivery-loop` | `refactor_as_landed_treatment_frozen` | `ABSENT` | — |
| `forgejo-delivery-loop` | `old_strengths_asserted` | `ABSENT` | — |
| `forgejo-delivery-loop` | `matched_hermetic_task` | `ABSENT` | — |
| `forgejo-delivery-loop` | `golden_proof_registered` | `ABSENT` | — |
| `forgejo-delivery-loop` | `live_model_runtime_ab` | `NOT_IMPLEMENTED` | No model/runtime A/B harness exists; live Forgejo delivery receipts are a separate lane. |
| `forgejo-delivery-loop` | `molecular_traceability` | `ABSENT` | — |

### #347 — 6 gaps

| Skill | Criterion | State | Why |
|---|---|---|---|
| `git-town-stacked-pr-worker` | `old_canonical_treatment_frozen` | `ABSENT` | — |
| `git-town-stacked-pr-worker` | `refactor_as_landed_treatment_frozen` | `ABSENT` | — |
| `git-town-stacked-pr-worker` | `old_strengths_asserted` | `ABSENT` | — |
| `git-town-stacked-pr-worker` | `matched_hermetic_task` | `ABSENT` | — |
| `git-town-stacked-pr-worker` | `golden_proof_registered` | `ABSENT` | — |
| `git-town-stacked-pr-worker` | `molecular_traceability` | `ABSENT` | — |

### #348 — 7 gaps

| Skill | Criterion | State | Why |
|---|---|---|---|
| `github-delivery-loop` | `old_canonical_treatment_frozen` | `ABSENT` | — |
| `github-delivery-loop` | `refactor_as_landed_treatment_frozen` | `ABSENT` | — |
| `github-delivery-loop` | `old_strengths_asserted` | `ABSENT` | — |
| `github-delivery-loop` | `schema_and_semantic_gates_executable` | `PARTIAL` | Gates are executable and fail closed, but the delivery receipt shape has no machine schema. |
| `github-delivery-loop` | `matched_hermetic_task` | `ABSENT` | — |
| `github-delivery-loop` | `golden_proof_registered` | `ABSENT` | — |
| `github-delivery-loop` | `molecular_traceability` | `ABSENT` | — |

### #349 — 8 gaps

| Skill | Criterion | State | Why |
|---|---|---|---|
| `knowledge-continuity` | `old_canonical_treatment_frozen` | `ABSENT` | — |
| `knowledge-continuity` | `refactor_as_landed_treatment_frozen` | `ABSENT` | — |
| `knowledge-continuity` | `old_strengths_asserted` | `ABSENT` | — |
| `knowledge-continuity` | `schema_and_semantic_gates_executable` | `PARTIAL` | Four mechanical rules are executable; the human-judgement half of the Skill has no machine gate. |
| `knowledge-continuity` | `matched_hermetic_task` | `ABSENT` | — |
| `knowledge-continuity` | `golden_proof_registered` | `ABSENT` | — |
| `knowledge-continuity` | `live_model_runtime_ab` | `NOT_IMPLEMENTED` | — |
| `knowledge-continuity` | `molecular_traceability` | `ABSENT` | — |

### #350 — 6 gaps

| Skill | Criterion | State | Why |
|---|---|---|---|
| `procedural-shadow-runtime` | `old_canonical_treatment_frozen` | `ABSENT` | — |
| `procedural-shadow-runtime` | `refactor_as_landed_treatment_frozen` | `ABSENT` | — |
| `procedural-shadow-runtime` | `old_strengths_asserted` | `ABSENT` | — |
| `procedural-shadow-runtime` | `matched_hermetic_task` | `PARTIAL` | Arms and trials are deterministic, but they are not bound to frozen refactor treatments of this Skill. |
| `procedural-shadow-runtime` | `golden_proof_registered` | `ABSENT` | — |
| `procedural-shadow-runtime` | `molecular_traceability` | `ABSENT` | — |

### #351 — 5 gaps

| Skill | Criterion | State | Why |
|---|---|---|---|
| `repository-capability-audit` | `old_canonical_treatment_frozen` | `ABSENT` | — |
| `repository-capability-audit` | `refactor_as_landed_treatment_frozen` | `ABSENT` | — |
| `repository-capability-audit` | `old_strengths_asserted` | `ABSENT` | — |
| `repository-capability-audit` | `golden_proof_registered` | `ABSENT` | — |
| `repository-capability-audit` | `molecular_traceability` | `ABSENT` | — |

### #352 — 7 gaps

| Skill | Criterion | State | Why |
|---|---|---|---|
| `spatial-loop-systems-engineering` | `old_canonical_treatment_frozen` | `ABSENT` | — |
| `spatial-loop-systems-engineering` | `refactor_as_landed_treatment_frozen` | `ABSENT` | — |
| `spatial-loop-systems-engineering` | `old_strengths_asserted` | `ABSENT` | — |
| `spatial-loop-systems-engineering` | `matched_hermetic_task` | `ABSENT` | — |
| `spatial-loop-systems-engineering` | `golden_proof_registered` | `ABSENT` | — |
| `spatial-loop-systems-engineering` | `live_model_runtime_ab` | `NOT_IMPLEMENTED` | — |
| `spatial-loop-systems-engineering` | `molecular_traceability` | `ABSENT` | — |

## Migration order

The leaves above are not independent. Each row's `Blocked by` is derived from files that
already resolve or assert a path into another in-scope Skill, so closing them out of order
means freezing a treatment whose bytes are still moving underneath it. `Basis` names the
files the edge was read out of; the checker requires every one of them to exist.

This sequence is not a preference. `check_skill_adoption_ledger.py` discards it, recomputes it
from `depends_on` alone by stable topological sort — alphabetically first Skill whose blockers
are all placed — and refuses the ledger if the recorded list differs or if a cycle means no
order exists. Rows with no blocker are genuinely unordered against each other; only the
alphabetical tie-break fixes where they land.

| # | Skill | Leaf | Blocked by | Why | Basis |
|---|---|---|---|---|---|
| 1 | `agentic-tech-lead-orchestration` | #343 | — | Blocked by no other leaf, and it is the only Skill whose golden proof is registered, so its treatments are the one worked instance the other nine copy. | — |
| 2 | `controlled-technical-language-harness` | #344 | — | No file under this Skill's scripts, tests, evals, references or contracts resolves a path into any other in-scope Skill. | — |
| 3 | `forgejo-delivery-loop` | #346 | — | No file under this Skill's scripts, tests, evals, references or contracts resolves a path into any other in-scope Skill. | — |
| 4 | `github-delivery-loop` | #348 | — | No file under this Skill's scripts, tests, evals, references or contracts resolves a path into any other in-scope Skill; two of them resolve paths into this one. | — |
| 5 | `dual-forge-repository-loop` | #345 | `github-delivery-loop` | check_dual_forge_contract.py load_module()s github-delivery-loop/scripts/ci_publish_gate.py and ci_workflow_policy.py at gate time, so this Skill's executable contract is literally the other Skill's code running. | `skills/dual-forge-repository-loop/scripts/check_dual_forge_contract.py`, `skills/github-delivery-loop/scripts/ci_publish_gate.py`, `skills/github-delivery-loop/scripts/ci_workflow_policy.py` |
| 6 | `git-town-stacked-pr-worker` | #347 | `github-delivery-loop` | check_publication_boundary.py require_markers() the literal string github-delivery-loop in this Skill's own publication surface, so freezing a treatment here freezes text bound to the other Skill's contract. | `skills/git-town-stacked-pr-worker/scripts/check_publication_boundary.py`, `skills/git-town-stacked-pr-worker/references/GITHUB_ACTIONS_PUBLICATION_ADOPTION.md` |
| 7 | `knowledge-continuity` | #349 | — | No file under this Skill's scripts, tests, evals, references or contracts resolves a path into any other in-scope Skill. | — |
| 8 | `spatial-loop-systems-engineering` | #352 | `forgejo-delivery-loop` | recovery-escalation/verify.sh require_literal()s forgejo-delivery-loop in the escalation overlay, so this Skill's hollow-route control is red the moment the other Skill's name moves. | `skills/spatial-loop-systems-engineering/tests/recovery-escalation/verify.sh`, `skills/spatial-loop-systems-engineering/references/three-failure-escalation.md` |
| 9 | `repository-capability-audit` | #351 | `controlled-technical-language-harness`, `github-delivery-loop`, `knowledge-continuity`, `spatial-loop-systems-engineering` | run_pilot_matrix.py SOURCE_SKILLS names these four as measured subjects and test_source_contribution.py scores them by name, so a matched hermetic task here is comparing bytes those four Skills own. | `skills/repository-capability-audit/scripts/run_pilot_matrix.py`, `skills/repository-capability-audit/tests/test_source_contribution.py`, `skills/repository-capability-audit/evals/held-out-corpus.json` |
| 10 | `procedural-shadow-runtime` | #350 | `git-town-stacked-pr-worker`, `repository-capability-audit` | summarise_uplift_matrix.py opens repository-capability-audit/evals/uplift-preregistration.json from a module-level constant, and the capsule and receipt fixtures pin git-town-stacked-pr-worker/SKILL.md as the procedure source. The reverse edge is not symmetric: repository-capability-audit only names this Skill's artifacts as inert preregistration data, and no script of its own reads them. | `skills/procedural-shadow-runtime/scripts/summarise_uplift_matrix.py`, `skills/repository-capability-audit/evals/uplift-preregistration.json`, `skills/procedural-shadow-runtime/tests/fixtures/valid-capsule.json` |

## Evidence boundary

This report proves inventory and gap classification against current bytes. It does not prove
model uplift, provider operation, scheduler or Shadow enforcement, Git Town/Forgejo delivery,
merge, release or production readiness. `molecular_traceability` cannot reach `PASS` here at all:
the audit is zero-network, and no offline byte proves current issue or PR delivery state.

The migration order proves coupling between Skills as their current bytes express it. It is not a
schedule, not an estimate, and not an assignment: it says which leaf would be freezing a moving
target if it went first, and nothing about when any of them is worked or by whom.
