# procedural-core-refactor

Canonical repository method for refactoring a shared Skill into a portable procedural core plus trigger-selected domain modules without losing executable closure.

## Current integration state

| Surface | State | Owner / next step |
|---|---|---|
| Portable method and typed refactor contract | `IMPLEMENTED` in issue #327 | this branch |
| Deterministic checker and mutation suite | `NOT_IMPLEMENTED` | issue #328 |
| Agentic Tech Lead golden-proof ledger | `NOT_IMPLEMENTED` | issue #328, consumes #308/#315 |
| Registry, entry route and CI admission | `NOT_IMPLEMENTED` | issue #329 |
| Live model/provider/delivery dominance | `NOT_EXERCISED` | #231/#232/#234/#256/#312 Phase 2 |
| Merge/promotion | `HUMAN_ADMIT_REQUIRED` | repository authority |

Do not interpret this contract leaf as completed executable proof. It establishes the method and input shape that the child PR must consume.

## Read order

1. repository `AGENTS.md` and the target Skill's nearest instructions;
2. this `README.md` for directory ownership and current state;
3. `SKILL.md` for the portable refactor state machine and hard laws;
4. `references/refactor-contract.schema.json` and `references/example-refactor-contract.json`;
5. `modules/README.md`, then only target modules selected by frozen triggers;
6. `cases.json` and `evals.json` for proof obligations;
7. executable assertions and proof ledger after issue #328 lands.

## Directory ownership

```text
procedural-core-refactor/
├── SKILL.md
│   └── portable procedure, states, PCR-LAW IDs, evidence ceilings, stop/handoff
├── README.md
│   └── read order, current integration state, directory/DAG/data-flow index
├── modules/
│   └── target-specific proof instances and domain/provider/consumer specialization
├── references/
│   └── typed refactor/proof schemas, immutable treatment identities and examples
├── scripts/
│   └── deterministic assertions and receipt emitters; added by issue #328
├── tests/
│   └── positive, hollow, mutation and matched A/B controls; added by issue #328
├── cases.json
│   └── case inventory, inputs, expected state transitions and negative controls
└── evals.json
    └── runnable claim → checker → test → fixture/evidence routing
```

Ownership is exclusive. Provider, repository, host, path, credential, live index and consumer command details do not move into the portable `SKILL.md` merely because they are useful examples.

## State machine by directory

| State | Primary owner | Input | Output / admission evidence |
|---|---|---|---|
| `REQUEST_BOUND` | target issue + `references/` | exact target/repository/authority | typed refactor request |
| `BASELINE_FROZEN` | `references/` | old Skill/modules/scripts/tests | immutable treatment digests and strengths/failures |
| `OWNERSHIP_CLASSIFIED` | `SKILL.md` + contract | baseline inventory | one owner per load-bearing atom |
| `CORE_EXTRACTED` | target `SKILL.md` | classified method atoms | provider-neutral procedure with stable law IDs |
| `DOMAIN_MODULED` | target `modules/` | classified instance atoms | trigger/non-trigger/input/output/fallback contracts |
| `ROUTES_WIRED` | target entry docs | core, modules, schemas, assertions | resolvable entry graph |
| `ASSERTIONS_BOUND` | `scripts/` + `tests/` | law manifest | executable positive/refusal/mechanism controls |
| `STRUCTURAL_AB` | `tests/` + `references/` | immutable treatments | old strengths, regressions and repaired dimensions |
| `REAL_TASK_AB` | admitted harness/consumer | matched task/base/tests/budgets/carrier | output/global/cleanup receipts or `NOT_EXERCISED` |
| `GOLDEN_PROOF_ADMITTED` | proof schema/checker | structural and real-task records | scope-bounded golden-proof receipt |
| `REGISTRY_INDEXED` | repo registry/README/CI | admitted Skill and proof | discoverable and invoked repository route |
| `DELIVERY_HANDOFF` | issue/PR/Stack index | exact heads and CI states | reviewable molecular Stack + residual lanes |

## DAG responsibilities

```text
contract/method leaf (#327)
  produces refactor schema + PCR-LAW identities
       │
       ▼
executable proof child (#328)
  consumes schema/laws
  produces checker + mutations + Tech Lead golden proof
       │
       ▼
repository convergence child (#329)
  consumes admitted proof contracts
  updates AGENTS/README/registry/entry routes/CI/Stack index
```

This is a true serial Stack because each child consumes unmerged parent contracts. Work on path-disjoint live runtime lanes remains parallel and is not converted into fake parent/child edges.

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
→ update registry, AGENTS, READMEs and CI
→ molecular Stack handoff
→ live runtime/provider/delivery lanes or Human admission
```

## Parallelism rule

Parallelize only when two slices have disjoint write/resource ownership and neither consumes the other's unmerged contracts or bytes. Use a Stack edge only when the child has a real predecessor dependency. One convergence owner updates shared indexes, registry, generated projections or aggregate proof state after prerequisites are verified.

## Evidence ceiling

The contract and example in this leaf establish `STATIC_CONTRACT`. They do not establish checker correctness, target refactor correctness, model behavior, provider health, Git Town synchronization, Forgejo/GitHub delivery, merge or production readiness.

## Verification target

Issue #328 will add the canonical command:

```bash
sh skills/procedural-core-refactor/tests/run-all.sh
```

Until that executable owner exists, the truthful state is `NOT_IMPLEMENTED`, not `PASS`.

## Traceability

- Epic: #326
- Contract/method: #327
- Executable proof: #328
- Repository convergence: #329
- Tech Lead causal repair: #308
- Production-shaped A/B: #312 / #315
- Remaining live lanes: #231, #232, #234, #256
