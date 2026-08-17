# Agentic Tech Lead capability profile

Historical product/tool-specific orchestration detail remains recoverable from pre-refactor blob `a01f53592cda98f61b413b4467afa96356fb4ef7`.

## Trigger
Load when concrete code-intelligence providers, symbol/index adapters, structural parsers, bounded executor tools, vector projections, scheduler/runtime implementations, tournament execution, or consumer repository delivery integrations must be bound.

## Non-trigger
Do not load for generic task-contract compilation, DAG construction, dependency validation, path/resource leasing, worker admission, candidate comparison, convergence, global-objective verification, or delivery handoff when no concrete adapter is required.

## Assumptions
The orchestration problem can be expressed as typed task packets with explicit inputs, outputs, dependencies, owners, budgets, evidence oracles, and convergence rules before choosing tools. Module selection is derived from that frozen task packet; a module never activates itself from executable presence, model preference, provider availability, or a previous run.

## Specialization inventory and selection router

Select the smallest matching set. Every decision must be materialized as a transition in `../references/capability-plan.schema.json`; a Markdown link alone is not an execution decision. Every selected module path becomes part of the task evidence and every non-matching module remains unloaded.

| Frozen task need / trigger | Load exactly this module | Typical produced state |
|---|---|---|
| exact-subject Def/Ref/call/type impact graph, normalized SQLite evidence, or structural AST/CST slicing is required | [`deterministic-code-intelligence.md`](deterministic-code-intelligence.md) | `DETERMINISTIC_CONTEXT_READY` |
| conceptual intent cannot be located reliably by exact search and semantic seed discovery is admitted | [`semantic-intent-anchor.md`](semantic-intent-anchor.md) | `INTENT_ANCHORED` |
| an admitted Worker must execute bounded edits inside an isolated workspace/lease | [`agent-executor.md`](agent-executor.md) | `ATTEMPTS_EXECUTED` |
| optional semantic/example retrieval benefits from a rebuildable vector projection | [`vector-store.md`](vector-store.md) | `VECTOR_CONTEXT_READY` |
| branch/Stack synchronization or forge handoff is actually required by the task and repository policy admits it | [`stacked-delivery.md`](stacked-delivery.md) | `DELIVERY_HANDOFF` |
| multiple independent candidates implement the same locked contract and a deterministic tournament is requested | [`tournament-mode.md`](tournament-mode.md) | `CANDIDATES_COMPARED` |

For navigation and authority ceilings, [`README.md`](README.md) indexes the same modules. The table above is normative for module identity; `../references/example-capability-plan.json` demonstrates the causal transition shape. Neither README nor module presence may widen selection.

## Selection state

Record one transition per capability before execution:

```text
id
module_path
trigger.matched
trigger.evidence[]
selection = REQUIRED | OPTIONAL_SELECTED | NOT_APPLICABLE
predecessor_transitions[]
requires_states[]
produces_state
required_before_state
fallback = STOP | DIRECT_SOURCE | SINGLE_WORKER | SKIP
runtime_state = NOT_EXERCISED
subject / provider identity when selected
```

`REQUIRED` implies `fallback=STOP`. `NOT_APPLICABLE` implies `trigger.matched=false`, `fallback=SKIP`, no invocation, and no receipt. `OPTIONAL_SELECTED` requires a matched trigger; if its provider is unavailable, an admitted fallback must be represented by an identity-bound receipt rather than a silent substitution.

## Runtime transition law

A selected Markdown module is `IMPLEMENTED` procedure, not runtime `PASS`. The runtime may advance across a module-dependent boundary only through this chain:

```text
selected predecessor receipts + required core states
→ frozen trigger evidence
→ exact module path
→ invocation on frozen task subject
→ capability receipt
→ scripts/assert_capability_dag.py --admit-state <STATE>
→ downstream state
```

The receipt contract is `../references/capability-receipts.schema.json`. Every receipt binds task id, exact subject, transition id, module path, attempt id, input states, output state, evidence digest, evidence kind, readback state, and authority ceiling. A predecessor transition is closed only when its receipt output appears in the dependent receipt's `input_states`.

`FIXTURE` receipts are allowed only in deterministic tests with `--fixture-mode`. Default/live admission rejects them. Installation, process exit zero, a Markdown route, or a plan row can never replace a live receipt.

## Evidence ceiling
A provider hit, parsed graph, symbol index, vector retrieval, executor exit, Stack synchronization, or worker self-report is candidate/transport evidence only. Exact source readback and owning assertions remain higher authority. A module success cannot be copied into another module, provider, repository, worktree, model/harness, forge, CI, or merge state.

## Fallback
When optional intelligence/execution providers are absent, fall back only through the transition's declared fallback and emit a receipt for that fallback when it contributes to a downstream state. Direct source reads, version-control search, compiler/language-service output, deterministic tests, and bounded single-worker execution may lower capability requirements while preserving unsupported lanes explicitly. When a required capability is unavailable, stop rather than silently substituting an unadmitted provider.

## Forbidden overrides
This module and every linked child module may not override `CORE-LAW-001` through `CORE-LAW-006`, fabricate DAG dependencies, accept overlapping writers, promote provider output without readback, suppress failed workers/dissent, weaken or skip `scripts/assert_task_contract.py` or `scripts/assert_capability_dag.py`, consume a predecessor state without its receipt, promote `FIXTURE` evidence to live runtime, widen filesystem/network/secret/provider/merge authority, or auto-activate itself because a tool is installed.
