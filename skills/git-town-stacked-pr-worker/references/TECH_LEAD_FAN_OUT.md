# Tech Lead fan-out

One supervising Agent driving one branch is a serial machine wearing a parallel
name. This reference turns that supervisor into a bounded Tech Lead: the
Planner owns the contract, the architecture, the branch graph, the context
subject, the budgets and the acceptance oracles; a Worker owns one leased
implementation surface and nothing else.

The contract is checked before a branch exists.
[`scripts/check_fanout_contract.py`](../scripts/check_fanout_contract.py) reads
one file shaped by
[`FAN_OUT_CONTRACT.schema.json`](FAN_OUT_CONTRACT.schema.json) and exits `2`
with a named refusal, `0` on pass, `64` on unusable input, `70` on its own
defect. It creates no branch, worktree, Agent or provider session.

## The four modes

```text
TOURNAMENT    one bounded task, several differentiated strategies, one admitted winner
COOPERATIVE   path-disjoint sibling tasks, one convergence owner
SERIAL_STACK  a real parent-child edge on unmerged bytes or contracts
HYBRID        cooperative layers with a bounded tournament inside one leaf
```

Choosing between them is not a style question. It is a question about what the
work actually depends on:

```text
Do two tasks write the same file?
  yes → same Worker, or serialize them. Not siblings.
Does B need bytes or a contract A has not merged yet?
  yes → SERIAL_STACK, and B must name what it consumes.
Is the task one problem with several plausible shapes?
  yes → TOURNAMENT, and every competitor gets the same base and context.
Otherwise → COOPERATIVE.
```

## What the checker refuses, and why each one matters

| Code | Refused shape |
|---|---|
| `MUTABLE_BASE` | The base is not one immutable commit and tree. Two competitors that both passed were never compared; they answered different questions. |
| `CONTEXT_DIGEST_MISMATCH` | A competitor was given a different context bundle. Same reason: the tournament measured the context, not the strategy. |
| `MISSING_BRANCH_FOCUS` | A competitor declares no focus, or repeats another's. Competitors without differentiated strategies are repeats, and repeats measure sampling noise. |
| `PATH_OVERLAP` | Two concurrent Workers lease the same path. Competitors are the one exception, because at most one of them is ever admitted. |
| `UNDECLARED_DEPENDENCY` | A child branch names a parent but no consumed contract or path, a sibling depends on a sibling, or the graph has a cycle. Stacking is not a dependency. |
| `ACCEPTANCE_TEST_MUTATED` | A writable lease reaches an immutable acceptance path. A competitor that can edit its own oracle has moved the test, not passed it. |
| `WORKER_BUDGET_OVERFLOW` | More Workers than admitted, or a per-Worker token request over budget. |
| `QUALITATIVE_BEFORE_HARD_GATE` | Qualitative review ranks before the deterministic gates. Taste applied to code that does not pass is taste applied to nothing. |
| `CHERRY_PICK_ACROSS_COMPETITORS` | Parts of two competitors combined without a Human decision. Competitors implement incompatible architectures; the seam between them is exactly the semantic conflict a Human owns. |
| `CONVERGENCE_OWNER_AMBIGUOUS` | No owner, an owner that is not a Worker, or two Workers claiming the role. |
| `PREMATURE_CONVERGENCE` | A convergence Worker converges an input it does not depend on, so it can start before that input has an admitted subject. |
| `AUTOMATIC_SEMANTIC_RESOLUTION` | The plan grants itself winner admission or semantic-conflict resolution, or drops one of the Human-owned operations. |
| `FORBIDDEN_CONTEXT_PROVIDER` | Code-Graph-RAG declared a required context provider. Non-required historical residue still validates; the rule bans the dependency, not the name. |
| `CONTEXT_FUNNEL_STATE_LAUNDERED` | The compiler-truth funnel reports `PASS` with no evidence, or an unexercised state carrying run evidence. A funnel that did not run stays `NOT_EXERCISED`. |

## Budgets and circuit breakers

Every fan-out declares `max_workers`, `max_tokens_per_worker`,
`max_wall_clock_seconds`, `max_retries_per_worker`, and at least one circuit
breaker in prose that names the condition that stops the run. A budget with no
breaker is a number nobody enforces; a breaker with no budget is a sentence.

## Evidence boundary

A `FAN-OUT CONTRACT PASS` line means one thing: the plan is internally
consistent and refuses the shapes above. It does not mean a branch exists, a
worktree was created, an Agent ran, Git Town synchronized, a provider was
invoked, tokens were spent well, or that multiple Agents were cheaper or better
than one. Those are separate evidence lanes with their own receipts.

Controls: [`tests/fan-out-contract/verify.sh`](../tests/fan-out-contract/verify.sh).

## Human-owned operations

Winner admission, semantic conflict resolution, merge or ship, release
promotion, permission widening and destructive rollback. The contract must
declare the first four explicitly; the checker refuses a plan that omits any of
them.
