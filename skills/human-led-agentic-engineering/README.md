# Human-Led Agentic Engineering

This directory is the portable composition layer for a human-led, high-throughput Agentic Engineering workflow. It does not vendor or canonize Kenn products. Existing shared Skills remain the owners of task DAGs, Shadow enforcement, architecture monitoring, and Stack PR mechanics.

## Directory ownership

```text
human-led-agentic-engineering/
├── SKILL.md                         portable laws and workflow
├── AGENTS.md                        local Agent read order and authority
├── README.md                        topology, State Machine, DAG and data flow
└── references/
    └── design-admission.schema.json machine shape for Human design admission
```

Future provider adapters belong under trigger-selected modules or consumer repositories. Runtime paths, credentials, issue IDs, provider sessions, local databases, and live receipts never enter this portable directory.

## State Machine

```text
REQUEST_BOUND
→ HUMAN_DESIGN_ACTIVE
→ DESIGN_ADVERSARY_COMPLETE
→ HUMAN_DESIGN_ADMITTED
→ SYSTEM_CONTRACT_EXTRACTED
→ CAPABILITY_PLAN_ASSERTED
→ TASK_DAG_ASSERTED
→ WORKSPACE_LEASED
→ IMPLEMENTATION_ACTIVE
→ COMMIT_CREATED
→ COMMIT_REVIEW_RECONCILED
→ BRANCH_REVIEW_RECONCILED
→ GLOBAL_OBJECTIVE_ASSERTED
→ LIVING_CONTEXT_PERSISTED
→ DELIVERY_READY
→ HUMAN_ADMIT_REQUIRED
```

### State owners

| State family | Owner | Evidence ceiling |
|---|---|---|
| design | Human + independent Design Adversary | design direction only |
| task/capability planning | `agentic-tech-lead-orchestration` | admitted execution contract |
| procedure/architecture shadow | `procedural-shadow-runtime` + `spatial-loop-systems-engineering` | read-only intervention/evidence |
| implementation | consumer Worker/runtime | leased artifact changes |
| verification | native/domain gates + optional review providers | exact-subject verification evidence |
| documentation persistence | owning repo docs/contracts | durable context only |
| delivery | `git-town-stacked-pr-worker` + delivery loops | reviewable Stack PR state |
| merge/release | Human/trusted policy | irreversible delivery authority |

## Dependency DAG

```text
DESIGN_ADVERSARY_COMPLETE ─┐
                           ├─> HUMAN_DESIGN_ADMITTED
Human decision ────────────┘

HUMAN_DESIGN_ADMITTED
  -> SYSTEM_CONTRACT_EXTRACTED
  -> CAPABILITY_PLAN_ASSERTED
  -> TASK_DAG_ASSERTED

TASK_DAG_ASSERTED
  -> Worker sibling slices when path/resource leases are disjoint
  -> TRUE_CHILD only when a child consumes named unmerged parent bytes/contracts

Worker commits
  -> ReviewProviderPort evidence
  -> native/domain verification
  -> convergence owner
  -> branch/global objective gate
  -> living-context owner
  -> Stack PR delivery
```

Process order does not manufacture Git ancestry. A review provider PASS does not manufacture verification PASS.

## Data flow

```text
Human intent / issue / source proposal
  ↓
Design snapshot + invariants + non-goals
  ↓
Independent adversarial design challenge
  ↓
Human design-admit receipt
  ↓
Tech Lead contracts + capability DAG + task DAG
  ↓
Leased worktrees / Workers
  ↓
Commit subjects
  ├─> review-provider evidence
  ├─> deterministic/domain tests
  └─> Shadow architecture delta observations
  ↓
Independent reconciliation
  ↓
Branch-wide/global-objective closure
  ↓
Living architecture/context sync
  ↓
Molecular Stack PR index
  ↓
Human delivery decision
```

## Provider selection

Provider selection is replaceable and license-aware:

```text
IntentLedgerPort
  ├─ GitHub Issues
  └─ Kata (MIT)

ReviewProviderPort
  ├─ native reviewer
  └─ roborev (MIT)

SessionObservabilityPort
  ├─ native metrics
  └─ AgentsView (MIT)

WorkspacePort
  ├─ Git Town
  ├─ kwt (Apache-2.0)
  └─ Kenn Forge (Elastic-2.0; external process/API boundary only)

SessionCarrierPort
  ├─ tmux / Herdr / Zellij
  └─ Ghosthub (AGPL-3.0; external process boundary only)
```

Installation or availability never self-selects a provider. The Tech Lead capability plan must bind the trigger, identity, authority ceiling, fallback, and receipt requirement.

## Stack PR decomposition

The intended molecular delivery topology for this integration is:

```text
S1 DESIGN-CONTROL-PLANE
  adds portable Human Design Gate + adversary + provider boundaries

S2 SHARED-INDEX-AND-TRACE
  TRUE_CHILD of S1 only because it references the new shared method bytes
  updates root routing, README, traceability and issue closure map

B1 BETTOR-CONSUMER-BINDING
  cross-repository consumer slice; does not form Git ancestry with S1/S2
  binds exact shared release/commit and adds consumer adapters/contracts

B2 BETTOR-PROVIDER-LEAVES
  siblings under the Bettor consumer plan when provider implementations are path-disjoint
  e.g. review / intent / observability adapters

B3 BETTOR-CONVERGENCE
  sole owner of shared Bettor indexes, aggregate docs and final consumer verification
```

The canonical Stack PR index remains the repository's existing `git-town-stacked-pr-worker` traceability owner; this README records only the method-relative decomposition.

## Closure against Kenn workflow problems

| Real problem | Current shared closure |
|---|---|
| autonomous loops can drift | closed by Human/receipt authority and Shadow gates |
| design/taste delegated to Agent | this Skill adds explicit Human Design Gate |
| second opinion conflated with implementation | explicit Design Adversary role |
| imprecise plan/parallel collisions | existing Tech Lead typed DAG + leases |
| self-reported success | existing independent verification laws |
| continuous commit review | provider contract defined; live adapter issue remains |
| branch-wide bug bash | branch/global-objective state exists; live provider issue remains |
| transient specs pollute repo | living-context classification is explicit |
| intent scattered across prose | IntentLedgerPort issue remains |
| session/token accountability | SessionObservabilityPort issue remains |
| human-unreadable PR output | delivery contracts should remain outcome-oriented; consumer enforcement may tighten |

Open work is tracked by GitHub issues; a documentation statement never upgrades an open issue to implemented evidence.
