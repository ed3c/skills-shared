# Skill refactor proof Stack — golden proof and generalized method

This document is the human-readable trace for Epic #318. Machine authority is:

- `skills/skill-refactor-proof-loop/references/refactor-proof-stack.json`;
- `skills/skill-refactor-proof-loop/references/refactor-proof-stack.schema.json`;
- `skills/skill-refactor-proof-loop/scripts/check_refactor_proof_stack.py`.

Open PR heads and current workflow states are read from GitHub metadata. This document records PR identities but does not self-embed a mutable open head SHA.

## Molecular implementation graph

```text
#307/#309 — Tech Lead causal/reachability repair
PR #308  fix/307-tech-lead-runtime-reachability → main
└─ consumes repaired task/capability contracts

#312 — production-shaped hermetic golden proof
PR #315  agent/312-tech-lead-real-task-ab → PR #308 branch
└─ consumes B2 checkers, schemas and frozen treatments

#319 — generalized proof contract and golden registry
PR #323  agent/319-skill-refactor-proof-contract → PR #315 branch
└─ consumes the matched L3 report, denominator and cleanup proof

#320 — Agent routes, directory State Machines, DAG and data flow
PR #324  agent/320-refactor-proof-agent-docs → PR #323 branch
└─ consumes the new portable contract and registry

#321 — molecular Stack and traceability convergence
PR #325  agent/321-refactor-proof-stack-index → PR #324 branch
├─ consumes root/nearest Agent and State Machine documentation
└─ converges the golden registry and Git Town traceability rules

#322 — cross-Skill adoption audit
PLANNED after the standard and convergence are Human-admitted
```

## Node ledger

| Node | Issues | PR | Stack class | Owns | Provides | State authority |
|---|---|---|---|---|---|---|
| Tech Lead causal repair | `#307/#309` | `#308` | root | task/capability Skill, routes, governance subject selection | B2 task/schema/semantic/capability gates and frozen treatments | GitHub PR metadata + owning workflows |
| Hermetic golden proof | `#312` | `#315` | true child | real-task fixture/runtime/scheduler/A-B suite | matched worktree/process/tournament/retry/global-objective/cleanup evidence | GitHub PR metadata + Skill Suites |
| Portable proof contract | `#319` | `#323` | true child | `skill-refactor-proof-loop`, registry, route and CI admission | L0-L5 contract, golden registry, mutation controls | GitHub PR metadata + Skill Suites/Shared Skills Infra |
| Agent documentation | `#320` | `#324` | true child | root and nearest Agent/README/State Machine routes | cold-start integration truth and directory DAG/data flow | GitHub PR metadata + route/check workflows |
| Molecular convergence | `#321` | `#325` | convergence | Stack schema/index/checker, Git Town README, traceability | complete issue/PR/artifact/evidence index | GitHub PR #325 metadata + exact-head workflows |
| Adoption audit | `#322` | delivery PRs of `agent/goal-33-issues-batch` and `agent/admit-batch` (GitHub metadata) | planned follow-up, terminal classification `PARTIAL` | `skills/skill-refactor-proof-loop/references/skill-adoption-ledger.json` + schema + checker; `docs/traceability/SKILL_REFACTOR_ADOPTION_AUDIT.md` (rendered) | cross-Skill adoption ledger, rendered audit report, standard admission (`evals/proof-standard-admission.json`, 2026-08-17) | per-gap migration issues and migration ordering still open |

## Artifact dependency edges

```text
PR #308
  task-and-semantic-admission
  capability-causal-dag
  frozen-treatment-fixtures
        ↓ consumed unmerged
PR #315
  matched-L3-report
  complete-denominator
  clean-worktree-process-receipt
        ↓ consumed unmerged
PR #323
  portable-proof-contract
  golden-proof-registry
  proof-checkers
        ↓ consumed unmerged
PR #324
  root-Agent-contract
  directory-State-Machine-map
  Tech-Lead-DAG-data-flow
        ↓ consumed unmerged
PR #325 convergence
  machine-molecular-Stack-index
  Git-Town-refactor-Stack-template
  complete-trace
```

PR #325 also consumes the verified registry from PR #323. This is a convergence edge, not a second Git parent.

## Independent live evidence lanes

These issues are not Stack children because they own other runtimes or evidence planes:

| Issue | Owner | Required contribution | Current proof layer |
|---|---|---|---|
| `#231` | scheduler/runtime | live attempts, leases, heartbeat, checkpoint, retry, stale and straggler receipts | open; L4 input not yet admitted |
| `#232` | independent Shadow | separate-context/model/checker L2/L3 enforcement and global objective | open; L4 input not yet admitted |
| `#234` | Git Town/dual forge | real synchronization, semantic-conflict refusal, Forgejo/GitHub delivery receipts | open; L5 input not yet admitted |
| `#256` | tool adapters | same-subject GrepAI, SCIP, Tree-sitter, Serena and SQLite receipts | open; L4 input not yet admitted |

They may raise issue #312 Phase 2 only when receipts bind the same treatment, repository, task graph, context, budget, carrier, repetitions and acceptance subjects.

## Golden proof result

```text
A_OLD_MONOLITH              PASS
B0_REFACTOR_AS_LANDED       BLOCKED_DISPATCH_ROUTE_ABSENT
B1_REACHABILITY_REPAIRED    PASS
B2_CAUSAL_DAG_REPAIRED      PASS
B3_CLOSURE_LAWS_BOUND       PASS

A/B1/B2/B3 final bytes      equivalent
B3 causal/evidence closure  strongest
```

B2 is frozen at the blob the registry pins; B3 is the live body carrying the
closure laws. Every treatment has exactly one immutable subject, so the newest
arm is the only one that moves when the core changes.

Current ceiling:

```text
L0 SOURCE_FREEZE              PASS
L1 STRUCTURAL_REACHABILITY    PASS
L2 EXECUTABLE_CONTRACT        PASS
L3 HERMETIC_REAL_TASK         PASS
L4 MATCHED_LIVE_MODEL_RUNTIME NOT_EXERCISED
L5 DELIVERY_AND_HUMAN_ADMIT   HUMAN_ADMIT_REQUIRED
```

This does not prove live model/provider quality, Git Town/Forgejo delivery, semantic conflict resolution, merge, release, promotion or production.

## Exact-head and workflow policy

```text
open PR
→ head policy READ_FROM_GITHUB_PR_METADATA
→ current workflow state read from the exact head

merged PR
→ immutable merge commit may be recorded
→ only with PASS workflow/evidence and terminal MERGED classification
```

A stale self-embedded head, old green workflow, issue close, or merge-side effect cannot advance a node.

## Rollback and Human boundary

Each node records its rollback. Closing a downstream PR preserves its parent artifacts. The Stack never grants automatic semantic conflict resolution, force push, `git town ship`, merge, release or promotion. Those remain Human/repository-trusted authorities.
