# Tests

`run-all.sh` executes every nested `verify.sh`.

The universal-entry suite proves:

- the Skill entrypoint is a pre-implementation Constraint-First compiler;
- A/B/C/D complexity classes exist;
- Level C/D work cannot silently degrade into Level A implementation behavior;
- the copyable System Prompt exposes the canonical `System Prompt → source intent → Constraint Compiler → {Domain module, Unknown probes, Hard laws} → Executable Spec → Implementation → Harness/Evals` topology;
- domain modules extend rather than replace the universal method;
- the required output contract reaches the Implementation Gate before the Implementation Plan;
- planted regressions can remove the anti-degradation or domain-extension law and be detected by the control.

The system-contract suite proves:

- a complete prototype contract is admitted;
- an invariant with no oracle is refused;
- a required capability cannot be `NOT_EXERCISED` under `READY_FOR_IMPLEMENTATION`;
- teardown cannot be absent or reference an unknown transition;
- a performance claim cannot exist without a percentile/load/environment-bound measurement budget;
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

The procedural-grounding suite proves:

- a critical execution procedure cannot pass through mention or planning alone;
- a required negative control must execute and show the expected red observation;
- Skill-specific/unknown critical procedures require satisfied assertion/probe obligations;
- unreviewed sources, scripts, dynamic context, or license state cannot feed an injected critical capsule;
- fork count/depth/token/no-progress and capsule-token budgets fail closed;
- only actionable capsule payloads are admitted; raw reasoning traces are rejected;
- injected capsules must be grounded, faithful, runtime-relevant, fresh, and authority-compatible;
- exact-subject observations and weighted coverage are recomputed rather than trusted from model prose;
- an `UNKNOWN` runtime, Human/external proof, or unexecuted four-condition attribution cannot become receipt-level runtime truth.

These controls validate method contracts. They do not exercise external Skill
search, live model/context forks, browser/device observers, external providers,
Linux privilege, KVM, cgroups, seccomp, hardware, chaos/exploit paths, a live
Forgejo mutation, a GitHub Actions repair incident, or a ChatGPT Desktop session.
