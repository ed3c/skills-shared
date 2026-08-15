# dual-forge-repository-loop

Portable orchestration for a private GitHub repository plus a local Forgejo implementation plane, with an optional capability-bound Builder/Shadow and multi-Worker control contract.

## Composition boundary

```text
repository multi-Agent composition kernel
  = topology selection + Shadow control + Worker attempts/leases/results + budgets

spatial-loop-systems-engineering
  = architecture deltas + invariants + evidence promotion + three-failure escalation

git-town-stacked-pr-worker
  = branch graph + isolated worktrees + path leases + bounded synchronization

dual-forge-repository-loop
  = GitHub/Forgejo authority separation + local-main-first ordering + publication lineage

consumer repository/runtime
  = concrete paths, branches, profiles, tasks, live Workers, tools, credentials,
    receipts, CI, merge policy, and production authority
```

The composition prompt does not turn documentation into a scheduler. The machine contract validates submitted topology/attempt/result relationships; live execution remains a separate evidence lane.

## Multi-Agent runtime state

```text
RUNTIME_BOUND
→ TOPOLOGY_SELECTED
    ├── SINGLE_BUILDER
    ├── BUILDER_SHADOW
    └── MULTI_WORKER only after all admission predicates pass
→ TASKS_AND_ATTEMPTS_BOUND
→ PATH_STATE_AND_RESOURCE_LEASES_BOUND
→ WORKER_RESULTS_BOUND
→ POSITIVE_AND_NEGATIVE_EVIDENCE_BOUND
→ BUDGET_LEDGER_CLOSED
→ SHADOW_AND_MERGE_BOUNDARIES_CLOSED
→ DELIVERY_LANE
```

The deterministic gate rejects false parallelism admission, duplicate task/attempt/branch/worktree identities, dependency cycles, overlapping path/state/resource ownership, stale or out-of-lease results, unreconciled budgets, in-process Shadow independence overclaim, L3 bypass, collapsed evidence/authority states, and Agent merge enablement.

## Dual-forge data flow

```text
ChatGPT iOS/macOS or other GitHub-connected host
        ↓ GitHub private repo + issues/PRs + remote main SHA
GitHub ingress snapshot
        ↓
local checkout + Forgejo mirror
        ↓
Forgejo issues
        ↓
isolated worktrees / one writer
        ↓
verification + negative controls
        ↓
Forgejo PRs
        ↓
LOCAL MAIN
        ↓
re-fetch GitHub main + enumerate open GitHub PRs/issues
        ↓
ancestry/conflict/issue reconciliation
        ↓
publication candidate
        ↓
GitHub Actions exact-head verification
        ↓
GitHub issue/PR publication
        ↓
repository merge policy / Human Admit
```

## Authority map

| Plane | Authority | Not authority for |
|---|---|---|
| Composition kernel | topology, task/result vocabulary, budget and Shadow/merge stop conditions | live Worker creation, provider truth, merge |
| Deterministic runtime checker | semantic closure of one submitted runtime contract | proving a model/process/worktree actually ran |
| GitHub connector/app | private-repo ingress, issues/PR metadata and allowed mutations | local Forgejo state, local test execution |
| GitHub Actions | remote CI evidence for exact head | local implementation history, semantic merge correctness |
| Local checkout | Git object integration and local main | remote GitHub publication state |
| Forgejo | local implementation issues/PR receipts | GitHub issue/PR identity or Actions truth |
| Worktree | one issue/branch writer | global main or another Worker branch |
| Shadow Architect | architecture/evidence delta classification and named L3 blocker | implementation-path mutation or self-created authority |
| External trusted automation / Human | merge/admit under existing repository policy | retroactively converting absent evidence into PASS |

## Documents and machine authorities

- [`SKILL.md`](SKILL.md): dual-forge procedure and hard laws.
- [`references/system-prompt.md`](references/system-prompt.md): Repository Multi-Agent Runtime + Dual-Lane Delivery system prompt v2.1.
- [`references/multi-agent-runtime-machine-contract.md`](references/multi-agent-runtime-machine-contract.md): checker scope, state machine, exits, and evidence boundary.
- [`references/multi-agent-runtime-contract.schema.json`](references/multi-agent-runtime-contract.schema.json): top-level runtime/topology/Shadow/budget/state contract.
- [`references/worker-task.schema.json`](references/worker-task.schema.json): task, attempt, branch/worktree, lease, oracle, budget, and lifecycle packet.
- [`references/worker-result.schema.json`](references/worker-result.schema.json): durable result, artifact, eval/control, checkpoint, and budget receipt.
- [`references/multi-agent-runtime-profile.template.json`](references/multi-agent-runtime-profile.template.json): consumer-owned quantitative fallback/fan-out profile template.
- [`references/repo-binding.template.json`](references/repo-binding.template.json): dual-forge repo-owned binding/receipt shape.
- [`scripts/check_multi_agent_runtime.py`](scripts/check_multi_agent_runtime.py): deterministic topology, DAG, ownership, result, budget, Shadow, and merge-boundary checker.
- [`scripts/check_dual_forge_contract.py`](scripts/check_dual_forge_contract.py): deterministic publication-order checker.
- [`scripts/export_git_proof.py`](scripts/export_git_proof.py): canonical four-ref Git ancestry/tree proof producer.
- [`scripts/capture_origin_ref.py`](scripts/capture_origin_ref.py): canonical GitHub API, authenticated loopback Forgejo API, and local Git default-ref observation producer.
- [`scripts/capture_reconciliation.py`](scripts/capture_reconciliation.py): exhaustive paginated GitHub/Forgejo open-PR/open-issue raw transport and typed-inventory replay.
- [`scripts/capture_forgejo_delivery.py`](scripts/capture_forgejo_delivery.py): causal fresh-worktree materialization, Forgejo issue/merged-PR plus local-main parent/tree receipt producer and replay.
- [`evals.json`](evals.json), [`tests/`](tests/): positive and planted-negative controls, including [`tests/multi-agent-runtime/`](tests/multi-agent-runtime/README.md).

## Runtime contract command

```bash
python3 skills/dual-forge-repository-loop/scripts/check_multi_agent_runtime.py \
  path/to/repository-multi-agent-runtime.json
```

```text
exit 0   submitted contract structurally and semantically closes
exit 2   structurally valid contract violates a runtime invariant
exit 64  absent, malformed, unreadable, or schema-invalid input
exit 70  schema validator unavailable; the check is not skipped
```

A passing contract is not a live Worker, Shadow context, Git Town run, Forgejo mutation, GitHub Actions run, or merge receipt.

## Evidence boundary

```text
portable dual-forge orchestration contract          IMPLEMENTED
deterministic publication gate                      IMPLEMENTED
Repository Multi-Agent Runtime v2.1 prompt          IMPLEMENTED
runtime/task/result Draft 2020-12 schemas            IMPLEMENTED
semantic topology/lease/result/budget checker        IMPLEMENTED
positive multi-Worker + single-Builder fixtures      IMPLEMENTED
planted multi-Agent mutation controls                IMPLEMENTED
canonical Git proof export/replay                    IMPLEMENTED
raw provider transport replay                        IMPLEMENTED
Forgejo delivery receipt replay                      IMPLEMENTED
exact-local-main verification triple                 IMPLEMENTED
full issue/comment + PR closure replay               IMPLEMENTED
structured Desktop receipt + screenshot-byte derivation IMPLEMENTED
live multi-Agent scheduler                           NOT_EXERCISED
independent Shadow context/model                     NOT_EXERCISED
live checkpoint/resume and straggler reassignment    NOT_EXERCISED
organization-level alignment                         NOT_EXERCISED
ChatGPT private-GitHub ingress                        NOT_EXERCISED by this Skill's tests
local Forgejo mutation                               NOT_EXERCISED
real consumer worktree integration                   NOT_EXERCISED
consumer GitHub Actions                              NOT_EXERCISED
final merge                                          HUMAN_ADMIT_REQUIRED
```

The dual-forge machine checker treats an empty or partial publication history as a draft receipt: `NOT_EXERCISED`, exit `3`. Only complete publication-ready history can return `PASS`; a legal state-name prefix is not evidence that transitions ran.

The multi-Agent runtime checker separately uses exit `0/2/64/70` for one static contract. Neither checker can proxy the other's authority.
