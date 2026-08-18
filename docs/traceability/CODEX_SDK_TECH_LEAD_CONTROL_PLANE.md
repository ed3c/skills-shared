# Codex SDK Tech Lead Control Plane — Shadow-monitored trace

Status: `PLANNED / DOCUMENTED`, runtime lanes remain `NOT_IMPLEMENTED` or `NOT_EXERCISED` until their owning issues produce exact-subject receipts.

This document records the current integration target introduced by issues #375–#379. It does not replace `agentic-tech-lead-orchestration`, `procedural-shadow-runtime`, `git-town-stacked-pr-worker`, GitHub metadata, runtime-env, or consumer-local receipts.

## Ownership

```text
skills-shared
  portable method, schemas, adapter contracts, eval controls, Agent routes

runtime-env / consumer runtime
  Codex SDK installation/runtime identity, host policy, process/session execution

consumer repository
  issue/PR identities, worktrees, branches, leases, exact commands, provider/session receipts

Human / repository authority
  semantic conflict, merge, release, visibility/access/license/permission widening, rollback
```

## Directory → State Machine responsibility

```text
skills/agentic-tech-lead-orchestration/
├── SKILL.md
│   └── request/contract/capability/task DAG/lease/convergence/handoff laws
├── references/
│   ├── issue-dual-dag.schema.json
│   ├── task/capability/scheduler schemas
│   └── future session/result/problem-closure contracts owned by #375/#378
├── modules/
│   ├── domain-profile.md
│   ├── future codex-sdk-controller.md        #375
│   ├── future github-issue-dag.md            #376
│   └── future herdr-runtime-observer.md      #377
└── scripts/tests/
    └── deterministic admission, readback, mutation and closure gates

docs/traceability/
└── future machine-readable problem closure projection #378

skills/git-town-stacked-pr-worker/
└── molecular branch/PR/Stack ancestry and convergence index #379
```

## Control-plane State Machine

```text
SOURCE / ISSUE / ARTICLE / PDF / PRD
→ REAL_PROBLEM_BOUND
→ SYSTEM_CONTRACT_EXTRACTED
→ TASK_DAG_COMPILED
→ TASK_DAG_ASSERTED
→ GITHUB_DAG_PROJECTED                 #376
→ READY_WAVE_COMPUTED
→ SESSION_PACKET_COMPILED              #375
→ ISOLATED_WORKTREE_BOUND
→ CODEX_SDK_THREAD_STARTED             #375
→ ATTEMPT_EXECUTED
→ STRUCTURED_RESULT_COLLECTED
→ SOURCE / DIFF / TEST READBACK
→ CAPABILITY_RECEIPT_EMITTED
→ HERDR_OBSERVATION_OPTIONAL           #377
→ INDEPENDENT_SHADOW_RECONCILIATION
→ PR / STACK DELIVERY
→ CI / EXACT-HEAD READBACK
→ PROBLEM_CLOSURE_RECOMPUTED           #378
→ NEXT_WAVE | LOCAL_HANDOFF | HUMAN_ADMIT
```

A Herdr terminal `done`, Codex model prose, issue close, PR merge, workflow green, Google/CodexDoc link, or source document cannot skip a state.

## Dual DAG

The controller maintains two edge classes over the same task nodes:

```text
start-readiness
  prerequisite bytes are readable and writer/resource leases are available

completion-readiness
  prerequisite is independently admitted by an exact-subject receipt in the required evidence lane
```

GitHub Issue Dependencies are an external projection of admitted semantic edges. GitHub metadata does not become the semantic DAG authority merely because an edge exists remotely.

```text
portable task/issue dual DAG
        ↓ validated projection
GitHub blockedBy / blocking readback
        ↓
ready-wave computation
        ↓
Codex SDK session dispatch
```

## Parallel work division

```text
#375 Codex SDK controller/session adapter       SIBLING / runtime adapter
#376 GitHub Issue DAG projection               SIBLING / forge projection
#377 Herdr observer                            SIBLING / optional observer
#378 problem-closure ledger                    SIBLING / evidence reconciliation
      ↓ admitted artifacts only
#379 docs/Molecular Stack convergence          CONVERGENCE
```

These issues must not be serialized into a fake Git Stack. A true child may be created only when it consumes named unmerged parent bytes/contracts. Otherwise each implementation starts from the admitted common base and owns disjoint paths/resources.

## Worker/session contract

A Codex SDK session packet must bind at least:

```text
task_id
attempt_id
repository + immutable base/tree
issue/DAG node identities
worktree + branch identity
allowed/read-only/forbidden paths
start/completion predecessor receipts
acceptance/global-objective oracles
system-prompt/session-manifest digest
runtime/model/tool policy
budget/retry/timeout
structured-result contract
cleanup + rollback subject
Human-owned operations
```

One writing worker owns one mutable path/resource lease. Read-only explorers, test analysts and reviewers may execute in parallel when their scopes cannot mutate the Worker state.

## Shadow Architect monitor

Shadow is independent read/reconcile authority, not a second writer.

```text
Tech Lead candidate result
→ bind same immutable subject
→ recompute requirement applicability
→ inspect current source/contracts/tests/GitHub readback/runtime receipts
→ compare complete denominator
→ detect contradiction/evidence laundering/stale subject/false closure
→ HOLD | REJECT | ELIGIBLE_FOR_HUMAN_ADMIT
```

Required controls across #375–#378 include wrong worktree/thread/task identity, overlapping writer leases, missing predecessor consumption, stale GitHub edges, false sibling serialization, terminal-DONE laundering, model self-report without readback, fixture/static evidence promoted to live, issue-close/PR-merge promoted to problem closure, missing source claims, stale PDF/article locations, and credential/private-reasoning persistence.

## Problem closure chain

```text
source identity + exact location
→ problem id
→ applicability
→ task contract
→ DAG node
→ GitHub issue
→ session / attempt / worktree
→ commit / PR
→ deterministic / CI / live / Shadow receipts
→ merge subject when applicable
→ closure state
```

Allowed closure projection:

```text
OPEN
PARTIAL
IMPLEMENTED_UNVERIFIED
VERIFIED_LOCAL
VERIFIED_LIVE
NOT_APPLICABLE
HUMAN_ADMIT_REQUIRED
```

`issue closed == solved` and `PR merged == verified live` are forbidden equivalences.

## Molecular terminal delivery

`git-town-stacked-pr-worker` owns branch ancestry and PR molecularity, not semantic task planning.

```text
path-disjoint work              → SIBLING branches
unmerged byte dependency        → TRUE_CHILD Stack
multiple admitted prerequisites → one CONVERGENCE owner
runtime/Shadow evidence         → EXTERNAL_EVIDENCE edge, no Git parent
process ordering only           → PROCESS_DEPENDENCY, no Git parent
```

Every implementation atom must eventually record:

```text
issue
relation class
branch + base/true parent
consumed/provided artifacts
writable lease
acceptance/eval/negative controls
exact-head workflow/runtime evidence
rollback
Human authority
terminal evidence state
successor/convergence owner
```

## Current Shadow verdict

```text
portable Tech Lead core                 IMPLEMENTED
issue dual-DAG contract                 IMPLEMENTED
molecular Stack method                  IMPLEMENTED
independent Shadow procedure            IMPLEMENTED
new-repository bootstrap foundation     IMPLEMENTED / evidence subject owned by #361/#364 lineage
Codex SDK controller adapter            NOT_IMPLEMENTED (#375)
GitHub Issue Dependency projection      NOT_IMPLEMENTED (#376)
Herdr runtime observer adapter          NOT_IMPLEMENTED (#377)
problem-closure machine ledger          NOT_IMPLEMENTED (#378)
control-plane docs/index convergence    IN_PROGRESS (#379)
live Codex SDK session execution        NOT_EXERCISED
live Herdr observation                  NOT_EXERCISED
merge/release                           HUMAN_ADMIT_REQUIRED
```

## Cold-start read route

A fresh Agent handling this program should read:

```text
root AGENTS.md
→ CONTEXT.md
→ docs/INDEX.md
→ docs/architecture/STATE_MACHINES.md
→ agentic-tech-lead-orchestration/AGENTS.md
→ agentic-tech-lead-orchestration/README.md
→ SKILL.md + selected modules only
→ procedural-shadow-runtime README/SKILL
→ git-town-stacked-pr-worker README
→ this trace
→ issues #375–#379
→ exact current GitHub/branch/workflow/runtime subjects
```

Chat history is not a required dependency.

## Evidence ceiling

This document establishes navigation and decomposition only. It proves no Codex SDK, Herdr, GitHub dependency mutation, Agent/model behavior, live provider, CI, merge, release, production safety or closure outcome.
