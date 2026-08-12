# AGENTS.md — skills-shared operating contract

This repository is the canonical home for cross-repository Skills and the truth-gated Skill Eval/Evolution system. It is not a product monorepo and it is not a place for consumer-specific paths, credentials, branches, or live provider receipts.

## Mandatory read order

Before modifying this repository, read in order:

1. [`README.md`](README.md) — repository topology, integrated state machine, active PR stack, and continuation checklist.
2. [`docs/AGENT_INTEGRATION_STATE.md`](docs/AGENT_INTEGRATION_STATE.md) — live handoff/current integration truth.
3. [`docs/SKILL_EVAL_ROADMAP.md`](docs/SKILL_EVAL_ROADMAP.md) — target phases; do not confuse target architecture with landed state.
4. [`registry.json`](registry.json) — machine-readable shared versus repo-owned rulings.
5. [`skills/README.md`](skills/README.md) — canonical Skill directory contract.
6. The target skill's `README.md` when present, then its `SKILL.md`.
7. The target skill's nearest `modules/README.md`, `scripts/README.md`, and `tests/README.md` when present.
8. The target skill's `evals.json` and the exact issue/PR acceptance contract.
9. For GitHub delivery work, [`skills/github-delivery-loop/README.md`](skills/github-delivery-loop/README.md).
10. For Git Town or Stacked PR work, [`skills/git-town-stacked-pr-worker/README.md`](skills/git-town-stacked-pr-worker/README.md).

A missing required document, issue, eval, parent branch, implementation target, or evidence subject is `ABSENT`. Do not infer it from a branch name, roadmap, chat history, or another repository.

## Authority layers

The following are distinct and must not be collapsed:

| Authority | Owns |
|---|---|
| `registry.json` | whether a skill name is shared or repo-owned |
| `SKILL.md` | portable Agent behavior and operating law |
| `README.md` | human/Agent navigation, directory ownership, state-machine explanation |
| `evals.json` and `evals/` | machine-readable eval inventory and case contracts |
| deterministic verifier | hard-gate outcome authority for its declared subject |
| `scripts/` | executable mechanisms and transitions |
| `tests/` | positive, hollow, mutation, and integration controls |
| issue / PR | one admitted change, its path lease, evals, parent graph, and evidence boundary |
| Human Admit | merge, promotion, permission widening, legal acceptance, and production rollback |

Markdown must not become a second API, registry, schema, receipt, verifier, capability unlock, or merge authority.

## Shared versus consumer-owned

Shared here:

- portable `SKILL.md` bodies;
- reusable method documents;
- host-neutral scripts and fixtures that belong to the shared method;
- eval contracts for the shared method;
- canonical Skill Eval schemas, adapters, verifier contracts, mutation lineage, and release gates admitted by this repository.

Consumer-owned elsewhere:

- repository branch names and Git Town parent graph;
- `.git-town.toml`;
- worktree paths and path leases;
- repository-specific workflows and fixed verification commands;
- GitHub/Forgejo identities and live snapshots;
- secrets, browser profiles, device sessions, API keys, and provider credentials;
- live receipts, merge decisions, release promotion, and rollback refs.

A consumer-local copy of a shared skill silently shadows the canonical body and is a governance error unless `registry.json` explicitly classifies the name as repo-owned.

## Evidence vocabulary

Use these states exactly:

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
```

Rules:

- Source prose, architecture diagrams, package presence, and a green linter are not live runtime evidence.
- A GitHub job that never received a runner is `NOT_EXERCISED`, not repository-test `FAIL` and not `PASS`.
- A workflow job skipped by admitted trigger policy is `SKIPPED_BY_POLICY`, not executed evidence.
- A receipt is a claim. A control must reach the public entrypoint and observe behavior.
- A mutation or hollow control must demonstrate that a load-bearing guard can turn red.
- GitHub/Forgejo equivalence requires a subject-bound equivalence receipt; similar prose or files are insufficient.
- Capability unlock and release require the authorities and physical evidence defined by the live integration state; documentation and ecosystem quality cannot compensate.

## GitHub delivery and Actions publication

Local commit cadence, remote publication cadence, GitHub Actions cadence, and merge cadence are separate state machines.

For private repositories:

```text
local commits
→ local exact-HEAD verification
→ trusted GitHub snapshot
→ publication gate
→ one admitted push/transition
→ GitHub check
→ batched repair when actionable feedback exists
```

Do not push every local checkpoint. Do not use no-op commits or reruns to probe an open billing circuit. See [`skills/github-delivery-loop/README.md`](skills/github-delivery-loop/README.md).

## Git Town and Stacked PRs

Git Town is a branch hierarchy and synchronization engine, not a merge authority.

- One Worker owns one branch and one isolated linked worktree.
- Independent path-disjoint work uses sibling branches.
- A child branch is used only when it consumes unmerged parent bytes.
- Unattended sync is bounded, non-interactive, default no-push, and no auto-resolve.
- Semantic conflict stops the Worker.
- Terminal leaf PRs are the smallest reviewable implementation slices; convergence/index work is a separate leaf.
- `git town sync` exit `0` proves synchronization only, not correctness or merge readiness.
- After a parent squash merge, reconstruct/rebase the child onto the new tree and rerun the owning gates; old green status is not inherited.

See [`skills/git-town-stacked-pr-worker/README.md`](skills/git-town-stacked-pr-worker/README.md).

## Source-document boundary

The external architecture source `科技巨頭開源授權與AI框架v2.pdf` is classified as `SOURCE_PROPOSAL`. It proposes E2B/Firecracker, cloud/local synchronization, mobile automation, wallet/security, and cost choices. These statements do not become repository `PASS` until separately verified and exercised. Do not copy source confidence language such as absolute safety, guaranteed latency, licensing certainty, or cost certainty into current-state truth.

## Completion contract

Before claiming a change complete, report:

- changed skill names and paths;
- state-machine transition and authority boundary changed;
- whether shared/repo-owned classification changed;
- implementation target and verifier affected;
- public interfaces, schemas, or workflow triggers changed;
- eval IDs executed;
- positive and negative-control results;
- exact commit/PR subject and current base/head;
- Stacked PR parent, siblings, and terminal leaf;
- whether the owning workflow steps actually executed;
- evidence states that remain `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, or `SKIPPED_BY_POLICY`;
- Human Admit actions still required.

Do not claim merge, promotion, capability unlock, provider recovery, GitHub/Forgejo equivalence, or live runtime success without the corresponding immutable evidence.
