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

Both commands must return `0` before Worker admission. Shape PASS and semantic PASS are distinct states; neither proves a provider, Worker, worktree, delivery lane, merge, or promotion ran.

## Capability causal DAG

`assert_capability_dag.py` validates `references/capability-plan.schema.json` and `references/capability-receipts.schema.json`. It enforces frozen trigger/selection consistency, predecessor closure, exact task/subject/module identity, predecessor-output consumption, evidence-kind ceilings, source readback where required, fallback policy, and authority ceilings.

Default state admission requires identity-matched `LIVE` receipts. `--fixture-mode` proves only deterministic checker behavior and cannot advance a production runtime state.

`check_runtime_reachability.py --selftest` proves that `SKILL.md → task gates → domain profile → concrete modules → capability assertion → owning test suite` remains reachable. Reachability proves a route exists, not that a module ran.

## Scheduler lifecycle

`assert_scheduler_lifecycle.py` keeps Worker attempts, retry lineage, leases, checkpoints, result states, stale/terminal refusal, accepted-oracle results, and active-lease closure mechanically separate from a static task graph.

A portable lifecycle fixture remains `IMPLEMENTED`; it cannot self-promote to live scheduler `PASS`.

## Local Handoff Execution Queue

`assert_local_handoff_queue.py` is the zero-network hard gate for consumer handoff continuation. It validates exact subject binding, exactly one `ACTIVE` item, predecessor/next ordering, concrete argv/cwd/timeout lanes, durable receipt contracts, evidence-state ceilings, rollback identity, and forbidden automation authority. Its selftest plants stale-subject, dual-active, early-successor, placeholder-command, authority-widening, receipt-laundering, and queue-skip defects.

A queue PASS validates the continuation contract only. It does not execute consumer commands, providers, issue mutations, merges, promotions, or queue advancement.

## Repository closure and Issue dual DAG

`assert_repository_closure_contract.py` is the zero-network gate for a repository-wide completion review. It reconciles documented status against observed tree inventory, keeps documentation evidence kinds from reporting runtime `PASS`, holds cloud/local/private/Human/provider/production receipt lanes literally separate, and keeps start dependencies and completion dependencies as two edge classes with one declared convergence owner.

Shape is owned by `references/repository-closure-contract.schema.json` and `references/issue-dual-dag.schema.json`; this script owns the semantic laws. A green result reports internal consistency for the declared subject. It does not read a consumer tree, run a provider, or admit anything.

## Codex control-plane adapters and closure — #375–#378

These scripts are trigger-selected implementation/evidence bindings. None owns the semantic Tech Lead core, merge, release, or Human Admit.

### `run_codex_sdk_worker.py` — #375

```text
static invocation
  frozen session manifest → STATIC_VALIDATED / STATIC_CONTRACT_ONLY

--execute
  existing signed-in Codex auth
  → start/resume compatible thread in exact worktree
  → runtime result receipt
  → RUNTIME_RESULT_ONLY
  → controller source/diff/test readback still required
```

The adapter rejects unsafe/overlapping repository path leases, prompt-digest drift, incompatible thread reuse, credential-bearing durable fields, and full model/private-reasoning persistence. It never reads a repository API key. `--execute` is not used by the shared deterministic suite.

### `github_issue_dag_projection.py` — #376

```text
asserted semantic dual DAG
→ completion-readiness projection only
→ desired blockedBy denominator
→ exact remote readback
→ ready wave
```

Static mode is zero-network. `--apply` is explicit: it may add missing managed blockers, but any extra remote blocker fails closed before mutation. The adapter does not auto-delete unmanaged dependency state and never treats GitHub metadata as semantic truth. `--apply` is not used by the shared deterministic suite.

### `herdr_runtime_observer.py` — #377

```text
Herdr unavailable → UNAVAILABLE_FALLBACK
Herdr available   → pane/workspace/process/native-session + foreground_cwd observation
                  → RUNNING | BLOCKED | IDLE | DONE_CANDIDATE | UNKNOWN
                  → controller readback still required
```

Live observation requires worktree identity by `foreground_cwd` unless the manifest explicitly changes that policy. The receipt excludes terminal transcripts, credentials and private reasoning. `DONE_CANDIDATE` is never implementation PASS. The shared deterministic suite tests the reducer/fallback only; it does not require Herdr.

### `check_problem_closure.py` / `render_problem_closure.py` — #378

The checker validates the complete problem denominator and independently recomputes declared closure from exact source, repo subject, task/DAG/issue/session-attempt lineage, implementation evidence, verification evidence, typed receipts, Shadow verdict and residual gaps. Verification evidence must have a matching receipt. Issue close and PR merge are not verification lanes.

The renderer emits deterministic Markdown **after** the JSON ledger passes. Its output explicitly declares itself a human projection; it never becomes a second closure authority.

## Control-plane shared gate

`../tests/run-all.sh` now:

```text
validate six control-plane JSON Schemas
→ validate problem-closure example
→ run codex_sdk_controller_selftest.py
→ run github_issue_dag_selftest.py
→ run herdr_observer_selftest.py
→ run problem_closure_selftest.py
→ run deterministic closure checker + renderer projection marker
```

This closes deterministic convergence coverage only. Live Codex, GitHub mutation, Herdr observation, real article/PDF/provider closure and Human/merge/release lanes stay separate.

## Behavioral A/B (spends real tokens only on explicit live invocation)

`run_behavioral_ab.py` answers whether the repaired modular body changes what a live host orchestrates compared with a frozen treatment. `--selftest` is cheap, deterministic, zero-network and never invokes a model. The live run is a separate explicitly-argumented invocation whose receipts land in `../evals/`.

## Refactor boundary

`check_skill_core_boundaries.py --skill agentic-tech-lead-orchestration` verifies portable-core/domain-module separation. It does not admit tasks, capabilities, scheduler results, control-plane runtime results, or handoff execution.

## Exit contract

```text
0   the named gate passed for the declared subject/evidence mode
2   the input was evaluable and a contract/causal violation was found
64  usage, JSON, or required input was invalid/absent where supported
70  validator, schema, or assertion mechanism was unavailable/invalid where supported
```

## Wave 3 live-evidence carriers — #464–#467

These scripts consume the Wave-2 adapters/checkers. They do not replace them and they do not own the Tech Lead semantic DAG.

### `compile_codex_live_acceptance.py` — #464

Binds an actual `run_codex_sdk_worker.py` runtime result to controller-owned source/diff/test readback. It accepts only `sdk_execution=EXERCISED`, `lease_readback=PASS`, a completed turn, exact task/attempt/repo/base/tree identities, exact changed-file denominator, and successful digest-bound controller verification commands. Output remains Shadow-pending.

Raw model prose, prompt bytes, private reasoning, auth material, tokens, credentials and API keys are forbidden durable input fields.

### `github_issue_dag_live_canary.py` — #465

Owns a single reversible test edge only when both fixture issues are OPEN and carry the declared canary ownership label. It freezes repository identity and the complete original `blockedBy` denominator, adds exactly one edge, reads it back, removes only that edge, and proves the original denominator is restored. Unexpected drift and cleanup failure are terminal.

Static invocation reports `NOT_EXERCISED`; only explicit `--execute` can produce a remote-canary candidate.

### `collect_herdr_lifecycle.py` — #466

Reuses `herdr_runtime_observer.py` over a bounded sample window. Task/attempt/repo/Git/worktree/target plus pane/workspace/PID-start/native-session identity must remain stable; source timestamps cannot regress; nonterminal states require a live process; terminal state requires `CLEAN`/zero residue; no state may follow terminal. `UNAVAILABLE_FALLBACK` is preserved as non-success.

### `compile_source_claims.py` — #467

Converts exact GitHub Issue / ARTICLE / PDF / PRD source records into the existing #378 problem-closure ledger. GitHub issues require `owner/repo#number`; external documents require immutable `sha256:<64hex>` identity plus exact locator. It computes per-claim and complete source-manifest digests, preserves NOT_APPLICABLE/SUPERSEDED rows, and emits no invented verification, receipt, or merge evidence.

## Wave-3 shared gate — #468

`../tests/run-all.sh` now extends the denominator to:

```text
10 Draft-2020-12 control-plane schemas
Wave 2 selftests: 4/14 + 6/17 + 4/18 + 6/22
Wave 3 selftests: 1/12 + 1/6 + 2/7 + 4-source/11
source-claims example → compile_source_claims.py → check_problem_closure.py
wave3-live-handoff-queue.json → assert_local_handoff_queue.py
```

No Wave-3 deterministic command calls live Codex, live Herdr, or remote GitHub mutation. A green shared gate proves the carrier/checker integration only; it cannot raise the runtime evidence ceiling.
