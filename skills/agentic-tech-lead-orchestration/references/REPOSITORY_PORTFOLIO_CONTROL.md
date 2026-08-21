# Repository Portfolio Control

Tracking: `ed3c/skills-shared#560`  
Contract ID: `agentic-tech-lead/repository-portfolio-control/v1`

This composition adds a portfolio-level join protocol to the existing Tech Lead,
Shadow, GitHub delivery, Git Town, Issue Closure, and shared bootstrap authorities.
It does not create another authority.

## Mandatory coordinator law

```text
Use subagents. Wait for all agents and consolidate their findings.
```

## State Machine

```text
REQUEST_BOUND
→ RUNTIME_AND_AUTHORITY_ADMITTED
→ REPOSITORY_SET_FROZEN
→ SNAPSHOT_EPOCH_BOUND
→ ISSUE_PR_DENOMINATOR_COMPLETE
→ ACCEPTANCE_CONTRACTS_COMPILED
→ ADVERSARIAL_DRIFT_AUDITED
→ G1_G7_ASSERTED
→ READY_WAVES_COMPUTED
→ SUBAGENTS_DISPATCHED
→ ALL_REQUIRED_AGENTS_TERMINAL
→ RESULTS_SCHEMA_VALIDATED
→ FINDINGS_CONSOLIDATED
→ LOCAL_WORKTREES_EXECUTED
→ EXACT_HEAD_LOCAL_GATES_PASS
→ DRAFT_PUBLICATION
→ ONE_SHOT_CI_EPOCH
→ READY_FOR_HUMAN_ADMIT | HOLD | REJECT
→ MERGE_IN_TRUE_DEPENDENCY_ORDER
→ EXACT_MAIN_READBACK
→ ISSUE_CLOSURE_RECONCILED
→ PORTFOLIO_EPOCH_CLOSED
```

## Seven graphs

| Graph | Meaning | Key refusal |
|---|---|---|
| G1 | start dependencies | start edge used as completion proof |
| G2 | completion dependencies | prerequisite lacks admitted receipt |
| G3 | Git ancestry / Stack | TRUE_CHILD lacks consumed unmerged bytes |
| G4 | path writer conflicts | overlapping writers in one ready wave |
| G5 | resource/runtime contention | shared exclusive resource dispatched in parallel |
| G6 | evidence and authority | cheaper evidence lane substitutes for stronger lane |
| G7 | publication, merge and closure | merge/Issue state substitutes for acceptance |

## Data flow

```text
trusted repository/GitHub readback
→ repository-portfolio-snapshot
→ issue-pr-acceptance records
→ portfolio-multigraph
→ ready waves
→ subagent dispatches
→ terminal results
→ subagent join receipt
→ exact-head local verification
→ one-shot CI epoch
→ Human/repository admission
→ exact-main readback
→ existing Issue Closure Contract
```

## Authority split

```text
Tech Lead       planning, G1–G7, leases, ready waves, join gate, convergence
Shadow          read-only drift and false-promotion findings
Codex subagents bounded exploration/review/implementation under inherited sandbox
GitHub delivery exact provider snapshot and hosted execution evidence
Git Town        real worktree/branch ancestry and synchronization
Issue Closure   landed implementation and residual/successor disposition
Human/repo      semantic conflict, merge, release, permissions, production, rollback
```

## Evidence ceiling

The prompt pack, schemas, checkers, fixtures, and deterministic tests prove only the
portable control mechanism for exact fixture subjects. They do not prove a live Codex
subagent run, local worktree execution, private-repository egress, hosted CI, merge,
release, new-repository bootstrap, or production behavior.
