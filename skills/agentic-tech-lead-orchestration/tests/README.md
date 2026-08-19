# Test controls

`run-all.sh` is the shared deterministic convergence entrypoint. It executes the positive examples and independent mutation cases for provider role/subject separation, active code-graph-rag rejection, path leases, DAG cycles, Git Town admission, semantic-conflict blocking, evidence ceilings, Human Admit, scheduler lifecycle, the matched real-task A/B, and the Codex control-plane adapters/closure contracts.

## Codex control-plane denominator — #375–#378

The convergence suite executes four required selftests unconditionally. Current frozen denominator for this convergence candidate:

| Test | Positive denominator | Mutation denominator | Live lane |
|---|---:|---:|---|
| `codex_sdk_controller_selftest.py` | 4 | 14 | `NOT_EXERCISED` |
| `github_issue_dag_selftest.py` | 6 | 17 | `NOT_EXERCISED` |
| `herdr_observer_selftest.py` | 4 | 18 | `NOT_EXERCISED` |
| `problem_closure_selftest.py` | 6 | 22 | `EVIDENCE_DEPENDENT` |

The Codex denominator includes exact 40-hex subject checks, clean-worktree preflight, ancestor/descendant lease conflict, repository-path escape refusal, and post-turn changed-file readback that rejects read-only/out-of-lease mutations. The GitHub-DAG denominator includes repository visibility/default-branch binding, expected issue state, closing-PR reference ownership checks, graph/readback drift and destructive extra-edge refusal. Generic development-link ownership beyond the closing-reference surface remains a separate residual; the deterministic test does not claim broader GitHub linkage semantics than it exercises.

The Herdr denominator binds exact Git subjects, worktree/pane/workspace/PID/native-session identity, PID start time, bounded observation freshness, nonterminal process liveness and terminal cleanup/residue before `DONE_CANDIDATE`. The problem-closure denominator binds a frozen source manifest and complete problem ID set, exact 40-hex repo subjects, portable worktree identity, current/historical implementation evidence, exact-subject verification receipts, supersession targets/cycles, residual gaps and deterministic Markdown projection.

The suite also validates six control-plane JSON Schemas as Draft 2020-12, validates `references/examples/problem-closure.example.json`, runs the deterministic closure checker, renders its Markdown human projection, and asserts that the projection still declares machine JSON as authority.

No required control uses an `if file exists` skip. The #379 convergence subject contains the exact selected sibling bytes first, then executes the shared gate. This keeps a green result from being green merely because a sibling file was absent.

The shared suite intentionally does **not**:

```text
pass --execute to run_codex_sdk_worker.py
pass --apply to github_issue_dag_projection.py
require a Herdr binary or observe a real process
claim a real article/PDF/provider closure
merge/release/promote anything
```

Therefore a green suite proves deterministic integration on the exact checked subject, not live provider/runtime closure and not Human admission of the unmerged sibling candidates.

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
