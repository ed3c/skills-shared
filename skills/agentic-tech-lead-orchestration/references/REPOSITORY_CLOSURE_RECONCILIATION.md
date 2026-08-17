# Repository closure reconciliation

A repository-wide completion review answers one question: *which real problem is actually closed, by which evidence, on which exact subject?* Documentation drifts silently because every other question is cheaper to answer. This contract makes the drift mechanical.

Machine authority: [`repository-closure-contract.schema.json`](repository-closure-contract.schema.json), [`issue-dual-dag.schema.json`](issue-dual-dag.schema.json) and [`../scripts/assert_repository_closure_contract.py`](../scripts/assert_repository_closure_contract.py). This file explains why those shapes exist; it is not a second verifier.

Law authority: the two load-bearing rules below — the dual dependency DAG and lane non-substitution — are `CORE-LAW-009` and `CORE-LAW-010` in [`../SKILL.md`](../SKILL.md). They are stated here in the reviewer's vocabulary, not owned here.

## Reconciliation order

```text
repository reality readback
→ current integration/closure index
→ nearest directory README
→ code/schema/verifier authority
→ Issue dual DAG
→ Molecular Stack index
→ exact evidence subjects
```

The first hop is a readback of the actual tree, not of a diagram. A directory diagram, a roadmap table, and a status badge are all downstream of `exists`.

## Tree inventory versus documented status

Every governed path carries an observed `exists` boolean and a `documented_status`. Two states are contradictions, not opinions:

| Contradiction | Meaning |
|---|---|
| `exists: true` with `PLANNED` / `NOT_PLANNED` | the work landed and the index never caught up; the reviewer reads a plan and the runtime reads code |
| `exists: false` with `IMPLEMENTED*` / `PARTIAL_CONTRACT` | the index promoted an intention; the path cannot fail a test because it cannot be loaded |

An existing governed path also names its nearest README owner. An owner-less directory has no one to reconcile it next time.

## Real-problem closure matrix

A closure row binds one real problem to one evidence lane and one receipt. The classification states are documentation states; they never replace the runtime vocabulary.

```text
IMPLEMENTED_DRAFT           code exists, contract not yet closed
PARTIAL_CONTRACT            part of the interface is closed and part is open
SYNTHETIC_CLOSED            closed against fixtures/synthetic controls only
INTEGRATION_ADMISSION_OPEN  implemented, waiting on an explicit admission
OPEN_DESIGN                 the problem is not yet decided
BLOCKED_LIVE_SUBSTRATE      only a live substrate can close it and it is absent
```

Evidence kinds stay distinct from runtime outcomes:

```text
SOURCE_REPORTED             a document or a person said so
PRIMARY_SOURCE_CONFIRMED    a primary source confirmed it — still documentation
SYNTHETIC_ANALOG_ONLY       a fixture or analog stood in for the real substrate
HUMAN_ADMIT_REQUIRED        only a Human may close it
DETERMINISTIC_RUN_OBSERVED  a deterministic checker executed on the exact subject
LIVE_SUBSTRATE_OBSERVED     the real substrate was observed on the exact subject
```

Only the last two may carry runtime `PASS`. A confirmed source is still a claim about the world; a fixture is still a fixture. This is the single rule that stops a review from reading its own prose back as a result.

## Evidence lanes

```text
CLOUD  LOCAL  PRIVATE  HUMAN  PROVIDER  PRODUCTION
```

A receipt satisfies the lane it was produced in and no other. A cloud job is not a local checkout; a local run is not a provider or a production release; a private forge is not a public one; nothing substitutes for Human admission. Lane equality is checked literally, because every laundering path in practice is a receipt from a cheaper lane pasted into an expensive one.

## Dual dependency DAG

One Issue graph, two edge classes:

```text
start_dependencies       what must be true before work may begin
completion_dependencies  what must be admitted before work may finish
```

They are not the same set and they are not orderable into one. Start-readiness is cheap and reversible: a contract is readable, a lease is free, no other PR owns the paths. Completion-readiness is expensive and irreversible: the prerequisite is *admitted*, and its receipt names the exact subject and the prerequisite's own lane.

Collapsing the two is how a Stack lands: every child is start-ready the moment its parent branch exists, so a single edge class silently reports the whole Stack as finishable. Each completion edge therefore carries a receipt or the edge is `ABSENT` — never assumed from the branch graph.

A node with more than one completion dependency is a convergence. Exactly one node is the declared `convergence_owner`; any other multi-parent node is hidden convergence and fails closed.

## Publication versus admission

```text
NOT_CREATED  DRAFT  READY  MERGED     publication state
NOT_ADMITTED  ADMITTED                 admission state
```

An uncreated or Draft publication can never be `ADMITTED`. Merge, release, promotion and rollback remain Human-owned; the checker refuses the promotion, it does not perform the admission.

## Evidence ceiling

The checker validates repository bytes with zero network access. A green run proves the closure contract and dual DAG are internally consistent for their declared subject. It does not observe the tree, run a consumer test suite, read a provider, or admit anything. Consumer repositories bind their own paths, Issues, receipts and Human admissions outside this shared directory.
