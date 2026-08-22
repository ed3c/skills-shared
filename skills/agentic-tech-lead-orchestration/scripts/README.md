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

### `run_codex_sdk_worker.py` — #375 / #505 hardening

```text
static invocation
  frozen session manifest → STATIC_VALIDATED / STATIC_CONTRACT_ONLY

--execute
  existing signed-in Codex auth
  → start/resume compatible thread in exact clean worktree
  → post-turn changed-path + lease readback
  → private temporary index seeded from frozen base
  → immutable detached post-turn Git tree
  → exact base→result-tree denominator readback
  → RUNTIME_RESULT_ONLY
  → controller source/diff/test readback still required
```

`--execute` additionally requires `--carrier-out-dir`: a result tree with no durable carrier is not a replayable receipt (#508). The live result is emitted as `schema_version: 2` and carries `executor_provenance` (adapter version/blob digest, `openai-codex` version, resolved binary identity and SHA-256, runtime/model/config identity, sandbox/approval policy) plus `result_carrier`. A signed-in session is never recorded as executable provenance, and auth values, tokens, prompts, private reasoning and model prose remain forbidden.

The adapter rejects unsafe/overlapping repository path leases, prompt-digest drift, incompatible thread reuse, credential-bearing durable fields, and full model/private-reasoning persistence. After the live turn it does **not** commit, move a branch, or mutate the normal index. Instead it writes the post-turn bytes as a detached Git tree using `GIT_INDEX_FILE`, then verifies that `git diff --name-only --no-renames <base_sha> <tree_sha>` exactly matches its observed changed-file denominator. The runtime result carries both `base_tree_sha` and the post-turn `tree_sha` so the two phases cannot share one ambiguous tree identity. `--execute` is not used by the shared deterministic suite.

### `codex_result_carrier.py` / `check_codex_worker_result.py` — #508

```text
POST_TURN_TREE_MATERIALIZED
→ DURABLE_OBJECT_CARRIER_BOUND      refs/evidence/codex-v2/<id>/{base,result}
→ CARRIER_MANIFEST_DIGEST_BOUND     manifest + content-addressed bundle SHA-256
→ INDEPENDENT_CLONE_OR_BUNDLE_READBACK
→ RESULT_TREE_REPLAY_PASS
```

`codex_result_carrier.py create` publishes the base and result trees as two **parentless** evidence commits under a hidden `refs/evidence/codex-v2/` namespace and packs exactly those two refs into a Git bundle with a sidecar manifest. Parentless is deliberate: the carrier transports the two trees under comparison, not the history behind them. The implementation branch is never moved and nothing depends on reflog or accidental object retention.

`codex_result_carrier.py replay` resolves the result tree from bundle + manifest alone, in a bare scratch repository created outside the originating repository with every inherited `GIT_DIR`/alternates variable stripped, then recomputes the changed-path denominator. A tree that survives only in the originating object store cannot satisfy this readback.

`check_codex_worker_result.py` is the shape + semantic gate for the live worker result. `references/contracts/codex-worker-result-v2.schema.json` owns the Draft 2020-12 shape (`additionalProperties: false`, `schema_version` pinned to `2` so a historical v1 receipt cannot arrive here). The script owns what a schema cannot express: the adapter blob digest is recomputed from the adapter that would actually execute, a recorded binary digest is recomputed from disk, `SDK_BUNDLED` and `PATH` must agree with where the executable actually lives, and the carrier manifest must name this exact task/attempt, repository, base and result tree. `--carrier-bundle` additionally performs the offline replay.

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

`../tests/run-all.sh` validates the Wave-2/Wave-3 control-plane schemas and executes the owning selftests. It intentionally does not execute Codex, mutate GitHub dependencies, invoke Herdr, or infer real source/provider closure.

## Behavioral A/B (spends real tokens only on explicit live invocation)

`run_behavioral_ab.py` answers whether the repaired modular body changes what a live host orchestrates compared with a frozen treatment. `--selftest` is cheap, deterministic, zero-network and never invokes a model. The live run is a separate explicitly-argumented invocation whose receipts land in `../evals/`.

## Refactor boundary

`check_skill_core_boundaries.py --skill agentic-tech-lead-orchestration` verifies portable-core/domain-module separation. It does not admit tasks, capabilities, scheduler results, control-plane runtime results, or handoff execution.

## Gate preservation — #605

Every other script here judges the tree in front of it, so none of them can see a gate that is no longer there: when a merge deletes a check, the suite goes green *because* the check vanished. Shadow-proven twice on this repository — the #466 receipt paper gate was deleted by a merge, and two per-queue selftest invocations were dropped.

`check_gate_preservation.py` takes the range, not the tree, as its subject. It reports a gate file (`assert_*`/`check_*`, `run-all.sh`, `verify.sh`, `*selftest*.py`, workflow) that existed at the base and is gone at HEAD, and an invocation line that a shell runner or workflow carried at the base and no longer carries. A deleted invocation whose exact text reappears anywhere in the same range is a move, not a deletion. An intended retirement must be named with `--allow <substring>` at the call site; there is no heuristic that decides a deletion was meant.

The base is `--base`, else `GITHUB_BASE_REF` through `merge-base` (the suite's CI job checks out with `fetch-depth: 0` for exactly this reason), else the first parent of HEAD — which is the pre-merge base of a merge commit. A shallow checkout, a root commit, a non-git tree, or a base that resolves to HEAD itself prints `GATE-PRESERVATION-SKIPPED_BY_POLICY` with the reason. An unreadable base is never reported as an audited green (#576 class).

```bash
python3 scripts/check_gate_preservation.py --selftest
python3 scripts/check_gate_preservation.py [--base <rev>] [--allow <substring>]
```

## Exit contract

```text
0   the named gate passed for the declared subject/evidence mode
2   the input was evaluable and a contract/causal violation was found
64  usage, JSON, or required input was invalid/absent where supported
70  validator, schema, or assertion mechanism was unavailable/invalid where supported
```

## Wave 3 live-evidence carriers — #464–#467

These scripts consume the Wave-2 adapters/checkers. They do not replace them and they do not own the Tech Lead semantic DAG.

### `compile_codex_live_acceptance.py` — #464 / #505 hardening

The historical v1 binder compared worker/controller document identity and digests but did not touch Git. The first real #464 run proved that this was insufficient: two internally consistent documents could bind the pre-turn tree while the claimed change existed only as an uncommitted worktree modification.

The current binder emits receipt v2 only after all prior runtime/lease/controller checks **and** independent Git truth:

```text
base_sha resolves to base_tree_sha
post-turn tree_sha resolves to a Git tree
Git diff(base_sha, tree_sha) == exact changed_files denominator
→ result_tree_readback=PASS
→ LIVE_RUNTIME_AND_CONTROLLER_READBACK_CANDIDATE
```

Since #508 the binder no longer reads the originating worktree at all. It validates the worker result against `codex-worker-result-v2.schema.json` through `check_codex_worker_result.py`, then replays the durable carrier named in `carrier_bundle_path`:

```text
worker result validated against the committed schema
carrier manifest names this repo/base/result tree and denominator
bundle + manifest replay in a scratch repository
→ result_tree_replay=PASS
```

A bound tree missing the claimed change, containing an undeclared extra change, resolving to no carried tree object, or disagreeing with `base_sha` now fails closed even when worker and controller repeat the same false values — and it fails closed after the originating worktree has been deleted. Output remains Shadow-pending. This deterministic repair does not promote #464's live lane; the earlier run remains `LIVE_EXECUTION_OBSERVED / SHADOW_READBACK_PARTIAL` until a fresh signed-in run produces a v2-bound result and independent Shadow readback.

Raw model prose, prompt bytes, private reasoning, auth material, tokens, credentials and API keys are forbidden durable input fields.

### `github_issue_dag_live_canary.py` — #465

Owns a single reversible test edge only when both fixture issues are OPEN and carry the declared canary ownership label. It freezes repository identity and the complete original `blockedBy` denominator, adds exactly one edge, reads it back, removes only that edge, and proves the original denominator is restored. Unexpected drift and cleanup failure are terminal.

Static invocation reports `NOT_EXERCISED`; only explicit `--execute` can produce a remote-canary candidate.

### `collect_herdr_lifecycle.py` — #466

Reuses `herdr_runtime_observer.py` over a bounded sample window. Task/attempt/repo/Git/worktree/target plus pane/workspace/PID-start/native-session identity must remain stable; source timestamps cannot regress; nonterminal states require a live process; terminal state requires `CLEAN`/zero residue; no state may follow terminal. `UNAVAILABLE_FALLBACK` is preserved as non-success.

### `compile_source_claims.py` — #467

Converts exact GitHub Issue / ARTICLE / PDF / PRD source records into the existing #378 problem-closure ledger. GitHub issues require `owner/repo#number`; external documents require immutable `sha256:<64hex>` identity plus exact locator. It computes per-claim and complete source-manifest digests, preserves NOT_APPLICABLE/SUPERSEDED rows, and emits no invented verification, receipt, or merge evidence.

## Wave-3 shared gate — #468 / post-admission repair #505

Current deterministic denominator includes eleven Draft-2020-12 control-plane schemas: historical Codex live-acceptance v1 is retained and current v2 is added. The current Codex live acceptance selftest is `1 positive / 16 mutations`; the four new controls are result-tree truth controls and remain zero-provider/zero-network. The GitHub DAG live canary is currently `1/10`; Herdr lifecycle `2/7`; source compiler `4-source/11`.

No deterministic command calls live Codex, live Herdr, or remote GitHub mutation. A green shared gate proves the carrier/checker integration only; it cannot raise the runtime evidence ceiling.
