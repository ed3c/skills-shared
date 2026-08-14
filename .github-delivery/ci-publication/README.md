# CI publication profile

This repository publishes itself through `github-delivery-loop`, so it owns the
same inputs any consumer owns. Two files, and nothing else:

| file | owns |
|---|---|
| [`profile.json`](profile.json) | immutable repository id, stable check identity, the exact publication intents, the billing stop rule, and where receipts land |
| [`verification-contract.json`](verification-contract.json) | the fixed argv-array local checks, each with an explicit time and output budget |

`ci-policy.json` in the parent directory is a different concern: it seals the
workflow triggers and names the command the publish path runs. This profile is
what the *gate* reads. Neither restates the other.

## Commands

Local verification receipt and its evidence sidecar, zero network, exact clean
HEAD required:

```bash
python3 skills/github-delivery-loop/scripts/local_verification.py verify \
  --repo-root . \
  --contract .github-delivery/ci-publication/verification-contract.json \
  --repository-id 1326262274 \
  --receipt .git/github-delivery/local-verification.json \
  --evidence .git/github-delivery/local-verification-evidence.json
```

Trusted GitHub snapshot. `capture` is the only step that touches the network;
`replay` reads a captured observation and touches nothing:

```bash
python3 skills/github-delivery-loop/scripts/github_actions_snapshot.py capture \
  --repo ed3c/skills-shared --branch <branch> --check-name contract --strict \
  --output .git/github-delivery/github-state.snapshot.json

python3 skills/github-delivery-loop/scripts/github_actions_snapshot.py replay \
  --observation <observation.json> --check-name contract --strict \
  --output .git/github-delivery/github-state.snapshot.json
```

Publication decision:

```bash
python3 skills/github-delivery-loop/scripts/ci_publish_gate.py evaluate \
  --repo-root . \
  --snapshot .git/github-delivery/github-state.snapshot.json \
  --verification .git/github-delivery/local-verification.json \
  --verification-evidence .git/github-delivery/local-verification-evidence.json \
  --intent ready-for-review \
  --json
```

## What this profile refuses

`scripts/check_ci_publication_profile.py` decides all of it offline, and its
`--selftest` plants each shape and requires a refusal that names which one:

- a repository id that is not the immutable numeric id, or one that disagrees
  between the profile and the contract;
- a check name that is a template, or that names no job in the owning workflow —
  a name nothing answers to produces no check run, and an absent check run reads
  as an absent blocker rather than as a missing observation;
- a fourth publication intent, or a missing one;
- `billing-open` configured to rerun or continue rather than stop;
- `bash -c` or any shell string where an argument vector belongs;
- an inherited environment name outside the admitted set;
- a machine-local absolute path in either file;
- a receipt path that is neither under `.git/` nor ignored, which would commit an
  observation as if it were configuration;
- a live receipt, evidence, snapshot, observation or recovery document committed
  anywhere under `.github-delivery/`.

## What is produced, never committed

Everything in `profile.json`'s `generated_paths` lives under `.git/`. Receipts,
evidence sidecars, snapshots, observations, billing recovery documents and
tokens are produced by a run and belong to that run. A committed one describes a
commit that is no longer HEAD, and a stale receipt that looks current is worse
than no receipt.
