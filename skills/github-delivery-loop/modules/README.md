# `github-delivery-loop/modules/`

This directory holds explanatory mechanism contracts. These files explain why the scripts and receipts exist; they do not replace executable code, JSON schemas, `evals.json`, or GitHub/Human authority.

## Index

| Document | Owns | Primary executable |
|---|---|---|
| [`delivery-mechanism.md`](delivery-mechanism.md) | registry, receipt, publication attestation, metrics, dashboard and merge-authority model | `../scripts/github_delivery.py`, `../scripts/delivery_sync.py` |
| [`github-actions-cost-control.md`](github-actions-cost-control.md) | private-repository publication cadence, billing circuit, evidence producer boundaries, workflow pattern | `../scripts/local_verification.py`, `../scripts/github_actions_snapshot.py`, `../scripts/ci_publish_gate.py` |
| [`host-permissions.md`](host-permissions.md) | Claude/Codex/GitHub policy planes and exact repair ownership | `../scripts/merge_gate.py`, `../scripts/install-codex-merge-rule.sh` |
| [`state-machines.md`](state-machines.md) | canonical human-readable transition map across all mechanisms | all scripts |
| [`traceability-index.md`](traceability-index.md) | source → decision → issue → PR → eval → evidence navigation | none; index only |

## State-machine ownership

```text
Delivery-line state machine
  delivery-mechanism.md

Local verification + GitHub observation + CI publication state machines
  github-actions-cost-control.md

Merge authority state machine
  delivery-mechanism.md + host-permissions.md

Git Town Worker state machine
  ../git-town-stacked-pr-worker/README.md

Integrated overview
  state-machines.md
```

## Documentation laws

- The script and schema define exact accepted fields and exit codes.
- The module document explains intent, actors, transitions, and forbidden shortcuts.
- The README links the mechanism into the directory and PR graph.
- An issue/PR defines one admitted change and its evals.
- A receipt records one observation; it does not rewrite the mechanism contract.
- Human Admit owns merge, permission widening, provider recovery, legal acceptance, promotion, and production rollback.

## Evidence states

Use these labels without substitution:

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
```

A module may describe a planned provider or workflow. Unless the repository contains the mechanism and a subject-bound execution receipt, its live state remains `NOT_IMPLEMENTED` or `NOT_EXERCISED`.

## Source material

The external PDF `科技巨頭開源授權與AI框架v2.pdf` is tracked as a source proposal. Its runtime, synchronization, mobile, wallet, security, license, latency, and cost claims must be independently verified before admission. This directory preserves the distinction between source proposal, repository decision, implementation mechanism, and live evidence.

## Change checklist

When adding or changing a module document:

1. name the state machine and owner;
2. identify inputs, outputs, effects, network boundary, and terminal states;
3. point to the executable and tests;
4. add positive and negative evals before implementation;
5. update [`state-machines.md`](state-machines.md) if a transition changes;
6. update [`traceability-index.md`](traceability-index.md) if an issue/PR/evidence relation changes;
7. keep consumer paths, secrets, branch names, and live receipts outside the shared document.
