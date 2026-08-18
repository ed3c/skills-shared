# Test controls

`run-all.sh` executes the positive examples and independent mutation cases for provider role/subject separation, active code-graph-rag rejection, no-double-graph, path leases, DAG cycles, Git Town admission, semantic-conflict blocking, evidence ceilings, Human Admit, scheduler lifecycle, and the matched real-task A/B.

`dual-agent-offload-contract/verify.sh` is the only executable authority over the portable local/cloud offload method: it freezes the vocabulary in [`../references/dual-agent-offload/OFFLOAD_METHOD.md`](../references/dual-agent-offload/OFFLOAD_METHOD.md), validates the two schemas and four positive fixtures, asserts that the method document still names every executable control, and requires all sixteen semantic controls to turn red on a mutant that stays schema-valid.

Real-task control ownership:

- `real_task_ab.py` freezes the old monolith, refactor-as-landed, reachability repair, and causal-DAG repair; it compiles the matched task/capability contracts and reports the PDF-derived closed-loop stage states.
- `real_task_fixture.py` owns the immutable contract/oracles, deterministic Worker carrier, true-dependency and tournament-lease controls, and exact frozen treatment identities.
- `real_task_runtime.py` creates real linked worktrees and subprocess Workers, proves path-disjoint overlap, checkpoint/resume, candidate comparison, global-objective veto, correct convergence ancestry, and residue cleanup.
- `real_task_scheduler.py` projects actual observations into the canonical scheduler lifecycle contract and requires planted active-writer, stale-result, retry-lineage, and fixture-to-PASS mutations to fail.

`run-all.sh` also runs `../scripts/run_behavioral_ab.py --selftest`. That script is the only one in this Skill that can spend tokens, and its selftest is the cheap surface that proves it discriminates before it is ever pointed at a host: it builds its own throwaway subject, scores two clean packets, and requires every planted rubric defect to turn its own check red. The selftest never invokes a model; the live run is a separate, explicitly-argumented invocation whose receipts land in `../evals/`.

The suite is offline and zero-network. It does not activate provider/model, Git Town, Forgejo, publication, merge, or production authority. Temporary repositories, worktrees, branches, processes, and receipts must be removed at close.
