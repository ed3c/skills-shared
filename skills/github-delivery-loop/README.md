# `github-delivery-loop`

`github-delivery-loop` owns the boundary between a locally materialized implementation and GitHub's issue, PR, check, publication, and merge surfaces. It does not own the implementation loop, the Git Town branch graph, Human Admit, or production promotion.

## Read order

1. [`SKILL.md`](SKILL.md) — mandatory Agent behavior.
2. This README — directory map, state-machine ownership, current state, and Stacked PR index.
3. [`modules/README.md`](modules/README.md) — mechanism-document index.
4. [`modules/state-machines.md`](modules/state-machines.md) — full transition contracts.
5. [`modules/traceability-index.md`](modules/traceability-index.md) — source → decision → issue → PR → eval → evidence.
6. [`scripts/README.md`](scripts/README.md) — executable ownership and I/O.
7. [`tests/README.md`](tests/README.md) and [`evals.json`](evals.json) — positive and negative controls.
8. [`../git-town-stacked-pr-worker/README.md`](../git-town-stacked-pr-worker/README.md) when branch stacks or unattended sync are involved.

## Directory map

```text
skills/github-delivery-loop/
├── README.md                         human/Agent navigation
├── SKILL.md                          portable operating law
├── evals.json                        eval inventory
├── modules/
│   ├── README.md                     mechanism index
│   ├── delivery-mechanism.md         registry, receipt, publication and metrics model
│   ├── github-actions-cost-control.md
│   │                                 private Actions publication boundary
│   ├── host-permissions.md           Claude/Codex/GitHub permission planes
│   ├── state-machines.md             state ownership and transitions
│   └── traceability-index.md         sources, decisions, issues, PRs and evidence
├── scripts/
│   ├── README.md
│   ├── github_delivery.py            zero-network delivery check and sync entry
│   ├── delivery_sync.py              compatibility/public sync adapter
│   ├── delivery_sync_impl.py         delivery derivation implementation
│   ├── local_verification.py         exact-HEAD local verification receipt producer
│   ├── github_actions_snapshot.py    trusted capture and zero-network replay
│   ├── ci_publish_gate.py            publication ALLOW/BLOCK policy
│   ├── merge_gate.py                 merge-admit preflight and checked-head landing
│   ├── reference_causality.py        reference/evidence causality checks
│   ├── link-canonical.sh             canonical-link migration with divergence refusal
│   └── install-codex-merge-rule.sh   narrow consumer-owned Codex execpolicy installer
└── tests/
    ├── README.md
    ├── run-all.sh
    ├── check-receipt/
    ├── evidence-producers/
    ├── ci-publish-gate/
    ├── merge-gate/
    ├── reference-causality/
    ├── reference-causality-integration/
    ├── link-canonical/
    └── install-codex-merge-rule/
```

`SKILL.md`, scripts, JSON contracts, and receipts remain the machine/behavior authorities. README files explain how those authorities fit together.

## Owned state machines

| State machine | Owner | Input | Output | Human boundary |
|---|---|---|---|---|
| Delivery line | `github_delivery.py` + delivery modules | artifact, registry line, receipt, publication attestation | valid/invalid line, metrics/dashboard sync | issue/PR/project creation remains admitted work |
| Local verification | `local_verification.py` | clean exact Git HEAD + fixed argv contract | local verification receipt + evidence | consumer chooses commands and accepts their meaning |
| GitHub observation | `github_actions_snapshot.py` | trusted raw `gh api` transport or replay fixture | content-addressable transport plus derived PR/check/billing snapshot | credentials and live capture authority are consumer-owned |
| CI publication | `ci_publish_gate.py` | local receipt + GitHub snapshot + intent | one `ALLOW` operation or stable `BLOCK` reason | owner recovery required for billing circuit; no generic push authority |
| Merge authority | `merge_gate.py` | owner-applied `merge-admit`, host policies, exact PR head | preflight result, provider-confirmed merge, or non-resubmitted pending state | owner label is the landing decision |
| Canonical projection | `link-canonical.sh` | canonical Skill and consumer target | symlink or divergence refusal | divergent content requires human reconciliation |
| Reference causality | `reference_causality.py` | source/ref/evidence subjects | causal validation result | promotion remains outside this script |

Full transitions and terminal states are in [`modules/state-machines.md`](modules/state-machines.md).

## End-to-end data flow

```text
small implementation loop
        │
        ├── materialized artifact
        └── implementation receipt
                │
                ▼
.github-delivery/registry.json
        │
        ├── zero-network shape/identity check
        └── trusted GitHub snapshot/sync
                │
                ├── delivery receipt
                ├── publication attestation
                ├── metrics
                └── dashboard projection
```

Private GitHub Actions publication is a separate flow:

```text
isolated Worker + local commits
        │
        ▼
fixed local verification contract
        │ exact clean HEAD
        ▼
local verification receipt
        │
trusted GitHub capture ──> PR/check/billing snapshot
        │                         │
        └──────────────┬──────────┘
                       ▼
              ci_publish_gate.py
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
ALLOW one operation             BLOCK stable reason
          │                         │
          ▼                         └── remain local; no rerun/no-op/bypass
initial draft / ready / one batched repair
          │
          ▼
GitHub exact-head check
          │
          ▼
review feedback or merge-admit
```

Merge is not a continuation of CI publication. It has its own authority stack:

```text
owner merge-admit on exact head
→ Claude/Codex host-policy preflight
→ GitHub auth/rules/checks/mergeability
→ checked-head landing request
→ merge result
```

## Macro and micro loop boundary

The implementation loop remains outside this Skill.

```text
Micro loop owns:
  task input, implementation, local tests, artifact, implementation receipt

GitHub delivery loop owns:
  tracking identity, publication evidence, CI publication decision, merge preflight

Macro / Human loop owns:
  issue decomposition, dependency graph, path leases, review, merge, promotion, rollback
```

The delivery loop never rewrites a micro-loop prompt, repairs semantic conflicts, promotes a candidate, or treats a receipt as proof without a control.

## Git Town integration

Use [`git-town-stacked-pr-worker`](../git-town-stacked-pr-worker/README.md) for branch hierarchy and bounded synchronization.

```text
issue + evals + path lease
→ one Worker / one linked worktree / one branch
→ local implementation commits
→ git town sync --stack --non-interactive --no-auto-resolve --no-push
→ exact-HEAD local verification
→ GitHub publication gate
→ PR review
→ Human Admit
```

Rules:

- Independent work is represented by sibling branches, not a fake serial stack.
- A child branch exists only when it consumes unmerged parent bytes.
- The terminal leaf is the smallest reviewable implementation PR.
- A convergence/index PR is a separate leaf after its inputs are stable.
- `git town sync` success proves only synchronization.
- Conflict, dirty tree, ancestry drift, timeout, or missing task packet stops the Worker.
- Git Town does not run `merge`, `ship`, `continue`, `skip`, `undo`, or production rollback without separate authority.

## Current Stacked PR index

This index distinguishes logical dependency from post-merge Git history. Squash/merge can flatten ancestry; PR bodies and base branches preserve the reviewed dependency graph.

### Skill-eval implementation chain

```text
#32  Skill Eval Contract v1
  ↓
#33  autoresearch-composer outcome evals
  ↓
#34  cross-harness run/evidence contracts
  ↓
#35  sealed holdouts and mutation lineage
  ↓
#36  verified-capability scorecards and unlock gates
  ↓
#39  pinned skill-up physical runtime bridge
  ↓
#42  deterministic verifier authority
  ↓
#46  draft-aware Actions cadence dogfood
```

The terminal leaf for the Actions-cadence change was PR #46. The reusable publication policy was developed separately in issue #43 and PR #44, then consumed by the workflow stack. Both policy and workflow application are now present on `main`.

### Documentation leaf

Issue #78 owns the documentation convergence represented by this branch. It is intentionally based on current `main`, not stacked under a runtime branch, because it does not consume unmerged runtime bytes. A later automated README/link checker must be a separate child issue/PR.

See [`modules/traceability-index.md`](modules/traceability-index.md) for full links and evidence states.

## Current implementation state

| Subject | State | Evidence boundary |
|---|---|---|
| Publication gate policy | `IMPLEMENTED` | issue #43 / PR #44 merged; scripts and tests present |
| Draft-aware Skill Eval workflow | `IMPLEMENTED` | PR #46 merged through the eval stack; workflow exists on `main` |
| Local verification producer | `IMPLEMENTED` | script and focused tests present |
| GitHub raw transport capture/replay | `IMPLEMENTED` | exact argv/stdout/exit/digests derive observation and snapshot; a particular live capture is environment-owned |
| Billing incident | historical observation | no-runner billing/spending event is not a test failure |
| Current account billing health | `NOT_EXERCISED` here | requires a fresh trusted snapshot |
| GitHub/Forgejo equivalence | `NOT_EXERCISED` | requires exact-commit/tree/release equivalence receipt |
| Git Town executable admission | `NOT_EXERCISED` here | consumer/host must pin and attest the binary |
| Physical skill-up/model execution | manual and environment-owned | no result is implied by deterministic contract docs |
| Merge/promotion | Human-owned | never inferred from green tests or documentation |

## Evidence semantics

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
```

A draft event that intentionally does not allocate a runner is `SKIPPED_BY_POLICY` at the workflow-policy layer, not CI `PASS`. A payment/spending event that prevents runner allocation is `NOT_EXERCISED` at the repository-test layer.

## Source-proposal boundary

The external PDF `科技巨頭開源授權與AI框架v2.pdf` proposes E2B/Firecracker runtimes, local/cloud sync, mobile automation, wallets, security controls, and cost estimates. This Skill uses none of those statements as automatic evidence. Provider admission requires independent license/spec verification and a live canary.

## Verification

```bash
bash skills/github-delivery-loop/tests/run-all.sh
python3 skills/github-delivery-loop/scripts/ci_publish_gate.py --selftest
python3 skills/github-delivery-loop/scripts/local_verification.py --selftest
python3 skills/github-delivery-loop/scripts/github_actions_snapshot.py --selftest
```

The consumer repository must additionally run its own fixed verification contract and live GitHub capture before publication.

## Change rules

- Add or update evals before changing a state transition.
- Update this README when a governed directory, state machine, or current evidence boundary changes.
- Keep consumer paths, secrets, remotes, branch names, and live receipts out of the shared body.
- Never broaden an allowlist to solve a one-repository incident.
- Never describe a source proposal, skipped workflow, old SHA, or absent receipt as current `PASS`.
