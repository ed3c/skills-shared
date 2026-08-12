---
name: git-town-stacked-pr-worker
description: |
  Govern eval-first Stacked PRs with Git Town in repositories that use multiple Worker Agents,
  isolated worktrees, bounded unattended sync/rebase, path leases, machine-readable receipts,
  and Human Admit for merge and promotion. Use when a repository asks for Git Town, stacked
  branches, background sync, parallel coding agents, PR dependency graphs, or a reusable
  Git-management system prompt. NOT for generic Git tutorials, semantic conflict resolution,
  automatic merge/ship, permission widening, secret setup, or production rollback.
---

# git-town-stacked-pr-worker

One canonical method for using Git Town as a **branch graph and synchronization engine** while the consuming repository keeps ownership of task decomposition, Bash adapters, evals, evidence, merge policy, release promotion, and rollback.

## Core boundary

```text
Git Town
  = branch hierarchy + deterministic synchronization

Consumer repository
  = repo profile + work packets + path leases + Bash wrapper + CI + receipts

Human / trusted operator
  = semantic conflict resolution + legal acceptance + merge/ship + promotion + rollback
```

`git town sync` exit `0` proves only that the selected synchronization command completed. It does not prove implementation correctness, review approval, release readiness, provider availability, or production safety.

## Mandatory read order

Before changing a consumer repository:

1. root `AGENTS.md` and host-specific projection such as `CLAUDE.md`;
2. architecture/placement SSOT;
3. repository Git and Stacked-PR governance;
4. Harness and eval contracts;
5. nearest `README.md` for every writable path;
6. issue or Worker task packet;
7. current PR/branch graph;
8. repository profile derived from [`references/REPO_PROFILE.template.md`](references/REPO_PROFILE.template.md);
9. exact Git Town admission record, version policy, and host evidence.

A missing required input is `ABSENT`; do not infer it from branch names, prose, a package manifest, or another repository.

## Use

1. Copy the **contents**, not the file, of [`SYSTEM_PROMPT.md`](SYSTEM_PROMPT.md) into the target Agent system/developer instruction surface, or reference this shared Skill from the target repository.
2. Fill one repository-owned profile from [`references/REPO_PROFILE.template.md`](references/REPO_PROFILE.template.md).
3. Design issue/PR evals before branch or implementation work using [`references/EVALS.md`](references/EVALS.md).
4. Keep target-repository scripts and configuration in that repository. Do not copy them back into this shared Skill.
5. Require the completion shape in [`references/COMPLETION_REPORT.template.md`](references/COMPLETION_REPORT.template.md).

The complete adoption path is in [`references/ADOPTION.md`](references/ADOPTION.md).

## Non-negotiable laws

- One Worker gets one isolated linked worktree and one branch writer lease.
- Independent work becomes sibling branches with disjoint path leases, not an artificial serial stack.
- A task cannot start until goal, non-goals, parent, path lease, evals, negative controls, evidence boundary, cleanup, and rollback subject exist.
- Exact Git Town version and executable admission come from the consumer/host policy; mutable `latest` is not an identity.
- Unattended sync is non-interactive, bounded, default no-push, and uses `--no-auto-resolve`.
- Semantic conflicts stop the Worker. The Worker must not run automatic `continue`, `skip`, `undo`, `ship`, merge, or semantic edits.
- Publication requires an explicit consumer-owned double guard and post-push ancestry verification.
- No credential-bearing remote URL, `.env`, token, browser profile, device session, key material, or secret value enters Git or portable receipts.
- `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, and `SKIPPED_BY_POLICY` are distinct.
- Direct permissive-license evidence is one input, not a promise of zero commercial/legal risk; transitive dependencies, artifacts, notices, service terms, patents, trademarks, export controls, and organization approval remain separate.

## Stable Worker outcomes

```text
SYNCED
NO_CHANGE
BLOCKED_TASK_PACKET
BLOCKED_DIRTY
BLOCKED_CONFLICT
BLOCKED_PROMPT
BLOCKED_TIMEOUT
BLOCKED_BRANCH_LEASE
BLOCKED_ANCESTRY
BLOCKED_POLICY
FAILED_TOOL
FAILED_EVAL
ROLLBACK_REFUSED_DRIFT
```

Every non-success outcome must preserve enough state for reviewed recovery and must not silently rewrite history.

## Evidence boundary

Static prompt review may prove the instruction contract. It cannot proxy:

- exact executable checksum/provenance/SBOM admission;
- a real Git Town run;
- a real remote publish;
- a planted conflict canary;
- multi-Worker scheduling;
- consumer CI;
- Human Admit.

Those remain `NOT_EXERCISED` until the owning environment emits a subject-bound receipt.

## Shared versus repo-owned

This Skill owns the portable method and prompt. The following are always repo-owned:

- `.git-town.toml` or equivalent configuration;
- branch names and parent graph;
- issue/PR numbers;
- worktree and receipt roots;
- Bash wrappers;
- CI workflows;
- remote names and publication guards;
- path ownership and eval commands;
- rollback refs;
- live receipts.

A consumer-local `git-town-stacked-pr-worker` copy would shadow this shared body and is a governance error. Retarget through a repository profile or binding instead.