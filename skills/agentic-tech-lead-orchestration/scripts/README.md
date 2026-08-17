# Executable assertions

Each script owns one evidence boundary. A green result from one script never substitutes for another script's state.

## Task packet gates

The portable pre-dispatch contract is a two-stage, zero-network gate. Neither stage invokes a model or provider.

1. `check_task_contract_schema.py` validates packet shape with Draft 2020-12 `references/task-contract.schema.json`. The owning CI installs the pinned `jsonschema` validator. A missing or invalid validator/schema is mechanism error `70`; it is never skipped or converted to PASS.
2. `assert_task_contract.py` is the Python-standard-library semantic/hard-law gate. It validates immutable subjects, safe paths and leases, branch/DAG topology, provider-role separation, exact-subject/readback rules, evidence ceilings, budgets, automation boundaries, Git Town admission, semantic-conflict refusal, Human merge authority, and the prohibition on active `code-graph-rag` dependencies. It mutates only the requested receipt.

```bash
python3 scripts/check_task_contract_schema.py --contract <contract.json>
python3 scripts/assert_task_contract.py --contract <contract.json> --receipt <receipt.json>
```

Both commands must return `0` before Worker admission. Shape PASS and semantic PASS are distinct states; neither proves a provider, Worker, Worktree, delivery lane, merge, or promotion ran.

## Capability causal DAG

`assert_capability_dag.py` validates `references/capability-plan.schema.json` and `references/capability-receipts.schema.json`. It enforces frozen trigger/selection consistency, predecessor closure, exact task/subject/module identity, predecessor-output consumption, evidence-kind ceilings, source readback where required, fallback policy, and authority ceilings.

```bash
python3 scripts/assert_capability_dag.py \
  --contract <contract.json> \
  --plan <capability-plan.json> \
  --receipts <capability-receipts.json> \
  --admit-state <STATE>
```

Default state admission requires identity-matched `LIVE` receipts. `--fixture-mode` proves only deterministic checker behavior and cannot advance a production runtime state.

`check_runtime_reachability.py --selftest` proves that `SKILL.md → task gates → domain profile → concrete modules → capability assertion → owning test suite` remains reachable. Reachability proves a route exists, not that a module ran.

## Scheduler lifecycle

`assert_scheduler_lifecycle.py` keeps Worker attempts, retry lineage, leases, checkpoints, result states, stale/terminal refusal, accepted-oracle results, and active-lease closure mechanically separate from a static task graph.

```bash
python3 scripts/assert_scheduler_lifecycle.py \
  --lifecycle <scheduler-lifecycle.json> \
  --receipt <receipt.json>
```

A portable lifecycle fixture remains `IMPLEMENTED`; it cannot self-promote to live scheduler `PASS`.

## Local Handoff Execution Queue

`assert_local_handoff_queue.py` is the zero-network hard gate for consumer handoff continuation. It validates exact subject binding, exactly one `ACTIVE` item, predecessor/next ordering, concrete argv/cwd/timeout lanes, durable receipt contracts, evidence-state ceilings, rollback identity, and forbidden automation authority. Its selftest plants stale-subject, dual-active, early-successor, placeholder-command, authority-widening, receipt-laundering, and queue-skip defects.

```bash
python3 scripts/assert_local_handoff_queue.py --queue <queue.json>
python3 scripts/assert_local_handoff_queue.py --queue <queue.json> --selftest
```

A queue PASS validates the continuation contract only. It does not execute consumer commands, providers, issue mutations, merges, promotions, or queue advancement.

## Repository closure and Issue dual DAG

`assert_repository_closure_contract.py` is the zero-network gate for a repository-wide completion review. It reconciles documented status against observed tree inventory, keeps documentation evidence kinds from reporting runtime `PASS`, holds cloud/local/private/Human/provider/production receipt lanes literally separate, and keeps start dependencies and completion dependencies as two edge classes with one declared convergence owner. Its selftest plants existing-path-`PLANNED`, absent-path-implemented, source-to-runtime-`PASS`, cross-lane receipt, stale-subject, laundered-admission, Draft-to-admitted, start-as-completion, receipt-less completion, unadmitted-prerequisite, and hidden-convergence defects.

```bash
python3 scripts/assert_repository_closure_contract.py --contract <closure.json> --dag <dual-dag.json>
python3 scripts/assert_repository_closure_contract.py --contract <closure.json> --dag <dual-dag.json> --selftest
```

Shape is owned by `references/repository-closure-contract.schema.json` and `references/issue-dual-dag.schema.json`; this script owns the semantic laws. A green result reports internal consistency for the declared subject. It does not read the tree, run a consumer suite, reach a provider, or admit anything. The method behind the shapes is in [`../references/REPOSITORY_CLOSURE_RECONCILIATION.md`](../references/REPOSITORY_CLOSURE_RECONCILIATION.md).

## Refactor boundary

`check_skill_core_boundaries.py --skill agentic-tech-lead-orchestration` verifies portable-core/domain-module separation. It does not admit tasks, capabilities, scheduler results, or handoff execution.

## Exit contract

```text
0   the named gate passed for the declared subject/evidence mode
2   the input was evaluable and a contract/causal violation was found
64  usage, JSON, or required input was invalid/absent where supported
70  validator, schema, or assertion mechanism was unavailable/invalid where supported
```
