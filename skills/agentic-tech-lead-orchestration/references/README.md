# Reusable contracts

These files are host-neutral and consumer-independent.

- `task-contract.schema.json` closes the portable task packet shape.
- `example-stack-contract.json` is a positive offline fixture, not a live provider receipt.
- `local-handoff-queue.schema.json` defines the zero-context continuation queue used only after a real host/runtime boundary is reached.
- `example-local-handoff-queue.json` is a generic positive fixture for entry → runtime lane → receipt → exit → next routing; its commands and task IDs are examples only.
- `scheduler-lifecycle.schema.json` defines scheduler/process-worktree lifecycle evidence.
- `fanout-prompt.md` is the standard Worker prompt envelope for Stack and Tournament modes.

Consumer repositories bind real commit/tree identities, issue/task references, path leases, commands, provider versions, indexes, budgets, branches, runtime capabilities, receipts, and Human admissions outside this shared directory. They consume these contracts without copying the shared `SKILL.md` body.
