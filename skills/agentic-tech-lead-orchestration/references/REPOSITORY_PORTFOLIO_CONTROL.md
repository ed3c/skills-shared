# Repository Portfolio Control

Tracking: `ed3c/skills-shared#560`, core landed under `#566`
Contract family: `repository-portfolio-control/v1`
Owner: `agentic-tech-lead-orchestration`

This contract extends the existing Tech Lead from one bounded task DAG to one fixed
repository-portfolio epoch. It composes existing task, Shadow, Git Town, GitHub
delivery, bootstrap, Issue closure, and `github-portfolio-control` (`ghpc`)
authorities. It does not replace them, and it does not create a second authority for
anything `ghpc` already owns -- see the authority table below.

Mandatory coordinator instruction:

```text
Use subagents. Wait for all agents and consolidate their findings.
```

## Authority split

```text
Tech Lead controller
  acceptance compilation, G1-G7 graph construction, ready waves,
  dispatch, join composition, convergence

Shadow Architect
  read-only drift, contradiction, authority and evidence-ceiling review

Git Town / Git
  real branches, ancestry, worktrees and path leases

GitHub delivery
  provider snapshot, Draft publication, exact-head hosted evidence

Issue Closure Contract
  landed implementation and residual disposition

github-portfolio-control (ghpc)
  one-shot hosted CI epoch, all-subagent join barrier, epoch subject,
  and composed-authority routing -- see the table below

Human / repository policy
  semantic conflict, merge, release, permissions, production, rollback
```

## Authority routing to ghpc

`skills/agentic-tech-lead-orchestration` composes these `ghpc` contracts by `$id`
rather than restating their shape or their checkers. This skill does not ship a
one-shot-CI checker, a subagent-join schema/checker, or a second contracts root:

| Concern | Owning `$id` | Owning module | This skill's role |
|---|---|---|---|
| One-shot hosted CI epoch | `ghpc/one-shot-ci-epoch/v1` | `skills/github-portfolio-control/references/schemas/one-shot-ci-epoch.schema.json` | reads the verdict; `release-auditor` reconciles against it, never re-derives it |
| All-subagent join barrier | `ghpc/subagent-join/v1` | `skills/github-portfolio-control/references/schemas/subagent-join.schema.json` | `consolidation-verifier` composes it for the denominator check; the join receipt shape itself lives in `ghpc` |
| Epoch subject `{main_commit, tree}` | `ghpc/portfolio-epoch/v1` | `skills/github-portfolio-control/references/schemas/portfolio-epoch.schema.json` | `portfolio-multigraph/v1.epoch_subject` (this skill, #566 mandatory fix 6) is populated from the same `{main_commit, tree}` shape so the two checkers reconcile on one picture |
| Composed-authority declaration | `ghpc/authority-composition/v1` | `skills/github-portfolio-control/references/schemas/authority-composition.schema.json` | this table is the human-readable projection of that composition; a machine-checked `ghpc/authority-composition/v1` instance is out of #566's C1 scope |

`ghpc`'s own K01-K09 controlled vocabulary
(`skills/github-portfolio-control/references/controlled-vocabulary.md`) is the
independent second-checker layer for the join/CI/epoch concerns above; the
deterministic control names this skill plants (`references/../tests/portfolio-control/selftest.py`)
cover the acceptance/multigraph/dispatch/snapshot layer that composes into it.

## State Machine

```text
REQUEST_BOUND
→ RUNTIME_AND_AUTHORITY_ADMITTED
→ REPOSITORY_SET_FROZEN
→ GITHUB_SNAPSHOT_EPOCH_BOUND
→ ISSUE_PR_DENOMINATOR_COMPLETE
→ ACCEPTANCE_CONTRACTS_COMPILED
→ ADVERSARIAL_DRIFT_AUDITED
→ MULTI_GRAPH_MODEL_ASSERTED
→ READY_WAVES_COMPUTED
→ SUBAGENTS_DISPATCHED
→ ALL_REQUIRED_AGENTS_TERMINAL
→ RESULTS_SCHEMA_VALIDATED
→ FINDINGS_CONSOLIDATED
→ LOCAL_WORKTREES_EXECUTED
→ EXACT_HEAD_LOCAL_GATES_PASS
→ DRAFT_PUBLICATION
→ ONE_SHOT_CI_EPOCH
→ CI_JOBS_STEPS_ARTIFACTS_READ_BACK
→ PR_ACCEPTANCE_RECONCILED
→ READY_FOR_HUMAN_ADMIT
→ MERGE_IN_TRUE_DEPENDENCY_ORDER
→ EXACT_MAIN_READBACK
→ ISSUE_CLOSURE_RECONCILED
→ PORTFOLIO_EPOCH_CLOSED
```

Failure and hold states include:

```text
BLOCKED_BY_MISSING_ACCEPTANCE
BLOCKED_BY_PARENT
BLOCKED_BY_PATH_WRITER
BLOCKED_BY_RUNTIME
BLOCKED_PREDECESSOR
BLOCKED_BY_EXTERNAL_EVIDENCE
BLOCKED_BY_PROVENANCE
JOIN_INCOMPLETE
STALE_EPOCH
REJECTED
SUPERSEDED
HUMAN_ADMIT_REQUIRED
```

Only affected nodes and descendants rewind after subject movement.

## Seven graph laws

```text
G1 start dependency
G2 completion dependency
G3 Git ancestry / Stack
G4 changed-path writer conflict
G5 resource/runtime contention
G6 evidence/authority
G7 publication/merge/closure
```

| Graph | Meaning | Key refusal |
|---|---|---|
| G1 | start dependencies | gates DISPATCH only; never promoted to gate COMPLETION (`START_DEPENDENCY_PROMOTED_TO_COMPLETION`) |
| G2 | completion dependencies | gates the node's own COMPLETION edge (recorded on G7), never merged into the G1 dispatch-order predecessor set |
| G3 | Git ancestry / Stack | `TRUE_CHILD` lacks consumed unmerged bytes |
| G4 | path writer conflicts | overlapping writers in one ready wave (glob-suffix leases like `scripts/**` normalize before comparison -- #566 mandatory fix 1) |
| G5 | resource/runtime contention | shared exclusive resource dispatched in parallel |
| G6 | evidence and authority | cheaper evidence lane substitutes for stronger lane |
| G7 | publication, merge and closure | merge/Issue state substitutes for acceptance; owned upstream by `ghpc` for the hosted-CI and join legs |

- G1, G2, and G3 are directed acyclic graphs.
- G4 and G5 are canonical undirected conflict pairs.
- G6 cannot contain an authority-widening edge.
- G7 cannot place merge or close before exact-head acceptance.
- Every edge binds a typed reason and immutable subject digest.
- `TRUE_CHILD` requires named consumption of unmerged parent bytes/contracts.
- Path disjointness does not erase a semantic completion dependency.
- Unknown writer/resource scope conflicts with every active writer/resource owner.
- A node with multiple completion parents has exactly one convergence owner.
- A predecessor stuck `BLOCKED_BY_RUNTIME` fails closed as `BLOCKED_PREDECESSOR`, not
  as a deadlock or cycle (#566 mandatory fix 3).

A ready wave is valid only when all G1 start prerequisites are met, G2 completion obligations required for entry are admitted, G3 ancestry is truthful, G4/G5 leases are disjoint, G6 authority is sufficient, and G7 publication is not prematurely advanced.

## Data flow

```text
trusted repository/GitHub readback
→ repository-portfolio-snapshot (per-source observed_at, max-skew bound)
→ issue-pr-acceptance records (typed start/completion dependency edges)
→ portfolio-multigraph (epoch_subject embedded, G1-only dispatch gating)
→ ready waves
→ subagent dispatches (sandbox_mode bound per role)
→ terminal results
→ ghpc/subagent-join/v1 (composed, not restated)
→ exact-head local verification
→ ghpc/one-shot-ci-epoch/v1 (composed, not restated)
→ Human/repository admission
→ exact-main readback
→ existing Issue Closure Contract
```

## Subagent join law

Dispatch and result packets are content-bound. Required agent roles are selected explicitly per task. A valid join composes `ghpc/subagent-join/v1`'s proof that:

```text
required dispatch denominator == observed result denominator
+ every result terminal
+ every result bound to its dispatch and exact base
+ no missing or duplicate result
+ failed/blocked/cancelled/stale/timeout results retained
+ contradictions and dissent preserved
+ one consolidation digest
```

`PASS` requires an empty missing set and no unresolved blocking contradiction. Agent majority, model confidence, or one green Worker cannot override a deterministic failure or missing auditor.

## Runtime and model identity

Aliases such as Fable, Opus, or Sonnet are routing policy only. Before dispatch, bind provider, carrier, exact model/version, configuration, reasoning effort, sandbox mode, approval policy, egress policy, and availability. An unresolved alias is `ABSENT`; an installed binary is `AVAILABLE`, not `EXERCISED`.

Private repository material remains local or inside an explicitly admitted provider boundary. Public packets never contain private URLs, paths, source content, credentials, or secret-shaped values.

## One-shot CI law

Owned by `ghpc/one-shot-ci-epoch/v1`; this skill composes it after local convergence and an all-agent join:

```text
local exact-head PASS
→ frozen candidate and workflow definitions
→ Draft publication
→ exactly one ready-for-review transition
→ no code push after ready
→ exact-head workflow run
→ non-empty jobs and steps
→ artifacts/logs/readback
```

Blind rerun is forbidden. A rerun is admissible only when a deterministic infrastructure-flake receipt proves source head, workflow, dependencies, and configuration unchanged. A code/test defect starts a new local candidate epoch.

## Merge and closure

A merged PR whose merge commit was never read back exactly from the default branch is
`MERGED_WITHOUT_EXACT_MAIN_READBACK`. A closed Issue or merged PR whose acceptance
contract never resolved is `ISSUE_CLOSED_WITH_UNRESOLVED_ACCEPTANCE`. A branch whose
provenance requirement is red must never be marked merge-ready
(`PROVENANCE_RED_BRANCH_MARKED_MERGE_READY`), regardless of any other green signal.

## Evidence ceiling

The prompt pack, schemas, checkers, fixtures, and deterministic tests prove only the
portable control mechanism for exact fixture subjects. They do not prove a live Codex
subagent run, local worktree execution, private-repository egress, hosted CI, merge,
release, new-repository bootstrap, or production behavior.
