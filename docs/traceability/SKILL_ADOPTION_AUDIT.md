# Cross-Skill adoption audit — issue #322

Generated from `skills/skill-refactor-proof-loop/references/skill-adoption-ledger.json` by `skills/skill-refactor-proof-loop/scripts/render_adoption_report.py`. Do not edit by
hand: CI runs the renderer with `--check` and refuses a byte difference, so an
edit here is reverted rather than believed. Change the ledger.

10 Skill(s) in scope against 10 refactor-proof criteria.
A criterion is one of `PASS`, `PARTIAL`, `NOT_EXERCISED`, `NOT_IMPLEMENTED` or
`ABSENT`; those states do not substitute for one another, and a `PASS` here is a
statement about deterministic repository evidence only.

## Per-Skill state

| Skill | Highest proven layer | Golden proof | PASS | PARTIAL | NOT_EXERCISED | NOT_IMPLEMENTED | ABSENT |
|---|---|---|---|---|---|---|---|
| `agentic-tech-lead-orchestration` | `L3_HERMETIC_REAL_TASK` | `agentic-tech-lead-real-task-ab-v1` | 8 | 1 | 1 | 0 | 0 |
| `controlled-technical-language-harness` | `L2_EXECUTABLE_CONTRACT` | `none` | 2 | 2 | 1 | 0 | 5 |
| `dual-forge-repository-loop` | `L2_EXECUTABLE_CONTRACT` | `none` | 3 | 1 | 1 | 0 | 5 |
| `forgejo-delivery-loop` | `L2_EXECUTABLE_CONTRACT` | `none` | 3 | 0 | 0 | 1 | 6 |
| `git-town-stacked-pr-worker` | `L2_EXECUTABLE_CONTRACT` | `none` | 3 | 0 | 1 | 0 | 6 |
| `github-delivery-loop` | `L2_EXECUTABLE_CONTRACT` | `none` | 2 | 1 | 0 | 1 | 6 |
| `knowledge-continuity` | `L2_EXECUTABLE_CONTRACT` | `none` | 2 | 1 | 0 | 1 | 6 |
| `procedural-shadow-runtime` | `L2_EXECUTABLE_CONTRACT` | `none` | 3 | 1 | 1 | 0 | 5 |
| `repository-capability-audit` | `L2_EXECUTABLE_CONTRACT` | `none` | 3 | 1 | 1 | 0 | 5 |
| `spatial-loop-systems-engineering` | `L2_EXECUTABLE_CONTRACT` | `none` | 3 | 0 | 0 | 1 | 6 |
| **total** | | | 32 | 8 | 6 | 4 | 50 |

## Open criteria

Every criterion that is not `PASS`, with the issue that owns it. A criterion
with no owner issue is unowned work, which is why the column is never blank by
default.

| Skill | Criterion | State | Owner issue | Note |
|---|---|---|---|---|
| `agentic-tech-lead-orchestration` | `live_model_runtime_ab` | `NOT_EXERCISED` | #231 | Deterministic carrier only; matched live receipts are owned by #231. |
| `agentic-tech-lead-orchestration` | `molecular_traceability` | `PARTIAL` | #322 | Nodes name their issues and PRs, but their state is declared READ_FROM_GITHUB and cannot be closed by a zero-network audit. |
| `controlled-technical-language-harness` | `golden_proof_registered` | `ABSENT` | #322 |  |
| `controlled-technical-language-harness` | `live_model_runtime_ab` | `NOT_EXERCISED` | #322 | The scorer consumes live-run bundles; no live bundle is registered as evidence. |
| `controlled-technical-language-harness` | `matched_hermetic_task` | `PARTIAL` | #322 | Matched-task fairness is enforced over recorded A/B bundles, not over frozen refactor treatments. |
| `controlled-technical-language-harness` | `molecular_traceability` | `ABSENT` | #322 |  |
| `controlled-technical-language-harness` | `old_canonical_treatment_frozen` | `ABSENT` | #322 | No pre-refactor treatment bytes are frozen anywhere in the Skill. |
| `controlled-technical-language-harness` | `old_strengths_asserted` | `ABSENT` | #322 | Without a frozen old treatment there is nothing to assert preservation against. |
| `controlled-technical-language-harness` | `refactor_as_landed_treatment_frozen` | `ABSENT` | #322 |  |
| `controlled-technical-language-harness` | `schema_and_semantic_gates_executable` | `PARTIAL` | #322 | Semantic and deterministic gates are executable; no machine shape contract (*.schema.json) exists. |
| `dual-forge-repository-loop` | `golden_proof_registered` | `ABSENT` | #322 |  |
| `dual-forge-repository-loop` | `live_model_runtime_ab` | `NOT_EXERCISED` | #234 | Requires two provider binaries and real spend; delivery receipts are owned by #234. |
| `dual-forge-repository-loop` | `matched_hermetic_task` | `PARTIAL` | #322 | The cross-stack case set is frozen and checked, but the comparison itself is never executed in the suite. |
| `dual-forge-repository-loop` | `molecular_traceability` | `ABSENT` | #322 |  |
| `dual-forge-repository-loop` | `old_canonical_treatment_frozen` | `ABSENT` | #322 |  |
| `dual-forge-repository-loop` | `old_strengths_asserted` | `ABSENT` | #322 |  |
| `dual-forge-repository-loop` | `refactor_as_landed_treatment_frozen` | `ABSENT` | #322 |  |
| `forgejo-delivery-loop` | `golden_proof_registered` | `ABSENT` | #322 |  |
| `forgejo-delivery-loop` | `live_model_runtime_ab` | `NOT_IMPLEMENTED` | #322 | No model/runtime A/B harness exists; live Forgejo delivery receipts are a separate lane. |
| `forgejo-delivery-loop` | `matched_hermetic_task` | `ABSENT` | #322 |  |
| `forgejo-delivery-loop` | `molecular_traceability` | `ABSENT` | #322 |  |
| `forgejo-delivery-loop` | `old_canonical_treatment_frozen` | `ABSENT` | #322 |  |
| `forgejo-delivery-loop` | `old_strengths_asserted` | `ABSENT` | #322 |  |
| `forgejo-delivery-loop` | `refactor_as_landed_treatment_frozen` | `ABSENT` | #322 |  |
| `git-town-stacked-pr-worker` | `golden_proof_registered` | `ABSENT` | #322 |  |
| `git-town-stacked-pr-worker` | `live_model_runtime_ab` | `NOT_EXERCISED` | #234 | A live canary exists behind an admission file; no admitted run is registered. |
| `git-town-stacked-pr-worker` | `matched_hermetic_task` | `ABSENT` | #322 |  |
| `git-town-stacked-pr-worker` | `molecular_traceability` | `ABSENT` | #322 |  |
| `git-town-stacked-pr-worker` | `old_canonical_treatment_frozen` | `ABSENT` | #322 |  |
| `git-town-stacked-pr-worker` | `old_strengths_asserted` | `ABSENT` | #322 |  |
| `git-town-stacked-pr-worker` | `refactor_as_landed_treatment_frozen` | `ABSENT` | #322 |  |
| `github-delivery-loop` | `golden_proof_registered` | `ABSENT` | #322 |  |
| `github-delivery-loop` | `live_model_runtime_ab` | `NOT_IMPLEMENTED` | #234 | Publication receipts are delivery evidence, not a matched model/runtime comparison. |
| `github-delivery-loop` | `matched_hermetic_task` | `ABSENT` | #322 |  |
| `github-delivery-loop` | `molecular_traceability` | `ABSENT` | #322 |  |
| `github-delivery-loop` | `old_canonical_treatment_frozen` | `ABSENT` | #322 |  |
| `github-delivery-loop` | `old_strengths_asserted` | `ABSENT` | #322 |  |
| `github-delivery-loop` | `refactor_as_landed_treatment_frozen` | `ABSENT` | #322 |  |
| `github-delivery-loop` | `schema_and_semantic_gates_executable` | `PARTIAL` | #322 | Gates are executable and fail closed, but the delivery receipt shape has no machine schema. |
| `knowledge-continuity` | `golden_proof_registered` | `ABSENT` | #322 |  |
| `knowledge-continuity` | `live_model_runtime_ab` | `NOT_IMPLEMENTED` | #322 |  |
| `knowledge-continuity` | `matched_hermetic_task` | `ABSENT` | #322 |  |
| `knowledge-continuity` | `molecular_traceability` | `ABSENT` | #322 |  |
| `knowledge-continuity` | `old_canonical_treatment_frozen` | `ABSENT` | #322 |  |
| `knowledge-continuity` | `old_strengths_asserted` | `ABSENT` | #322 |  |
| `knowledge-continuity` | `refactor_as_landed_treatment_frozen` | `ABSENT` | #322 |  |
| `knowledge-continuity` | `schema_and_semantic_gates_executable` | `PARTIAL` | #322 | Four mechanical rules are executable; the human-judgement half of the Skill has no machine gate. |
| `procedural-shadow-runtime` | `golden_proof_registered` | `ABSENT` | #322 |  |
| `procedural-shadow-runtime` | `live_model_runtime_ab` | `NOT_EXERCISED` | #232 | Independent Shadow receipts are owned by #232. |
| `procedural-shadow-runtime` | `matched_hermetic_task` | `PARTIAL` | #322 | Arms and trials are deterministic, but they are not bound to frozen refactor treatments of this Skill. |
| `procedural-shadow-runtime` | `molecular_traceability` | `ABSENT` | #322 |  |
| `procedural-shadow-runtime` | `old_canonical_treatment_frozen` | `ABSENT` | #322 |  |
| `procedural-shadow-runtime` | `old_strengths_asserted` | `ABSENT` | #322 |  |
| `procedural-shadow-runtime` | `refactor_as_landed_treatment_frozen` | `ABSENT` | #322 |  |
| `repository-capability-audit` | `golden_proof_registered` | `ABSENT` | #322 |  |
| `repository-capability-audit` | `live_model_runtime_ab` | `NOT_EXERCISED` | #256 | Same-subject adapter receipts are owned by #256. |
| `repository-capability-audit` | `matched_hermetic_task` | `PARTIAL` | #256 | The matrix is preregistered and scored deterministically, but every cell needs a real host binary. |
| `repository-capability-audit` | `molecular_traceability` | `ABSENT` | #322 |  |
| `repository-capability-audit` | `old_canonical_treatment_frozen` | `ABSENT` | #322 |  |
| `repository-capability-audit` | `old_strengths_asserted` | `ABSENT` | #322 |  |
| `repository-capability-audit` | `refactor_as_landed_treatment_frozen` | `ABSENT` | #322 |  |
| `spatial-loop-systems-engineering` | `golden_proof_registered` | `ABSENT` | #322 |  |
| `spatial-loop-systems-engineering` | `live_model_runtime_ab` | `NOT_IMPLEMENTED` | #322 |  |
| `spatial-loop-systems-engineering` | `matched_hermetic_task` | `ABSENT` | #322 |  |
| `spatial-loop-systems-engineering` | `molecular_traceability` | `ABSENT` | #322 |  |
| `spatial-loop-systems-engineering` | `old_canonical_treatment_frozen` | `ABSENT` | #322 |  |
| `spatial-loop-systems-engineering` | `old_strengths_asserted` | `ABSENT` | #322 |  |
| `spatial-loop-systems-engineering` | `refactor_as_landed_treatment_frozen` | `ABSENT` | #322 |  |

68 open criterion row(s). Known issue lanes: #231, #232, #234, #256, #312, #318, #322.

## Evidence boundary

This report is a projection of a zero-network ledger. It cannot promote any row
to a live-model, delivery, release or Human-admitted state, and `PASS` on
`molecular_traceability` is impossible here by construction: those node states
are read from the forge, not from this tree.
