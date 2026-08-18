---
name: git-town-stacked-pr-worker
description: |
  Govern eval-first Stacked PRs with Git Town in repositories that use multiple Worker Agents,
  isolated worktrees, bounded unattended sync/rebase, path leases, machine-readable receipts,
  GitHub Actions publication boundaries, and Human Admit for merge and promotion. Use when a
  repository asks for Git Town, stacked branches, background sync, parallel coding agents,
  private-repository CI cost control, PR dependency graphs, or a reusable Git-management system
  prompt. NOT for generic Git tutorials, semantic conflict resolution, automatic merge/ship,
  permission widening, secret setup, or production rollback.
---

# git-town-stacked-pr-worker

One canonical method for using Git Town as a **branch graph and synchronization engine** while the consuming repository keeps ownership of task decomposition, Bash adapters, evals, evidence, merge policy, release promotion, and rollback.

## Core boundary

```text
Git Town
  = branch hierarchy + deterministic local synchronization

github-delivery-loop
  = exact-HEAD GitHub publication admission + billing circuit

Consumer repository
  = repo profile + work packets + path leases + Bash wrapper + CI + receipts

Human / trusted operator
  = semantic conflict resolution + legal acceptance + billing recovery
    + merge/ship + promotion + rollback
```

`git town sync` exit `0` proves only that the selected synchronization command completed. It does not prove implementation correctness, review approval, GitHub publication admission, release readiness, provider availability, or production safety.

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
9. the publication fragment from [`references/GITHUB_ACTIONS_PUBLICATION_PROFILE.template.md`](references/GITHUB_ACTIONS_PUBLICATION_PROFILE.template.md) when GitHub publication is possible;
10. exact Git Town admission record, version policy, and host evidence;
11. [`PUBLICATION_POLICY.md`](PUBLICATION_POLICY.md) when any remote publication or GitHub Actions run is possible.

A missing required input is `ABSENT`; do not infer it from branch names, prose, a package manifest, or another repository.

## Use

1. Compose the target Agent instruction surface from the **contents**, not file paths, of [`SYSTEM_PROMPT.md`](SYSTEM_PROMPT.md) and [`PUBLICATION_POLICY.md`](PUBLICATION_POLICY.md), or reference this shared Skill from the target repository.
2. Fill one repository-owned profile from [`references/REPO_PROFILE.template.md`](references/REPO_PROFILE.template.md); compose the publication fragment when GitHub publication is possible.
3. Design issue/PR evals before branch or implementation work using [`references/EVALS.md`](references/EVALS.md) plus [`references/GITHUB_ACTIONS_PUBLICATION_EVALS.md`](references/GITHUB_ACTIONS_PUBLICATION_EVALS.md).
4. Keep target-repository scripts and configuration in that repository. Do not copy them back into this shared Skill.
5. Require the base completion shape plus [`references/GITHUB_ACTIONS_PUBLICATION_REPORT.template.md`](references/GITHUB_ACTIONS_PUBLICATION_REPORT.template.md).
6. When one request needs more than one branch writer, compile and check the fan-out contract before any branch or worktree exists, using [`references/TECH_LEAD_FAN_OUT.md`](references/TECH_LEAD_FAN_OUT.md) and [`references/FAN_OUT_CONTRACT.schema.json`](references/FAN_OUT_CONTRACT.schema.json):

   ```bash
   python3 skills/git-town-stacked-pr-worker/scripts/check_fanout_contract.py path/to/fanout.json
   ```

   Exit `2` names the refused shape: a mutable base, unequal competitor context, an undifferentiated competitor, overlapping concurrent leases, a child edge with no consumed contract, a writable acceptance path, a budget overflow, qualitative review ranked before the hard gates, cross-competitor cherry-pick, an ambiguous or premature convergence, an automatic winner or semantic merge, a required Code-Graph-RAG provider, or a laundered compiler-truth funnel state. A pass proves the plan is consistent, never that a branch, worktree, Agent, provider or Git Town sync ran.
7. Run `tests/run-all.sh` before publishing changes to this Skill.

The base adoption path is in [`references/ADOPTION.md`](references/ADOPTION.md); GitHub publication integration is in [`references/GITHUB_ACTIONS_PUBLICATION_ADOPTION.md`](references/GITHUB_ACTIONS_PUBLICATION_ADOPTION.md).

## Non-negotiable laws

- One Worker gets one isolated linked worktree and one branch writer lease.
- Independent work becomes sibling branches with disjoint path leases, not an artificial serial stack.
- A task cannot start until goal, non-goals, parent, path lease, evals, negative controls, evidence boundary, cleanup, and rollback subject exist.
- Exact Git Town version and executable admission come from the consumer/host policy; mutable `latest` is not an identity.
- Unattended sync is non-interactive, bounded, default no-push, and uses `--no-auto-resolve`.
- Background synchronization may never invoke `git town sync --push`, raw `git push`, a PR-ready transition, or a workflow rerun.
- Semantic conflicts stop the Worker. The Worker must not run automatic `continue`, `skip`, `undo`, `ship`, merge, or semantic edits.
- GitHub publication requires the canonical `github-delivery-loop` gate or a repository-admitted equivalent bound to the exact local `HEAD`.
- The only portable publication intents are `initial-pr`, `ready-for-review`, and `batched-repair`.
- `billing-open`, stale local verification, old-SHA checks, repeated feedback, or ambiguous PR identity block publication.
- Publication still requires the consumer-owned operator guard and post-push ancestry verification; gate `ALLOW` is not merge or promotion authority.
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

A GitHub publication decision remains a separate lane:

```text
ALLOW <intent> <single-operation>
BLOCK <stable-reason>
INVALID_POLICY_INPUT
```

Every non-success outcome must preserve enough state for reviewed recovery and must not silently rewrite history.

Completion evidence must keep local sync, local verification, publication decision, remote publication, remote ancestry, GitHub trusted check, and Human Admit as separate lanes.

## Evidence boundary

Static prompt review may prove the instruction contract. It cannot proxy:

- exact executable checksum/provenance/SBOM admission;
- a real Git Town run;
- a real remote publish;
- a planted conflict canary;
- multi-Worker scheduling;
- a current GitHub Actions runner allocation;
- consumer CI;
- Human Admit.

A skipped draft workflow is `SKIPPED_BY_POLICY`; an account-level no-runner billing blocker is not test `FAIL` or `PASS`. Those states remain distinct until the owning environment emits a subject-bound receipt.

## Shared versus repo-owned

This Skill owns the portable Git Town method and the requirement to consume the canonical GitHub publication policy. `github-delivery-loop` owns the portable publication schemas and evaluator. The following are always repo-owned:

- `.git-town.toml` or equivalent configuration;
- branch names and parent graph;
- issue/PR numbers;
- worktree and receipt roots;
- Bash wrappers;
- CI workflows;
- GitHub state snapshot capture;
- exact local-verification receipt production;
- billing recovery receipts;
- remote names and publication guards;
- path ownership and eval commands;
- rollback refs;
- live receipts.

A consumer-local `git-town-stacked-pr-worker` or `github-delivery-loop` copy would shadow the shared canonical body and is a governance error. Retarget through a repository profile or binding instead.
