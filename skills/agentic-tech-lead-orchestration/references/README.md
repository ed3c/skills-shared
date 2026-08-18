# Reusable contracts

These files are host-neutral and consumer-independent.

- `task-contract.schema.json` closes the portable task packet shape.
- `example-stack-contract.json` is a positive offline fixture, not a live provider receipt.
- `local-handoff-queue.schema.json` defines the zero-context continuation queue used only after a real host/runtime boundary is reached.
- `example-local-handoff-queue.json` is a generic positive fixture for entry → runtime lane → receipt → exit → next routing; its commands and task IDs are examples only.
- `scheduler-lifecycle.schema.json` defines scheduler/process-worktree lifecycle evidence.
- `fanout-prompt.md` is the standard Worker prompt envelope for Stack and Tournament modes.
- `REPOSITORY_CLOSURE_RECONCILIATION.md` explains the repository-wide completion review: tree inventory versus documented status, the real-problem closure matrix, evidence kinds and lanes, and the two Issue edge classes.
- `repository-closure-contract.schema.json` closes the tree-inventory/closure-matrix shape; `example-repository-closure-contract.json` is a generic positive fixture, not a consumer readback.
- `issue-dual-dag.schema.json` separates start dependencies from completion dependencies inside one Issue graph; `example-issue-dual-dag.json` is its generic positive fixture.
- [`dual-agent-offload/`](dual-agent-offload/README.md) holds the portable local/cloud offload method. [`dual-agent-offload/OFFLOAD_METHOD.md`](dual-agent-offload/OFFLOAD_METHOD.md) is the prose law — state machine, authority roles, idempotency, evidence lanes and the plane boundary; the two schemas beside it are the shape gates and `tests/dual-agent-offload-contract/verify.py` is the only executable authority over their semantics. The five runtime wire schemas are declared there and owned by the Runtime Contract Plane repository, never defined here.

Consumer repositories bind real commit/tree identities, issue/task references, path leases, commands, provider versions, indexes, budgets, branches, runtime capabilities, receipts, and Human admissions outside this shared directory. They consume these contracts without copying the shared `SKILL.md` body.
