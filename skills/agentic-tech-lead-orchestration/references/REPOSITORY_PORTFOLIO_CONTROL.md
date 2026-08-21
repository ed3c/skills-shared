# Repository Portfolio Control

Contract family: `repository-portfolio-control/v1`  
Owner: `agentic-tech-lead-orchestration`  
Tracking issue: `#560`

## Purpose

This contract extends the existing Tech Lead from one bounded task DAG to one fixed repository-portfolio epoch. It composes existing task, Shadow, Git Town, GitHub delivery, bootstrap, and Issue closure authorities. It does not replace them.

Mandatory coordinator instruction:

```text
Use subagents. Wait for all agents and consolidate their findings.
```

## Authority split

```text
Tech Lead controller
  acceptance compilation, G1-G7 graph construction, ready waves,
  dispatch, join, convergence, Local Handoff

Shadow Architect
  read-only drift, contradiction, authority and evidence-ceiling review

Git Town / Git
  real branches, ancestry, worktrees and path leases

GitHub delivery
  provider snapshot, Draft publication, exact-head hosted evidence

Issue Closure Contract
  landed implementation, residual owner and closure disposition

Human / repository policy
  semantic conflict, merge, release, production, rollback and visibility
```

Markdown is navigation and law projection. JSON packets, deterministic checkers, Git objects, workflow receipts, provider readback, and Human admission remain execution authorities.

## State machine

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

- G1, G2, and G3 are directed acyclic graphs.
- G4 and G5 are canonical undirected conflict pairs.
- G6 cannot contain an authority-widening edge.
- G7 cannot place merge or close before exact-head acceptance.
- Every edge binds a typed reason and immutable subject digest.
- `TRUE_CHILD` requires named consumption of unmerged parent bytes/contracts.
- Path disjointness does not erase a semantic completion dependency.
- Unknown writer/resource scope conflicts with every active writer/resource owner.
- A node with multiple completion parents has exactly one convergence owner.

A ready wave is valid only when all G1 start prerequisites are met, G2 completion obligations required for entry are admitted, G3 ancestry is truthful, G4/G5 leases are disjoint, G6 authority is sufficient, and G7 publication is not prematurely advanced.

## Subagent join law

Dispatch and result packets are content-bound. Required agent roles are selected explicitly per task. A valid join receipt proves:

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

Aliases such as Fable, Opus, or Sonnet are routing policy only. Before dispatch, bind provider, carrier, exact model/version, configuration, reasoning effort, sandbox, approval policy, egress policy, and availability. An unresolved alias is `ABSENT`; an installed binary is `AVAILABLE`, not `EXERCISED`.

Private repository material remains local or inside an explicitly admitted provider boundary. Public packets never contain private URLs, paths, source content, credentials, or secret-shaped values.

## One-shot CI law

A candidate earns hosted evidence only after local convergence and an all-agent join:

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

## Current C0 implementation ceiling

C0 provides portable contracts, schemas, role templates, deterministic checkers, fixtures, a dedicated hosted gate, and the canonical prompt. C0 may prove the static/deterministic control surface on one exact repository subject.

C0 does not prove:

```text
live Codex CLI subagents
continuous independent Shadow runtime
private-repository egress admission
real multi-repository implementation waves
one-shot CI until the exact workflow runs
merge, release or production
new-repository bootstrap consumer canary
```

Those remain `NOT_EXERCISED`, `BLOCKED`, or `HUMAN_ADMIT_REQUIRED` until their own receipts exist.
