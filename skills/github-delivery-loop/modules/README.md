# `github-delivery-loop/modules/`

This directory owns domain adapters and explanatory mechanism contracts. The portable delivery procedure lives in `../SKILL.md`; modules instantiate it for a forge, CI provider, Agent host, commit policy, or evidence surface. Module prose never replaces executable code, schemas, evals, or external authority.

## Domain-decoupling rule

```text
SKILL.md
  portable procedure atoms + hard laws + evidence states

modules/
  forge/provider/host/domain bindings

scripts/ + tests/
  executable enforcement and falsifying controls
```

A module may map a domain onto `DL-01..DL-09`; it may not redefine those atoms or push provider-specific facts back into the portable core.

## Index

| Document | Domain / mechanism ownership | Primary executable |
|---|---|---|
| [`github-domain.md`](github-domain.md) | GitHub repository, PR, check, Actions and merge-domain mapping onto `DL-01..DL-09` | `../scripts/github_delivery.py`, `../scripts/local_verification.py`, `../scripts/github_actions_snapshot.py`, `../scripts/ci_publish_gate.py`, `../scripts/ci_publish.py`, `../scripts/merge_gate.py` |
| [`ci-publication.md`](ci-publication.md) | exact-HEAD private-repository verification and controlled publication boundary | `../scripts/ci_publish.py`, `../scripts/ci_publish_guard.py` |
| [`commit-role.md`](commit-role.md) | commit driver/host trailers and machine identity separation | `../../../scripts/check_commit_roles.py` |
| [`delivery-mechanism.md`](delivery-mechanism.md) | registry, receipt, publication attestation, metrics, dashboard and merge-authority model | `../scripts/github_delivery.py`, `../scripts/delivery_sync.py` |
| [`github-actions-cost-control.md`](github-actions-cost-control.md) | GitHub Actions publication cadence, provider circuit, evidence-producer boundaries | `../scripts/local_verification.py`, `../scripts/github_actions_snapshot.py`, `../scripts/ci_publish_gate.py` |
| [`host-permissions.md`](host-permissions.md) | Claude/Codex/GitHub policy planes and exact repair ownership | `../scripts/merge_gate.py`, `../scripts/install-codex-merge-rule.sh` |
| [`state-machines.md`](state-machines.md) | canonical human-readable transition map across mechanisms | all scripts |
| [`traceability-index.md`](traceability-index.md) | source → decision → issue → PR → eval → evidence navigation | none; index only |

## Portable-core assertion

The domain boundary is executable, not only editorial:

```bash
python3 skills/github-delivery-loop/scripts/check_procedural_core.py \
  --root skills/github-delivery-loop
```

The checker asserts that all portable atoms/hard laws remain present, each hard law has an executable assertion, GitHub-domain tokens do not leak into the bounded portable core, and the GitHub adapter maps every procedure atom to an executable owner. Planted controls live in `../tests/procedural-core/verify.sh`.

## State-machine ownership

```text
Portable delivery state machine
  ../SKILL.md (DL-01..DL-09)

GitHub domain instantiation
  github-domain.md

Delivery-line registry/receipt mechanics
  delivery-mechanism.md

Local verification + GitHub observation + CI publication
  github-actions-cost-control.md + ci-publication.md

Merge authority
  delivery-mechanism.md + host-permissions.md

Integrated overview
  state-machines.md
```

## Documentation laws

- `SKILL.md` defines the reusable procedure and evidence laws.
- A domain module binds those laws to provider/forge/host objects.
- Scripts and schemas define exact accepted fields, effects, and exit codes.
- Tests must include positive and falsifying controls for load-bearing invariants.
- An issue/PR defines one admitted change and its eval scope.
- A receipt records one observation; it does not rewrite the method.
- Merge, permission widening, provider recovery, legal acceptance, release promotion, and production rollback remain external authority unless a separate bounded policy explicitly delegates them.

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

A module may describe a planned provider or workflow. Without the mechanism and subject-bound execution receipt, the live state stays `NOT_IMPLEMENTED` or `NOT_EXERCISED`.

## Change checklist

When adding or changing a module:

1. identify which `DL-01..DL-09` atoms it instantiates;
2. name inputs, outputs, effects, network boundary, and terminal states;
3. point to executable owners and tests;
4. add positive and negative evals before changing a load-bearing mechanism;
5. update `state-machines.md` when transitions change;
6. update `traceability-index.md` when evidence lineage changes;
7. keep consumer paths, credentials, mutable branch state, and live receipts outside portable procedure text;
8. run `scripts/check_procedural_core.py` and the complete Skill suite.
