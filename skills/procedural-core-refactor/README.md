# procedural-core-refactor

Canonical repository method for refactoring a shared Skill into a portable procedural core plus trigger-selected domain modules without losing executable closure.

## Current integration state

| Surface | State | Owner / evidence |
|---|---|---|
| Portable method and typed refactor contract | `IMPLEMENTED` | issue #327 / PR #330 |
| Deterministic checker and mutation suite | `PASS / DETERMINISTIC_FIXTURE` | issue #328 / PR #331 |
| Agentic Tech Lead structural golden proof | `PASS / DETERMINISTIC_FIXTURE` | #308 exact proof head |
| Production-shaped real-task proof | `PASS / SYNTHETIC_RUNTIME` | #312 / #315 exact proof head |
| Registry and entry-route admission | `IMPLEMENTED` in convergence candidate | issue #329 |
| Owning Skill Suites CI + golden-proof artifact | `NOT_EXERCISED` until exact-head run | issue #329 |
| Live model/provider/delivery dominance | `NOT_EXERCISED` | #231/#232/#234/#256/#312 Phase 2 |
| Merge/promotion | `HUMAN_ADMIT_REQUIRED` | repository authority |

The golden proof establishes deterministic structural and synthetic orchestration closure. It does not establish model quality uplift or live delivery.

## Read order

1. repository `AGENTS.md` and the target Skill's nearest instructions;
2. this README for directory ownership and current state;
3. `SKILL.md` for the portable refactor state machine and hard laws;
4. `references/refactor-contract.schema.json` and `references/example-refactor-contract.json`;
5. `modules/README.md`, then only target modules selected by frozen triggers;
6. `references/golden-proof.schema.json` and the selected proof ledger;
7. `scripts/README.md`, `tests/README.md`, and `tests/run-all.sh`;
8. `cases.json` and `evals.json` for claim and mutation routing;
9. exact issue, branch, PR, head/tree, workflow job and evidence artifact.

## Directory ownership

```text
procedural-core-refactor/
├── SKILL.md
│   └── portable procedure, states, PCR-LAW IDs, evidence ceilings, stop/handoff
├── README.md
│   └── read order, current integration state, directory/DAG/data-flow index
├── modules/
│   ├── README.md
│   └── trigger-selected target proof/domain specializations
├── references/
│   └── typed refactor/proof schemas, immutable treatment identities and examples
├── scripts/
│   └── deterministic assertions and receipt emitters
├── tests/
│   └── positive, hollow, mutation and matched-proof controls
├── cases.json
│   └── case inventory and negative-control expectations
└── evals.json
    └── runnable claim → checker → test → proof routing
```

Ownership is exclusive. Provider, repository, host, credential, live index and consumer command details do not move into the portable `SKILL.md` merely because they are useful examples.

## State machine by directory

| State | Primary owner | Input | Output / admission evidence |
|---|---|---|---|
| `REQUEST_BOUND` | issue + `references/` | exact target/repository/authority | typed refactor request |
| `BASELINE_FROZEN` | `references/` | old Skill/modules/scripts/tests | immutable treatment digests and strengths/failures |
| `OWNERSHIP_CLASSIFIED` | `SKILL.md` + contract | baseline inventory | one owner per load-bearing atom |
| `CORE_EXTRACTED` | target `SKILL.md` | classified method atoms | provider-neutral procedure with stable laws |
| `DOMAIN_MODULED` | target `modules/` | classified instance atoms | trigger/non-trigger/input/output/fallback contracts |
| `ROUTES_WIRED` | target entry docs | core, modules, schemas, assertions | resolvable entry graph |
| `ASSERTIONS_BOUND` | `scripts/` + `tests/` | law manifest | executable positive/refusal/mechanism controls |
| `STRUCTURAL_AB` | `tests/` + `references/` | immutable treatments | old strengths, regressions and repaired dimensions |
| `REAL_TASK_AB` | admitted harness/consumer | matched task/base/tests/budgets/carrier | output/global/cleanup receipts or `NOT_EXERCISED` |
| `GOLDEN_PROOF_ADMITTED` | proof schema/checker | structural and real-task records | scope-bounded golden-proof receipt |
| `REGISTRY_INDEXED` | registry/README/entry routes/CI | admitted Skill and proof | discoverable repository route |
| `DELIVERY_HANDOFF` | issue/PR/Stack index | exact heads and CI states | reviewable molecular Stack + residual lanes |

## DAG responsibilities

```text
#327 / PR #330  contract/method leaf
  produces refactor schema + PCR-LAW identities
       │
       ▼
#328 / PR #331  executable proof child
  consumes schema/laws
  produces checker + mutations + Tech Lead golden proof
       │
       ▼
#329 / convergence PR
  consumes admitted proof contracts
  updates AGENTS/README/registry/entry routes/CI/Stack index
```

This is a true serial Stack because each child consumes unmerged parent contracts. Path-disjoint live runtime lanes remain parallel and are not converted into fake parent/child edges.

## Data flow

```text
refactor request
→ freeze exact old/current subjects
→ classify portable vs domain vs executable ownership
→ extract SKILL.md procedural core
→ create trigger-selected modules
→ wire entry/module/assertion routes
→ bind every PCR-LAW to checker + mutation
→ structural old/B0/repaired A/B
→ matched real-task A/B when behavior is claimed
→ admit scope-bounded golden proof
→ registry + AGENTS + README + entry routes + CI
→ molecular Stack handoff
→ live runtime/provider/delivery lanes or Human admission
```

## Parallelism rule

Parallelize only when two slices have disjoint write/resource ownership and neither consumes the other's unmerged contracts or bytes. Use a Stack edge only when the child has a real predecessor dependency. One convergence owner updates shared indexes, registry, generated projections or aggregate proof state after prerequisites are verified.

## Local verification

```bash
sh skills/procedural-core-refactor/tests/run-all.sh
```

The command validates schemas, positive contract/proof semantics, law/module routes, evidence ceilings and planted mutations. Its PASS remains `DETERMINISTIC_FIXTURE`.

## Golden-proof subjects

```text
A   OLD_MONOLITH             a01f53592cda98f61b413b4467afa96356fb4ef7
B0  REFACTOR_AS_LANDED       8b2da7443aff7a9f53412b5af280048203bbd5e9
B1  REACHABILITY_REPAIRED    51c3fd81749598957f2b993c4d31c3b4c8c277c1
B2  CAUSAL_DAG_REPAIRED      3fd01571b49b1dfd1c9256661fe4aafe3ecc6e99

structural proof head         504c18f10d3380be4874a59f7cfad5c290daa93f
real-task proof head          403a4f041c5f8c07b0d7c8bb0ef2ccc44ac0f113
```

## Traceability

- Epic: #326
- Contract/method: #327 / PR #330 / head `cffa44526d0d3e895256df36c2c7a1628fff49e2`
- Executable proof: #328 / PR #331 / head `f65e19c848831f2fcac5ed1f9c66e80b5680243f`
- Repository convergence: #329 / convergence branch `refactor/329-procedural-core-convergence`
- Tech Lead causal repair: #307 / PR #308
- Production-shaped A/B: #312 / PR #315
- Remaining live lanes: #231, #232, #234, #256 and #312 Phase 2

PR metadata and exact-head CI/artifact receipts remain publication truth. This README cannot turn a pending or absent run into PASS.
