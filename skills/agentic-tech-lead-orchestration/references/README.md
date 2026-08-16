# Reusable contracts

These files are host-neutral and consumer-independent.

- `task-contract.schema.json` closes the portable task packet shape.
- `example-stack-contract.json` is a positive offline fixture, not a live provider receipt.
- `fanout-prompt.md` is the standard Worker prompt envelope for Stack and Tournament modes.

Consumer repositories bind real commit/tree identities, path leases, commands, provider versions, indexes, budgets, branches, and receipts outside this shared directory.
