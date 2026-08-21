# Test controls

`run-all.sh` is the shared deterministic convergence entrypoint. It executes the positive examples and independent mutation cases for provider role/subject separation, active code-graph-rag rejection, path leases, DAG cycles, Git Town admission, semantic-conflict blocking, evidence ceilings, Human Admit, scheduler lifecycle, the matched real-task A/B, and the Codex control-plane adapters/closure contracts.

## Codex control-plane denominator — #375–#378

The convergence suite executes four required selftests unconditionally. The immutable Wave-2 admitted denominator remains:

| Test | Positive denominator | Mutation denominator | Live lane |
|---|---:|---:|---|
| `codex_sdk_controller_selftest.py` | 4 | 14 | historical mechanism; live owned by #464 |
| `github_issue_dag_selftest.py` | 6 | 17 | historical mechanism; live owned by #465 |
| `herdr_observer_selftest.py` | 4 | 18 | historical mechanism; live owned by #466 |
| `problem_closure_selftest.py` | 6 | 22 | historical mechanism; source/provider owned by #467 |

The Codex denominator includes exact 40-hex subject checks, clean-worktree preflight, ancestor/descendant lease conflict, repository-path escape refusal, and post-turn changed-file readback that rejects read-only/out-of-lease mutations. Post-admission #505 additionally exercises detached result-tree materialization inside the same `4/14` high-level producer denominator; it does not rewrite the historical admitted count.

The current GitHub-DAG projection has separately advanced under #497 to `7 positive / 23 mutations`, adding producer controls for the live `blockedBy` connection-shaped response. The Wave-2 admitted `6/17` row above remains history rather than being rewritten. Generic development-link ownership beyond the closing-reference surface remains a separate residual.

The Herdr denominator binds exact Git subjects, worktree/pane/workspace/PID/native-session identity, PID start time, bounded observation freshness, nonterminal process liveness and terminal cleanup/residue before `DONE_CANDIDATE`. The problem-closure denominator binds a frozen source manifest and complete problem ID set, exact 40-hex repo subjects, portable worktree identity, current/historical implementation evidence, exact-subject verification receipts, supersession targets/cycles, residual gaps and deterministic Markdown projection.

The suite also validates the control-plane JSON Schemas as Draft 2020-12, validates `references/examples/problem-closure.example.json`, runs the deterministic closure checker, renders its Markdown human projection, and asserts that the projection still declares machine JSON as authority.

No required control uses an `if file exists` skip. A green result therefore cannot be green merely because an owning control was absent.

The shared suite intentionally does **not**:

```text
pass --execute to run_codex_sdk_worker.py
pass --apply to github_issue_dag_projection.py
require a Herdr binary or observe a real process
claim a real article/PDF/provider closure
merge/release/promote anything
```

Therefore a green suite proves deterministic integration on the exact checked subject, not live provider/runtime closure and not Human admission.

## Existing authority controls

`dual-agent-offload-contract/verify.sh` is the executable authority over the portable local/cloud offload method: it freezes the method vocabulary, validates its schemas/positive fixtures, asserts that the method document still names every executable control, and requires its semantic mutations to turn red.

Real-task control ownership:

- `real_task_ab.py` freezes the old monolith, refactor-as-landed, reachability repair, and causal-DAG repair; it compiles the matched task/capability contracts and reports the closed-loop stage states.
- `real_task_fixture.py` owns the immutable contract/oracles, deterministic Worker carrier, true-dependency and tournament-lease controls, and exact frozen treatment identities.
- `real_task_runtime.py` creates real linked worktrees and subprocess Workers, proves path-disjoint overlap, checkpoint/resume, candidate comparison, global-objective veto, correct convergence ancestry, and residue cleanup.
- `real_task_scheduler.py` projects actual observations into the canonical scheduler lifecycle contract and requires planted active-writer, stale-result, retry-lineage, and fixture-to-PASS mutations to fail.

`run-all.sh` also runs `../scripts/run_behavioral_ab.py --selftest`. The selftest never invokes a model; a live model run is a separate explicitly-argumented evidence lane.

## Evidence and cleanup law

The suite is offline and zero-network. It does not activate provider/model, GitHub Issue mutation, Herdr, Git Town, Forgejo, publication, merge, release, or production authority. Temporary repositories, worktrees, branches, processes, receipts and generated projections must be removed at close. A test PASS may raise only the evidence lane it actually exercised.

## Wave 3 live-evidence denominator — #464–#468

Wave 3 retains its original admitted controls and may add post-admission falsifiers without rewriting the historical admission record. Current executable denominator:

| Test | Positive denominator | Mutation denominator | Live lane |
|---|---:|---:|---|
| `codex_live_acceptance_selftest.py` | 1 | 26 | `LIVE_EXECUTION_OBSERVED / SHADOW_READBACK_PARTIAL`; fresh v2 run required |
| `codex_result_carrier_selftest.py` | 2 | 13 | `NOT_EXERCISED`; deterministic carrier mechanics only |
| `codex_worker_result_selftest.py` | 2 | 22 | `NOT_EXERCISED`; shape/binding/offline replay only |
| `github_issue_dag_live_canary_selftest.py` | 1 | 10 | remote canary already achieved separately; selftest remains deterministic |
| `herdr_lifecycle_selftest.py` | 2 | 7 | `NOT_EXERCISED` |
| `source_claim_compiler_selftest.py` | 4 source kinds | 11 | `EVIDENCE_DEPENDENT` |

The four #505 Codex acceptance mutations are specifically central-claim falsifiers:

```text
worker/controller agree on unchanged pre-turn tree while claiming a changed path → FAIL
bound result tree contains an undeclared extra path                           → FAIL
syntactically valid but absent result tree object                            → FAIL
base_sha and declared base_tree_sha disagree                                 → FAIL
```

The positive path uses a real temporary Git repository and an immutable result tree. This remains zero-provider: it does not invoke Codex. `run_codex_sdk_worker.py` separately proves that the producer can create the same kind of detached tree using a private index without staging the normal index.

The #508 controls add durability and executable provenance on top. `codex_v2_fixture.py` builds one real throwaway repository, materializes the post-turn tree, and publishes the durable carrier; the carrier and live-acceptance selftests then **delete the originating repository** before any replay or acceptance work happens, so a green result cannot come from the originating object store. Their planted controls are:

```text
result tree existed at execution time but was never carried            → FAIL
syntactically valid tree SHA absent from the bundle                    → FAIL
manifest names the wrong tree / evidence commit / refs / repository    → FAIL
hidden extra path omitted from the replayed denominator                → FAIL
bundle bytes or digest drift from the manifest                         → FAIL
adapter blob or codex binary digest differs from the bound receipt     → FAIL
PATH codex claimed while the SDK-bundled executable was used, or vice versa → FAIL
unschematized worker field, or missing required executor provenance    → FAIL
historical v1 worker result promoted into the v2 replay path           → FAIL
```

The shape denominator is now twelve Draft-2020-12 control-plane schemas: historical `codex-live-acceptance-receipt.schema.json` v1 is retained, `codex-live-acceptance-receipt-v2.schema.json` now also requires `result_tree_replay=PASS` plus carrier/executor identity, and `codex-worker-result-v2.schema.json` owns the strict worker-result shape the acceptance binder consumes.

These are deterministic mechanics. A green fixture or selftest is never live #464 completion, and merge remains separate repository authority.

`references/wave3-live-handoff-queue.json` remains the immutable fork-time continuation packet; its historical v1 receipt route is not current mutable evidence authority. A fresh #464 runtime attempt must be rebound to current code/contracts rather than laundering the old queue state.

Wave-3 controls intentionally do **not** call `--execute` on Codex or the GitHub canary and do not require Herdr. A test may contain expected output vocabulary such as `EXERCISED` only as deterministic fixture input; such fixture bytes never establish a live receipt. Hosted PASS proves the exact static carrier/checker subject only.
