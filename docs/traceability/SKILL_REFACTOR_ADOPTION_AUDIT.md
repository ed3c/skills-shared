# Cross-Skill adoption audit — issue #322

<!-- GENERATED FILE — do not edit by hand. -->

Rendered from [`skills/skill-refactor-proof-loop/references/skill-adoption-ledger.json`](../../skills/skill-refactor-proof-loop/references/skill-adoption-ledger.json) by [`skills/skill-refactor-proof-loop/scripts/render_adoption_audit.py`](../../skills/skill-refactor-proof-loop/scripts/render_adoption_audit.py).
Regenerate with `python3 skills/skill-refactor-proof-loop/scripts/render_adoption_audit.py`; `--check` re-renders and byte-compares this file.
`skills/skill-refactor-proof-loop/tests/run-all.sh` runs that `--check`, so a stale report is a red suite.

The standard this audit applies was admitted by [`skills/skill-refactor-proof-loop/evals/proof-standard-admission.json`](../../skills/skill-refactor-proof-loop/evals/proof-standard-admission.json):
approver `ed3c (repository owner)`, decided `2026-08-17`, `ADMITTED_FOR_BOUND_SCOPE`,
subject `ed3c/skills-shared@678e6f7` landed via PR #338 (subject bytes), renewed on branch agent/phase-a-batch.
That record is a decision. It reports no run, no receipt and no measurement, and it promoted no
Skill's proof level. Every state below is as measured by
[`skills/skill-refactor-proof-loop/scripts/check_skill_adoption_ledger.py`](../../skills/skill-refactor-proof-loop/scripts/check_skill_adoption_ledger.py)
against current repository bytes.

**That admission has expired by its own terms.** It expires on any change to the 6 blobs
it names as the admitted subject, and 1 of them no longer hash to the admitted SHA:

- `skills/skill-refactor-proof-loop/references/golden-proof-registry.json`

Re-admission is a new Human record with a new `decided_at`. Nothing in this pipeline re-points the
old one, and this report does not treat the expired record as authority for anything below it.
The measurements are unaffected: they were never derived from the admission in the first place.

## Headline

| Measure | Value |
|---|---|
| Skills classified | 10 |
| Criteria per Skill | 10 |
| Classification cells | 100 |
| `PASS` cells | 80 |
| Non-`PASS` gaps | 20 |
| Gaps carrying an owning issue | 20 |
| Distinct owning issues | 14 |
| Golden proofs registered | 10 |
| Migration leaves ordered | 10 |

Highest proof layer reached, per Skill:

| Layer | Skills |
|---|---|
| `L3_HERMETIC_REAL_TASK` | 10 |

Every classification cell, by state:

| State | Cells |
|---|---|
| `PASS` | 80 |
| `PARTIAL` | 10 |
| `ABSENT` | 0 |
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
| `controlled-technical-language-harness` | `L3_HERMETIC_REAL_TASK` | `controlled-technical-language-refactor-ab-v1` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `NOT_EXERCISED` | `PARTIAL` |
| `dual-forge-repository-loop` | `L3_HERMETIC_REAL_TASK` | `dual-forge-repository-loop-refactor-proof-v1` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `NOT_EXERCISED` | `PARTIAL` |
| `forgejo-delivery-loop` | `L3_HERMETIC_REAL_TASK` | `forgejo-delivery-readback-ab-v1` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `NOT_IMPLEMENTED` | `PARTIAL` |
| `git-town-stacked-pr-worker` | `L3_HERMETIC_REAL_TASK` | `git-town-stacked-pr-worker-refactor-proof-v1` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `NOT_EXERCISED` | `PARTIAL` |
| `github-delivery-loop` | `L3_HERMETIC_REAL_TASK` | `github-delivery-loop-refactor-proof-v1` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `NOT_IMPLEMENTED` | `PARTIAL` |
| `knowledge-continuity` | `L3_HERMETIC_REAL_TASK` | `knowledge-continuity-entrypoint-claim-closure-v1` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `NOT_IMPLEMENTED` | `PARTIAL` |
| `procedural-shadow-runtime` | `L3_HERMETIC_REAL_TASK` | `procedural-shadow-runtime-refactor-ab-v1` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `NOT_EXERCISED` | `PARTIAL` |
| `repository-capability-audit` | `L3_HERMETIC_REAL_TASK` | `repository-capability-audit-refactor-proof-ab-v1` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `NOT_EXERCISED` | `PARTIAL` |
| `spatial-loop-systems-engineering` | `L3_HERMETIC_REAL_TASK` | `spatial-loop-escalation-gate-ab-v1` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `NOT_IMPLEMENTED` | `PARTIAL` |

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
| `git-town-stacked-pr-worker` | `live_model_runtime_ab` | `NOT_EXERCISED` | A live canary exists behind an admission file; no admitted run is registered. The hermetic task below it contacted no Git Town binary, forge or model and cannot raise this lane. |
| `github-delivery-loop` | `live_model_runtime_ab` | `NOT_IMPLEMENTED` | Publication receipts are delivery evidence, not a matched model/runtime comparison. |

### #256 — 1 gap

| Skill | Criterion | State | Why |
|---|---|---|---|
| `repository-capability-audit` | `live_model_runtime_ab` | `NOT_EXERCISED` | Same-subject adapter receipts are owned by #256. The #351 hermetic task did not move this: it observes no model, no provider and no host binary. |

### #343 — 1 gap

| Skill | Criterion | State | Why |
|---|---|---|---|
| `agentic-tech-lead-orchestration` | `molecular_traceability` | `PARTIAL` | Nodes name their issues and PRs, but their state is declared READ_FROM_GITHUB and cannot be closed by a zero-network audit. |

### #344 — 2 gaps

| Skill | Criterion | State | Why |
|---|---|---|---|
| `controlled-technical-language-harness` | `live_model_runtime_ab` | `NOT_EXERCISED` | The scorer consumes live-run bundles; no live bundle is registered as evidence. The frozen-treatment A/B is deterministic text comparison and promotes nothing here. |
| `controlled-technical-language-harness` | `molecular_traceability` | `PARTIAL` | The leaf, its edges and its treatment PRs are indexed in machine artifacts, but refactor-proof-stack.json carries no node for #344 and the delivery state of the ones it does carry is READ_FROM_GITHUB. A zero-network audit cannot close this. |

### #345 — 1 gap

| Skill | Criterion | State | Why |
|---|---|---|---|
| `dual-forge-repository-loop` | `molecular_traceability` | `PARTIAL` | The Stack index names this Skill's delivery lane and its issues, but every node's state is declared READ_FROM_GITHUB. A zero-network checker cannot close it, so PARTIAL is the ceiling rather than a gap awaiting more work here. |

### #346 — 2 gaps

| Skill | Criterion | State | Why |
|---|---|---|---|
| `forgejo-delivery-loop` | `live_model_runtime_ab` | `NOT_IMPLEMENTED` | No model/runtime A/B harness exists; live Forgejo delivery receipts are a separate lane. The matched task injects its three authenticated reads, so nothing in it could become a live observation. |
| `forgejo-delivery-loop` | `molecular_traceability` | `PARTIAL` | The proof names its issue (#346) and the pull requests that landed the frozen treatments (#189 for A, #270 for B0, both read out of the commit subjects at 1295cdd and d757a5c). Forge-side state of those nodes is READ_FROM_GITHUB and a zero-network audit cannot close it. |

### #347 — 1 gap

| Skill | Criterion | State | Why |
|---|---|---|---|
| `git-town-stacked-pr-worker` | `molecular_traceability` | `PARTIAL` | The edge this leaf hangs on is read out of bytes and replayed by check_skill_adoption_ledger.py: migration_order records #347 blocked by github-delivery-loop with the two files that resolve the coupling. What a zero-network audit cannot close is the delivery half — the epic Stack's node states are declared READ_FROM_GITHUB, and no PR node exists for this leaf at all, so PARTIAL is the ceiling by design rather than a missing artefact. |

### #348 — 1 gap

| Skill | Criterion | State | Why |
|---|---|---|---|
| `github-delivery-loop` | `molecular_traceability` | `PARTIAL` | DEC-DELIVERY-14 binds the decision to the commits, the entrypoint and the registry entry, but the zero-network checkers cannot observe issue #348's own PR, review or merge state, and this leaf has no node in the Stack index. PASS is refused by design, not pending. |

### #349 — 2 gaps

| Skill | Criterion | State | Why |
|---|---|---|---|
| `knowledge-continuity` | `live_model_runtime_ab` | `NOT_IMPLEMENTED` | No live model or provider lane exists for this Skill; nothing here was run against one. |
| `knowledge-continuity` | `molecular_traceability` | `PARTIAL` | The leaf, its owner issue and its ordering edges are machine-checked here; PR, head and delivery state are GitHub facts this zero-network checker refuses to assert. |

### #350 — 1 gap

| Skill | Criterion | State | Why |
|---|---|---|---|
| `procedural-shadow-runtime` | `molecular_traceability` | `PARTIAL` | The proof report names its issue, its four treatment blobs and the commit each came from, and the Stack index carries this leaf under #322. It has no node of its own: that file has one convergence owner and is not this leaf's write. Node delivery state is declared READ_FROM_GITHUB either way, so a zero-network checker cannot reach PASS here by design. |

### #351 — 1 gap

| Skill | Criterion | State | Why |
|---|---|---|---|
| `repository-capability-audit` | `molecular_traceability` | `PARTIAL` | The proof report names its issue, its treatment lineage and the commit each treatment blob came from. This leaf has no node of its own in the Stack index: that file has one convergence owner and is not this leaf's write. Either way node delivery state is declared READ_FROM_GITHUB, so a zero-network audit cannot reach PASS here by design. |

### #352 — 2 gaps

| Skill | Criterion | State | Why |
|---|---|---|---|
| `spatial-loop-systems-engineering` | `live_model_runtime_ab` | `NOT_IMPLEMENTED` | No model/runtime A/B harness exists for this Skill; the proof arms are frozen text and deterministic checkers only. |
| `spatial-loop-systems-engineering` | `molecular_traceability` | `PARTIAL` | The registry entry names issue #352 and the two publication subjects this repository records for the leaf (#136 in the traceability index, #189 in the delivery-loop index). Their live state is READ_FROM_GITHUB and a zero-network audit cannot close it. |

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
