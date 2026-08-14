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

These controls validate the method contract. They do not exercise Linux,
privilege, KVM, cgroups, seccomp, hardware, chaos, or exploit paths.
