# Reusable contracts

These files are host-neutral and consumer-independent. A schema or example proves shape only; it does not prove that its provider/runtime/effect lane executed.

## Core orchestration contracts

- `task-contract.schema.json` closes the portable task packet shape.
- `example-stack-contract.json` is a positive offline fixture, not a live provider receipt.
- `local-handoff-queue.schema.json` defines the zero-context continuation queue used only after a real host/runtime boundary is reached.
- `example-local-handoff-queue.json` is a generic positive fixture for entry → runtime lane → receipt → exit → next routing; its commands and task IDs are examples only.
- `scheduler-lifecycle.schema.json` defines scheduler/process-worktree lifecycle evidence.
- `fanout-prompt.md` is the standard Worker prompt envelope for Stack and Tournament modes.
- `REPOSITORY_CLOSURE_RECONCILIATION.md` explains the repository-wide completion review: tree inventory versus documented status, the real-problem closure matrix, evidence kinds and lanes, and the two Issue edge classes.
- `repository-closure-contract.schema.json` closes the tree-inventory/closure-matrix shape; `example-repository-closure-contract.json` is a generic positive fixture, not a consumer readback.
- `issue-dual-dag.schema.json` separates start dependencies from completion dependencies inside one Issue graph; `example-issue-dual-dag.json` is its generic positive fixture.
- [`dual-agent-offload/`](dual-agent-offload/README.md) holds the portable local/cloud offload method. [`dual-agent-offload/OFFLOAD_METHOD.md`](dual-agent-offload/OFFLOAD_METHOD.md) is the prose law — state machine, authority roles, idempotency, evidence lanes and the plane boundary; the schemas beside it are shape gates and `tests/dual-agent-offload-contract/verify.py` is the executable authority over their semantics. Runtime wire schemas remain owned by the Runtime Contract Plane repository, never redefined here.

## Codex control-plane contracts — #375–#379

The provider-neutral core remains `SKILL.md`. These files are trigger-selected bindings owned by their issues and converged by #379:

```text
contracts/
├── codex-session-manifest.schema.json      #375 immutable task/attempt/worktree/session input
├── codex-worker-result.schema.json         #375 model self-report shape; never acceptance proof
├── github-issue-dag-receipt.schema.json    #376 projection/readback receipt
├── github-ready-wave.schema.json           #376 dispatch projection after graph/readback checks
├── herdr-observer-receipt.schema.json      #377 optional observer identity/state receipt
└── problem-closure.schema.json             #378 source→problem→evidence→Shadow closure ledger

examples/
├── herdr-runtime-binding.example.json      #377 generic host-neutral binding example
└── problem-closure.example.json            #378 deterministic positive closure fixture

execution-packets/
├── 375-codex-sdk.md
├── 376-github-issue-dag.md
├── 377-herdr-observer.md
└── 378-problem-closure.md
```

The execution packets freeze zero-context read order, writable/read-only lease, State Machine, worker prompt, controls, evidence ceiling, cleanup/rollback and #379 convergence handoff. They are historical/frozen task contracts for these implementation atoms; current runtime truth still comes from exact issue/PR/workflow/runtime subjects.

Evidence ceilings:

```text
Codex session/result schemas       STATIC SHAPE ONLY
GitHub DAG receipt/ready schemas   STATIC SHAPE ONLY
Herdr observer receipt schema      STATIC SHAPE ONLY
problem-closure schema/example     DETERMINISTIC CLOSURE CONSISTENCY ONLY
live provider/runtime effects      NOT_EXERCISED until exact receipts exist
Human Admit / merge / release      separate authority lanes
```

`tests/run-all.sh` validates all six new schemas as Draft 2020-12, validates the problem-closure example against its schema, and executes the four owning selftests. It intentionally does not execute Codex, mutate GitHub dependencies, invoke Herdr, or infer real source/provider closure.

Consumer repositories bind real commit/tree identities, issue/task references, path leases, commands, provider versions, indexes, budgets, branches, runtime capabilities, receipts, and Human admissions outside this shared directory. They consume these contracts without copying the shared `SKILL.md` body.

## Wave 3 live-evidence contracts — #464–#468

Wave 3 consumes the #455 static/deterministic control-plane bytes. Contract ownership is centralized in #468 so the four path-disjoint leaves do not race on shared schema/index paths.

```text
contracts/
├── codex-live-acceptance-receipt.schema.json   #464 output; controller + runtime candidate
├── github-dag-live-canary-receipt.schema.json  #465 output; one reversible owned edge
├── herdr-lifecycle-receipt.schema.json         #466 output; bounded reduced lifecycle
└── source-claims-input.schema.json              #467 input; immutable claim/source shape

examples/
└── source-claims.example.json                   #468 input → compiler → existing #378 checker

wave3-live-handoff-queue.json                    #468 immutable local/runtime continuation
```

State relation:

```text
#455 TRUE_PARENT
├─ #464/#469 TRUE_CHILD / SIBLING
├─ #465/#470 TRUE_CHILD / SIBLING
├─ #466/#471 TRUE_CHILD / SIBLING
└─ #467/#472 TRUE_CHILD / SIBLING
      ↓ exact selected bytes
#468/#473 CONVERGENCE
```

Shape and runtime evidence remain separate:

```text
codex-live-acceptance receipt schema     shape for a real EXERCISED+controller-readback candidate
GitHub canary receipt schema             shape for remote add/readback/remove proof
Herdr lifecycle receipt schema           shape for live observation or explicit unavailable fallback
source-claims input schema               source/input shape only; compiler + closure checker own semantics
Wave-3 handoff queue                     continuation contract only; execution not implied
```

`tests/run-all.sh` validates ten control-plane Draft 2020-12 schemas, runs all Wave-2 and Wave-3 mutation selftests unconditionally, compiles the source example into the existing problem-closure ledger and rechecks it, and asserts the Wave-3 handoff queue. It does not create live receipts.
