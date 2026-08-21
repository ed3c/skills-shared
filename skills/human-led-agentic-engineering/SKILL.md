---
name: human-led-agentic-engineering
description: Human-led Agentic Engineering composition for design admission, independent design challenge, typed Tech Lead execution, commit/branch adversarial verification, living-context persistence, and Human-owned delivery. Provider implementations remain adapters.
---

# Human-Led Agentic Engineering

## Purpose

This Skill composes existing `agentic-tech-lead-orchestration`, `procedural-shadow-runtime`, `spatial-loop-systems-engineering`, and `git-town-stacked-pr-worker` into a human-led delivery workflow. It internalizes the procedural lessons of high-throughput Agentic Engineering without making any model, issue tracker, reviewer, terminal, or IDE canonical.

## Hard laws

1. **Human design ownership.** Material product taste, architecture choice, irreversible scope, and trade-off selection require `HUMAN_DESIGN_ADMITTED` before implementation admission.
2. **Independent design challenge.** The design adversary is not the implementation Worker and cannot self-admit design.
3. **Model agreement is advisory.** Multi-model consensus cannot substitute for Human Admit or deterministic evidence.
4. **Providers are ports.** Kata, roborev, AgentsView, Kenn Forge, Ghosthub, or any future tool may implement a port but may not widen authority or become portable-core truth.
5. **Review is evidence, not correctness.** A provider review PASS is candidate evidence; native/domain assertions and global-objective checks remain distinct.
6. **Exact-subject binding.** Design, commit, branch, context and delivery receipts bind the exact repository/contract/tree/commit subject they claim.
7. **Transient plans are not durable architecture.** Before delivery, durable decisions/invariants must be routed into the owning `AGENTS.md`, `README.md`, `ARCHITECTURE.md`, context document, machine contract, or verifier; transient planning artifacts cannot become authority by retention.
8. **Human delivery authority.** Merge, release, visibility, permission, production promotion and destructive rollback remain Human/trusted-policy operations.

## State machine

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

`HUMAN_DESIGN_ADMITTED` and final `HUMAN_ADMIT_REQUIRED` are distinct gates. The first authorizes the frozen design direction; the second owns merge/release/promotion.

## Role DAG

```text
Human Designer
  ├─> Design Adversary (read-only independent challenge)
  └─> Tech Lead Orchestrator
         ├─> Worker A [lease A]
         ├─> Worker B [lease B]
         ├─> Implementation Verification Provider(s)
         └─> Shadow Architect Monitor [read-only]

Worker commits
  -> provider review receipts
  -> independent/native/domain reconciliation
  -> branch/global objective gate
  -> living context owner
  -> Stack PR / delivery handoff
  -> Human merge authority
```

## Data flow

```text
human intent
→ design snapshot
→ independent challenge receipt
→ Human design-admit receipt
→ Tech Lead system/task/capability contracts
→ leased implementation artifacts
→ exact commit/tree
→ review-provider evidence
→ independent verification receipt
→ branch/global-objective receipt
→ durable context delta
→ Stack PR traceability packet
→ Human delivery decision
```

## Provider ports

| Port | Permissive examples | Restricted/external examples | Authority ceiling |
|---|---|---|---|
| IntentLedgerPort | GitHub Issues, Kata (MIT) | — | task intent only |
| ReviewProviderPort | roborev (MIT), native reviewer | — | candidate review evidence |
| SessionObservabilityPort | AgentsView (MIT), native metrics | — | advisory/cost/trace evidence |
| WorkspacePort | Git Town, kwt (Apache-2.0) | Kenn Forge (Elastic-2.0) external only | workspace lifecycle only |
| SessionCarrierPort | tmux, Herdr, Zellij | Ghosthub (AGPL-3.0) external only | presentation/session transport only |

Restricted providers must remain replaceable process/API integrations unless a separate rights review explicitly admits a different boundary.

## Design admission

The machine contract is `references/design-admission.schema.json`. A valid receipt must bind:

```text
repository
subject
problem_statement_digest
design_digest
human_actor
admitted_at
adversary_receipt_digest
material_decisions[]
non_goals[]
```

A design adversary receipt must be present before Human design admission for material architecture changes. The adversary may emit dissent; Human Admit must record the disposition of unresolved material dissent rather than silently dropping it.

## Commit and branch verification

```text
COMMIT_CREATED
→ REVIEW_REQUESTED
→ PROVIDER_REVIEW_RECEIPT
→ FINDINGS_RECONCILED
   ├─ verified finding → REPAIR_REQUIRED
   ├─ false positive → DISMISSED_WITH_EVIDENCE
   └─ clean → NATIVE_GATES_REQUIRED
→ COMMIT_REVIEW_RECONCILED
```

Branch closure is separate:

```text
verified commits
→ branch-wide review/analysis
→ integration/domain tests
→ negative or mutation controls where applicable
→ global objective assertion
→ BRANCH_REVIEW_RECONCILED
```

Never infer branch correctness from all individual review providers reporting PASS.

## Living context persistence

Before `DELIVERY_READY`, classify transient knowledge:

```text
architecture invariant → ARCHITECTURE.md / owning context doc
agent operating rule    → nearest AGENTS.md
local topology/dataflow → nearest README.md
machine transition      → schema/checker/state-machine owner
current mutable handoff → CONTEXT.md / consumer handoff owner
historical rationale    → traceability/ADR only when repository policy admits it
```

Delete or ignore transient spec/plan artifacts when their durable obligations have been captured. A copied plan is not a living architecture document.

## Composition

- `agentic-tech-lead-orchestration` owns typed task/capability DAGs, leases, candidate comparison, convergence and Local Handoff queues.
- `procedural-shadow-runtime` owns read-only Shadow procedure/evidence enforcement.
- `spatial-loop-systems-engineering` owns architecture delta, hidden-assumption and failure-surface monitoring.
- `git-town-stacked-pr-worker` owns molecular branch/worktree/Stack PR mechanics.
- Consumer repositories own provider bindings, real runtime identities, secrets, worktrees, issue/PR IDs and live receipts.

## Stop conditions

Stop implementation admission on absent Human design admission for a material design, unresolved authority boundary, invalid exact-subject contract, overlapping writer leases, suppressed Shadow dissent, stale review receipt, failed deterministic/domain oracle, unpersisted durable architecture change, license-policy violation, or Human-owned delivery transition.
