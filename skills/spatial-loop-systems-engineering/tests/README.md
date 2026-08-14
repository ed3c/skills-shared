# Tests

`run-all.sh` executes every nested `verify.sh`.

The system-contract suite proves:

- a complete prototype contract is admitted;
- an invariant with no oracle is refused;
- a required capability cannot be `NOT_EXERCISED` under
  `READY_FOR_IMPLEMENTATION`;
- teardown cannot be absent or reference an unknown transition;
- a performance claim cannot exist without a percentile/load/environment-bound
  measurement budget;
- `PASS` cannot omit evidence;
- state-machine references must close;
- a missing contract file exits 64 rather than being read as a system failure.

The recovery-escalation suite proves the shared prompt/procedure retains:

- three **qualifying** failures on the same target as the escalation trigger;
- refusal of a fourth blind patch in the stale repair context;
- an issue-bound failure packet and fresh diagnosis transition;
- normal Forgejo routing versus the GitHub Actions/GitHub CI exception;
- the new isolated worktree/branch requirement;
- owning-oracle and negative-control PASS before commit/PR eligibility;
- no silent grant of merge authority.

These controls validate the method contract. They do not exercise Linux,
privilege, KVM, cgroups, seccomp, hardware, chaos, exploit paths, a live Forgejo
mutation, a GitHub Actions repair incident, or a ChatGPT Desktop session.
