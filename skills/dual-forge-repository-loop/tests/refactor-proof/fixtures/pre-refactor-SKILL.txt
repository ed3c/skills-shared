---
name: dual-forge-repository-loop
description: |
  Coordinate a private GitHub repository, GitHub Actions, a local checkout, a local Forgejo implementation forge, isolated worktrees, and final GitHub publication as one evidence-bound delivery loop. Use when ChatGPT on iOS/macOS or another GitHub-connected agent reads a private GitHub repo, implementation should happen through local Forgejo issues/PRs and worktrees, verified changes merge to local main first, then GitHub remote drift/open PR conflicts/issues must be reconciled before exact-head Actions and GitHub publication. NOT for single-forge delivery or as authority to force-push, auto-merge, widen permissions, or fabricate local/Forgejo execution.
license: MIT
compatibility: Any Agent Skills-compatible coding agent. GitHub-connected hosts may perform GitHub operations; local Forgejo/worktree operations require a consumer runtime that actually has that local capability.
metadata:
  version: "1.2.0"
  procedure: "dual-forge-repository-loop/v3"
---

# dual-forge-repository-loop

Treat GitHub and local Forgejo as two distinct control planes over one Git object graph.

```text
GitHub plane
  = private-repository ingress + remote collaboration + GitHub Actions + publication evidence

Local/Forgejo plane
  = implementation issues + isolated worktrees + local verification + Forgejo PRs + local-main integration
```

Neither plane proves the other. Every transition across the boundary binds exact commit SHA and ancestry.

## Mandatory runtime identity preflight

Before any repository mutation, load [`references/runtime-identity-contract.md`](references/runtime-identity-contract.md) and classify the current execution runtime as exactly one of:

```text
CHATGPT_GITHUB_CONNECTOR
GITHUB_ACTIONS
CLAUDE_CODE_LOCAL
CODEX_CLI_LOCAL
CHATGPT_DESKTOP_WORKTREE
UNKNOWN
```

Runtime identity is based on observed capabilities/provenance, not model family. `CHATGPT_GITHUB_CONNECTOR` is not `GITHUB_ACTIONS`; connector access cannot prove a local checkout, shell, worktree, or Forgejo. `GITHUB_ACTIONS` cannot inherit developer-worktree or local-Forgejo authority. Local Claude Code/Codex CLI/Desktop worktree claims require an observed checkout/path/remotes/HEAD. `UNKNOWN` fails closed for irreversible delivery actions.

If runtime changes, rebind environment-specific evidence before continuing.

## Composition

This Skill orchestrates, but does not duplicate:

- `spatial-loop-systems-engineering` for pre-implementation invariants and three-failure escalation;
- `forgejo-delivery-loop` for local Forgejo issue/PR/receipt semantics;
- `git-town-stacked-pr-worker` for one-writer isolated worktrees and branch graphs;
- `github-delivery-loop` for GitHub publication admission and exact-head evidence.

## Owned state machine

```text
RUNTIME_BOUND
→ GITHUB_BOUND
→ LOCAL_SYNCED
→ FORGEJO_ISSUES_BOUND
→ WORKTREES_VERIFIED
→ FORGEJO_PRS_MERGED
→ LOCAL_MAIN_MERGED
→ GITHUB_RECONCILING
    ├── REMOTE_MAIN_DRIFT
    ├── OPEN_PR_CONFLICT
    ├── AFFECTED_GITHUB_ISSUE
    └── RECONCILED
→ GITHUB_ACTIONS_VERIFYING
    ├── STALE_HEAD
    ├── FAIL
    └── EXACT_HEAD_PASS
→ GITHUB_PUBLICATION_READY
→ GITHUB_PUBLISHED
→ HUMAN_MERGE_OR_HANDOFF
```

A state transition is invalid unless the exact subject SHA and the receipts required by that state exist.

## Hard laws

1. **Runtime-identity law** — bind execution provenance/capabilities before mutation. Never infer Actions/local/Forgejo capability from model name or connector presence.
2. **Dual-authority law** — local/Forgejo is implementation authority; GitHub is remote publication and Actions authority. Do not collapse them into one forge identity.
3. **Single object-graph law** — both remotes must refer to the same repository lineage. Cross-plane movement is expressed through commit ancestry, never file copying as an implicit merge.
4. **Local-main-first law** — issue implementation merges through verified Forgejo PRs into local main before GitHub publication reconciliation begins.
5. **Remote-drift law** — before any GitHub push/PR update, fetch/rebind current GitHub main. If it moved, reconcile it into the publication candidate without force overwrite.
6. **Open-PR law** — enumerate open GitHub PRs that target or overlap the changed paths. A conflicting PR remains an explicit blocker until rebased/retargeted/resolved under its own ownership rules.
7. **Issue-namespace law** — `forgejo#N` and `github#N` are different identities even when N matches. Link them with an explicit receipt; never infer equivalence.
8. **Exact-head Actions law** — GitHub Actions evidence is valid only when `actions.head_sha == publication.candidate_sha`.
9. **Reconciliation-before-publication law** — publication is blocked until remote-main drift, affected open PRs, and affected GitHub issues are enumerated and resolved/routed.
10. **No-force law** — no `git push --force`, force ref update, silent history rewrite, or overwrite of concurrent GitHub work.
11. **No-secret law** — credentials/tokens/browser sessions remain host-owned and may not enter repository bindings or receipts.
12. **Three-failure law** — three qualifying failures against the same target invoke the fresh-diagnosis escalation from `spatial-loop-systems-engineering`; no fourth blind patch.
13. **Human-authority law** — test success does not create permission to merge protected GitHub/Forgejo PRs, widen permissions, or promote production state.

GitHub and Forgejo repository owners may differ (for example
`ed3c/skills-shared` and `neon/skills-shared`). Bind both exact
`OWNER/REPOSITORY` identities and prove the local checkout has both admitted
remotes; equality of owner names is not an integration invariant.

## Procedure

### 0. Runtime binding

Classify the current runtime using the canonical runtime contract. Record working-directory, local git, connector, Actions, Forgejo, branch, HEAD, and writer-lease evidence. If a required capability is absent, route or hand off instead of pretending it exists.

### 1. GitHub ingress

From ChatGPT iOS/macOS or another GitHub-connected host, bind:

```text
repository_full_name
remote default branch
exact GitHub main SHA
open GitHub issues/PRs relevant to the requested work
latest relevant GitHub Actions state
```

Connector access proves only that the host can observe/mutate allowed GitHub resources. It does not prove local checkout or Forgejo availability.

### 2. Local and Forgejo binding

A local-capable runtime must independently prove:

```text
local repository path
local main SHA
GitHub remote identity
Forgejo remote identity
Forgejo repository identity
worktree root
credential hygiene
```

Synchronize by Git objects. Do not embed credentials in remote URLs.

### 3. Convert work into Forgejo implementation issues

For each implementation unit create or bind one Forgejo issue containing:

```text
source GitHub issue/PR/request link when applicable
objective + non-goals
exact base SHA
path lease
hard invariants
verification commands
negative controls
rollback subject
```

If a GitHub issue is mirrored locally, record both namespaced identities explicitly.

### 3a. Compile the Tech Lead task DAG before allocating Workers

When one request needs more than one branch writer, the decomposition is a
compiled artifact, not a supervising Agent's running judgement. The Tech Lead
owns the goal graph, the contracts, the branch topology and the writer leases;
a Worker owns one packet and one branch.

Method and role separation:
[`references/tech-lead-task-decomposition.md`](references/tech-lead-task-decomposition.md).
Plan shape: [`references/tech-lead-plan.schema.json`](references/tech-lead-plan.schema.json),
with a validated instance at
[`references/tech-lead-plan.example.json`](references/tech-lead-plan.example.json).

```bash
python3 skills/dual-forge-repository-loop/scripts/compile_tech_lead_plan.py \
  verify --plan path/to/plan.json
python3 skills/dual-forge-repository-loop/scripts/compile_tech_lead_plan.py \
  compile --plan path/to/plan.json --output path/to/packets
```

`verify` exits `2` and names the refusal on a path-lease collision, a dependency
cycle, an incomplete blindspot query and a child branch that declares no
consumed contract. `compile` writes Worker packets, a stack graph and a receipt
whose `runtime_state` is `NOT_EXERCISED`: a compiled plan proves the packets are
well formed, never that a branch, worktree, Agent or provider ran. Controls:
[`tests/tech-lead-plan/verify.sh`](tests/tech-lead-plan/verify.sh).

### 4. Implement in isolated worktrees

One issue gets one branch writer and one isolated worktree. Run the pre-implementation Spatial-Loop gate before high-complexity code. Implement the smallest vertical slice, then run owning tests/oracles and negative controls.

Failure routing:

```text
FAIL #1 → bounded repair
FAIL #2 → bounded repair
FAIL #3 → Forgejo/GitHub incident issue by owning plane + fresh diagnosis + new worktree
```

### 5. Forgejo PR and local-main integration

Only verified work is eligible for a Forgejo PR. After repository-required review/admit, merge to local main. Record:

```text
forgejo_pr
merged_commit
local_main_after_merge
verification receipt
```

Do not push GitHub yet merely because local main is green.

### 6. GitHub reconciliation sweep

Re-observe GitHub immediately before publication:

```text
current GitHub main SHA
all open PRs (with each PR's base recorded explicitly)
changed-file overlap/conflict risk
all open GitHub issues affected by the local-main changes
current branch ancestry
```

Classify every open PR:

```text
UNAFFECTED
CLEANLY_REBASEABLE
NEEDS_OWNER_REBASE
SEMANTIC_CONFLICT
SUPERSEDED_BY_LOCAL_MAIN
BLOCKED_OTHER
```

Do not edit every PR blindly. Fix conflicts only where ownership/admission permits; otherwise create/update an issue or handoff receipt. `do all issues` means every relevant open issue gets a terminal routing state, not that unrelated issues are silently modified.

### 7. Build publication candidate

Construct a candidate that contains both:

```text
latest admitted local main
latest observed GitHub main
```

The candidate must prove ancestry for both. A merge/rebase conflict stops the loop for semantic review; automatic conflict resolution is not authority.

### 8. Exact-head GitHub Actions

Publish only the candidate branch required to obtain GitHub Actions evidence under `github-delivery-loop`. Bind workflow/run/job identities and exact head SHA.

```text
candidate SHA changed after CI → previous CI becomes stale
Actions skipped by policy       → SKIPPED_BY_POLICY, not PASS
no runner / billing blocker     → provider blocker, not test FAIL
```

### 9. GitHub publication

After reconciliation and exact-head Actions pass, update/create the GitHub issue/PR projection. Preserve source Forgejo issue/PR receipts and local merge SHA in the publication body or attached receipt where repository policy allows.

GitHub merge remains governed by the target repository's policy.

## Machine contract

Use [`references/repo-binding.template.json`](references/repo-binding.template.json) as a starting point and validate a run receipt with:

```bash
python3 skills/dual-forge-repository-loop/scripts/export_git_proof.py \
  --repo-root /absolute/path/to/integration-worktree \
  --github-main <observed-github-main-sha> \
  --forgejo-main <observed-forgejo-main-sha> \
  --local-main <admitted-local-main-sha> \
  --candidate <publication-candidate-sha> \
  --output /path/to/receipt/proof/repository.fast-import

python3 skills/dual-forge-repository-loop/scripts/check_dual_forge_contract.py path/to/dual-forge-receipt.json
```

Before exporting the Git proof, produce each default-branch observation through
`capture_origin_ref.py` with authority `github`, `forgejo`, or `local`. The
producer uses `gh api`, authenticated allowlisted-loopback Forgejo API reads, or
local `git rev-parse` respectively; it emits a secret-free transport record and
a content-addressed observation. Hand-authored `authority` or transport strings
are not accepted. The transport retains exact logical argv, exit codes, provider
stdout plus per-output digest, and numeric GitHub/Forgejo repository identity;
the local lane additionally proves both admitted remote names/repositories. The
GitHub repository ID is cross-checked against the publication snapshot. Offline
checking proves binding/replay of those bytes; a synthetic fixture still does not
prove a live capture, so the live producer process remains the trusted provider lane.

`capture_forgejo_delivery.py` binds the implementation issue, merged Forgejo
PR, and local-main commit parents/tree. After the Desktop response, its
`materialize` command derives a causal branch from the Desktop receipt digest,
issue, and base SHA, then performs the only admitted `git worktree add`: a fresh
path, `--lock`, and no force/reset flags. Delivery replay rejects the main tree,
a pre-existing path/ref, an older creation timestamp, an unlocked or duplicated
branch holder, and a worktree whose common Git directory differs from the target
repository. Commit identity alone cannot prove repository ownership because a
separate clone can contain the same objects. The checker separately requires the
canonical exact-HEAD verification receipt, detailed command evidence, and the
content-addressed argv contract for that local-main tree; a bare `PASS` label or
command-name list is not verification. Delivery capture also replays the full
issue body, every paginated issue comment, the merged PR body and `merged_at`.
Publication-ready requires a provider-read `three-strike-recovery/v1` packet with
exactly three ordered attempt subjects, errors/digests, timestamps, and evidence
references. Its nested `chatgpt-desktop-submission/v1` receipt binds the full
prompt/digest, ordered Submit/timeline/response timestamps, exact ChatGPT thread
URL, provider comment-author identity, and fetched Forgejo screenshot attachment
bytes/media/SHA-256. Marker prose, a digest without artifact bytes, or a populated-
but-unsent Desktop composer remains `NOT_EXERCISED` and blocks publication-ready.
`capture_reconciliation.py` captures complete paginated open-PR and open-issue
inventories from both providers. Reconciliation classifications remain typed
human/Agent decisions, but their keys must equal the captured provider inventory:
an empty or selectively omitted list cannot pass. The GitHub publication PR is
the unique candidate-bound `WIP=1` subject captured during reconciliation and
its typed inventory route must be `PUBLICATION_SUBJECT/WIP_CAPTURED`; the later
Actions observation must name the same PR.

The immutable numeric Forgejo repository ID must agree across the default-ref
origin capture, delivery capture, and reconciliation capture. Matching
`owner/repository` text alone cannot join those three evidence subjects.

`export_git_proof.py` is the only canonical Git proof producer. It refuses a
candidate unless the object graph proves `forgejo_main -> local_main -> candidate`
and also contains the observed GitHub main. It exports exactly
`refs/heads/github-main`, `refs/heads/forgejo-main`,
`refs/heads/local-main`, and `refs/heads/candidate`, and caps the replay stream
at 64 MiB. The receipt binds the stream by SHA-256; the checker imports it into
a disposable bare repository, runs strict object verification and
`merge-base --is-ancestor`, then reads the candidate tree from the verified Git
commit. Hand-authored ancestry booleans have no authority.

The checker owns composition and ordering, not a second publication truth. At
`GITHUB_PUBLICATION_READY` it must read content-addressed `github-delivery-loop`
decision-manifest inputs (including canonical policy, required check identity,
optional billing recovery, and evaluation time), reproduce the canonical
decision, derive the Actions observation and snapshot from bound raw GitHub API
transport captured through an admitted absolute `gh` path with recorded
realpath/binary SHA-256/version (never inherited-`PATH` resolution), and require exactly one
required-check execution with provider-derived workflow/run/job/check-suite/app
identities. A caller-selected fake provider and an exact-head rerun are refused.
The checker then requires
an exact-candidate successful required check on the same branch/PR subject.
Publication-ready also binds fresh GitHub/Forgejo/local main observations and an
explicit PR/issue/conflict reconciliation inventory. These structured receipts
do not make a synthetic fixture into live provider truth; live capture remains a
separately exercised authority lane, and connector access alone is never proof
that Forgejo or a local command ran.

An empty or proper-prefix `history` is a draft binding only. The checker returns
exit `3` with `NOT_EXERCISED`; it never prints `PASS` for a claimed intermediate
state whose state-specific receipts have not reached the full publication-ready
closure. Exit `0` is reserved for the exact `GITHUB_PUBLICATION_READY` history
and all proof lanes above.

## Runtime handoff

[`references/runtime-identity-contract.md`](references/runtime-identity-contract.md)
says what each runtime may claim. It does not cover what happens when one of
them runs out of capability halfway through, which is the situation that
actually occurs.

[`references/runtime-handoff-contract.md`](references/runtime-handoff-contract.md)
covers that: a capability matrix where every cell records how it was
established, and a packet that names the exact blocker, the remaining steps, and
which runtime can perform each one. Shape:
[`references/runtime-handoff.schema.json`](references/runtime-handoff.schema.json).
Worked example from #255:
[`references/runtime-handoff.example.json`](references/runtime-handoff.example.json).

```bash
python3 skills/dual-forge-repository-loop/scripts/check_runtime_handoff.py \
  check --packet path/to/handoff.json
```

The rule it exists for is `IDENTITY_LAUNDERED`: a step that writes a commit
assigned to a runtime without `git_author_identity`. That is #255 generalized —
GitHub's Git-Data `create_commit` exposes message, tree and parents but not
author, so a connector commit necessarily carries the linked account's real
address, and a plan that routes commit-writing there produces a machine role
under a person's address that the contribution gate catches one CI run too late.

It also refuses a step assigned to a runtime the matrix records as lacking a
required capability, a capability marked available with no evidence, a handoff
with no reproducible blocker, a sender that turns out to have had the capability
after all, a receiver missing something its own steps need, and a step no
runtime can perform that was routed at one anyway rather than at a Human.

A handoff moves work. It does not move evidence, authority, or the writer lease.

## Consumer delivery canary

[`scripts/run_consumer_canary.py`](scripts/run_consumer_canary.py) walks a real
consumer's delivery chain and records a state for **every** link, because a
receipt naming the four links that worked reads exactly like one that walked all
eleven. It mutates nothing: worktrees are created from the consumer's HEAD and
removed, both forge lanes are authenticated reads, and no branch, issue, PR,
push or merge is created.

```bash
python3 skills/dual-forge-repository-loop/scripts/run_consumer_canary.py \
  --consumer /path/to/consumer --github OWNER/NAME --forgejo OWNER/NAME \
  --out DIR [--allow-worktree]
python3 skills/dual-forge-repository-loop/scripts/check_consumer_canary.py check
```

[`scripts/check_consumer_canary.py`](scripts/check_consumer_canary.py) is
zero-network. It refuses an incomplete selection gate, a dirty consumer, a
consumer with no admitted dual-forge configuration, an unstated or duplicated
link, a coverage summary the chain does not support, a reconciliation claimed
`EXERCISED` without a passing replay, a credential-shaped value, and — the two
that matter — a link marked `EXERCISED` while the receipt says none of the
mutation it requires took place, and a link marked `BLOCKED` carrying no
observation of what blocks it.

That last rule refused its own author twice. `exact-head-github-actions` was
first written as blocked by the #191 billing circuit; measuring it showed the
consumer's Actions enabled and completing, so #191 is not in force there and the
link is held by a budget decision instead. A blocker nobody measured is a
blocker nobody can clear.

## Live multi-Worker scheduler

`references/worker-task.schema.json` declares twenty-one Worker states. A grep
for each of them found that `ASSIGNED`, `LEASED`, `CHECKPOINTED`, `RESULT_READY`
and `FAILED_RETRYABLE` had no producer anywhere -- not a script, not a fixture,
not a test -- and that every other state appeared only in a checker that reads
it or a fixture that constructs it. A state only tests can construct is a state
the runtime does not have.

[`scripts/run_worker_scheduler.py`](scripts/run_worker_scheduler.py) is the
producer. It builds a disposable subject repository, admits two path-disjoint
sibling Workers and one convergence owner, leases a worktree to each, runs a
real Agent inside it, verifies with an oracle the Worker cannot edit, and
integrates. The non-happy paths are driven on planted attempts. The committed
run in [`evals/receipts/scheduler-run.receipt.json`](evals/receipts/scheduler-run.receipt.json)
produced 17 of the 21 states; `BLOCKED_AUTHORITY`, `DUPLICATE_SUPPRESSED`,
`FAILED_TERMINAL` and `REJECTED_NOT_DECOMPOSABLE` are listed as not produced
rather than omitted.

```bash
python3 skills/dual-forge-repository-loop/scripts/run_worker_scheduler.py --out DIR
python3 skills/dual-forge-repository-loop/scripts/check_scheduler_receipt.py check
python3 skills/dual-forge-repository-loop/scripts/check_scheduler_receipt.py selftest
```

The checker is zero-network and runs no Agent. It refuses a duplicate attempt
identity, a broken or backwards transition log, an undeclared state, an attempt
that moves after a terminal state, an integration with no preceding verified
oracle, two writers holding one branch at once, a `LEASE_EXPIRED` that nothing
evaluated an expiry against, a skipped heartbeat, and a coverage claim the
transition log does not support.

Two scheduler defects were found by running it rather than by reading it, and
both are recorded in the code that fixes them: refusing a sibling as stale
merely because main advanced outside its lease (hidden serialism reintroduced
by the scheduler), and leasing a convergence Worker from the plan's base rather
than from the state containing the dependencies it consumes.

Evidence boundary: the receipt proves the transitions happened and the refusals
refused. It measures no throughput, latency or cost advantage over a single
Builder, and a disposable subject is not a production repository.

## Prompt baseline record

The #225 same-stack baseline for this Skill's System Prompt lives in
`evals/prompt-baseline-preregistration.json` (frozen design),
`evals/prompt-baseline-cases.json` (case set) and
`evals/prompt-baseline-result.json` (executed cells), produced by
[`scripts/run_prompt_baseline.py`](scripts/run_prompt_baseline.py).

Those three files make claims about each other, so they are checked against
each other:

```bash
python3 skills/dual-forge-repository-loop/scripts/check_prompt_baseline.py check
python3 skills/dual-forge-repository-loop/scripts/check_prompt_baseline.py selftest
```

It refuses a preregistration whose lifecycle state contradicts the committed
result, a drifted case set, a dropped or hidden arm, a cell that cannot have
come from the bound runtime, an arm order that does not reproduce from the
frozen derivation, and an eligibility outcome that the recorded cells do not
compute. The recorded outcome is `NOT_ELIGIBLE`: the candidate regressed
against the strongest baseline on the only metric that varied.

## Evidence states

Use only:

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
HUMAN_ADMIT_REQUIRED
```

ChatGPT iOS/macOS GitHub access, local Forgejo mutation, local worktree execution, Actions execution, and final merge are separate evidence lanes.
