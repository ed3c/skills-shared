# Tech Lead + Shadow Architect Closure Route

This document defines the portable closure-audit relationship between
`agentic-tech-lead-orchestration`, `procedural-shadow-runtime`, and
`git-town-stacked-pr-worker`.

It is method documentation. It is not a consumer queue, runtime receipt, Git
branch authority, merge decision, Human approval, release, or rollback.

## Read order

1. repository `AGENTS.md`
2. `skills/agentic-tech-lead-orchestration/README.md`
3. `skills/procedural-shadow-runtime/README.md`
4. `skills/git-town-stacked-pr-worker/README.md`
5. the consumer's nearest `AGENTS.md` and `README.md`
6. the consumer's machine queue, Stack index, issue/PR metadata and receipts

A dated external snapshot in this document is navigation evidence only. Refresh
consumer state from the consumer repository before executing or claiming
completion.

## Closure State Machine

```text
SOURCE_PROPOSAL
→ METHOD_IMPLEMENTED
→ CONSUMER_MECHANISM_IMPLEMENTED
→ DETERMINISTIC_EVIDENCE_VERIFIED
→ LIVE_OR_PHYSICAL_EVIDENCE_VERIFIED
→ HUMAN_ADMITTED
→ RELEASED
```

A later state needs its own evidence. These substitutions are forbidden:

```text
merged PR                 != live physical execution
static fixture PASS       != provider/model/runtime PASS
Tech Lead local PASS      != global objective PASS
Shadow agreement          != deterministic authority
workflow green            != Human Admit
source proposal           != official standard or repository truth
process dependency        != Git child ancestry
external evidence         != consumer Stack writer
```

## Role ownership

### Tech Lead

Owns:

```text
problem and capability decomposition
interface/output/test freeze
task DAG and true dependency edges
writer, branch/worktree, path and resource leases
Worker admission and bounded retry budgets
one convergence owner
Local Handoff Queue when the current runtime cannot execute the next proof
```

Must not:

```text
self-certify the global objective
proxy live evidence with fixture evidence
guess a semantic conflict
widen provider, merge, release or rollback authority
```

### Independent Shadow Architect

Owns:

```text
requirement applicability review
source/document/contract/runtime contradiction detection
global objective versus local task review
evidence ceiling and false-promotion review
missing owner/issue/eval/receipt discovery
cleanup, rollback and denominator review
```

Must not:

```text
become a second state writer
silently edit the Builder branch
reuse the Builder's conclusion as independent evidence
turn static or deterministic PASS into live PASS
turn agreement into Human Admit
persist private chain of thought
```

The Shadow uses the same immutable subject and a separate evaluation path. The
Shadow emits findings and a verdict. The Tech Lead owns the change plan and
convergence.

## Directory → State Machine → data flow

| Surface | State Machine | Input | Output | Evidence ceiling |
|---|---|---|---|---|
| `agentic-tech-lead-orchestration` | `REQUEST → CONTRACT → CAPABILITY DAG → TASK DAG → WORKERS → ATTEMPTS → CONVERGENCE → GLOBAL OBJECTIVE → HANDOFF` | issue/PRD/PDF, exact source, budgets, interfaces | task packets, leases, receipts, Local Handoff Queue | deterministic/hermetic until live run |
| `procedural-shadow-runtime` | `OBSERVE PLAN → APPLICABILITY → PRE-SIDE-EFFECT GATE → EXECUTION READBACK → CONTRADICTION/GLOBAL OBJECTIVE → HOLD/REJECT/HUMAN-ELIGIBLE` | same exact subject, public plan/actions, assertions, evidence | independent Shadow receipt and findings | declared evaluator/runtime subject |
| `git-town-stacked-pr-worker` | `ISSUE CONTRACT → LEASE → BRANCH/WORKTREE → LOCAL EVALS → BOUNDED NO-PUSH SYNC → PUBLICATION → HUMAN MERGE` | true branch DAG, path/resource leases, exact executable/config | Stack receipts and publication handoff | no live Git Town claim without run |
| consumer repository | consumer-owned State Machines | immutable shared method release + repository profile | exact queue, Stack index, CI, live receipts | consumer authority only |

## DAG relation vocabulary

```text
SIBLING
  path-disjoint work; no unmerged byte dependency

TRUE_CHILD
  consumes named unmerged parent contract/code/proof/document bytes

CONVERGENCE
  one owner integrates admitted prerequisites and shared indexes

PROCESS_DEPENDENCY
  must occur earlier, but does not change Git ancestry

EXTERNAL_EVIDENCE
  independent receipt lane; owns no implementation paths

HISTORICAL
  admitted or forensic prior subject; not current mutable state authority
```

Queue order, issue numbers, or review chronology do not create a true child.

## End-to-end closure flow

```text
article / PDF / issue / observed repository state
        ↓ classify source proposal versus current fact
Tech Lead compiles problem/capability/task DAG and leases
        ↓
Shadow independently checks applicability, contradictions and ceilings
        ↓
small implementation siblings / true children / independent evidence lanes
        ↓
deterministic positive + hollow/mutation controls
        ↓
convergence owner asserts local and global objectives
        ↓
current runtime can execute?
  ├─ yes → live/physical receipt
  └─ no  → asserted Local Handoff Queue
             ↓ local/runtime owner executes exact commands
             ↓ receipt + cleanup + next immutable queue epoch
        ↓
Human Admit where required
        ↓
merge / release / rollback authority
```

## External consumer snapshot — Bettor order 13

Observed: `2026-08-17`. This is `EXTERNAL_CONSUMER_SNAPSHOT`, not Bettor state
authority. Read `ed3c/bettor-arena` issues, PRs, machine queue and current exact
GitHub/local/Forgejo subjects before acting.

Merged implementation/governance subjects:

```text
PR #81   Git Town/document governance foundation (merged historical)
PR #153  Blindspots SQLite evidence ledger
PR #155  exact-subject context funnel
PR #156  Parallel Agent Tech Lead planner
PR #157  Code-Graph-RAG retirement
PR #158  deterministic convergence; no queue advancement
PR #159  physical-run readiness only
PR #169  Local Handoff queue contract; not execution
PR #154  consumer Tech Lead adoption; not a physical Worker run
```

Active process/evidence DAG:

```text
#172 dual-origin reconciliation
→ newly frozen exact subject
→ #161 runtime-env rebind and scheduler/process-worktree canary
→ #146 physical Tech Lead + independent Shadow run
→ #140 Human terminal admission and typed queue transition
→ #68 final convergence/release/rollback
```

Independent path-disjoint control defects:

```text
#173 closure monitor and one Local Handoff authority (PR #176 candidate)
#174 workflow-lock receipt-status laundering
#175 origin-projection freshness
```

Unclosed evidence remains explicit:

```text
local/Forgejo/GitHub reconciliation  NOT_EXERCISED / ACTIVE #172
runtime rebind/canary                BLOCKED_BY_PREDECESSOR
physical Tech Lead/Shadow run        NOT_EXERCISED
Git Town executable/no-push run      NOT_EXERCISED
live Codex/Claude carriers           NOT_EXERCISED
production TN/TV termbase            ABSENT
confidential external canary         NOT_EXERCISED
Human order-13 admission             HUMAN_ADMIT_REQUIRED
release/rollback                     BLOCKED
```

## Consumer adoption rules

A consumer must own:

```text
nearest AGENTS/README route
one machine queue authority
one machine Stack index authority
exact repository/commit/tree and rollback identity
writer/path/resource leases
host/runtime command contracts
positive/control/mutation tests
exact-head workflow and receipt
Human-owned semantic/merge/release boundaries
```

Do not copy consumer branches, paths, credentials, live receipts or mutable state
into a shared `SKILL.md`. A consumer snapshot must name its date, source and
evidence ceiling.
