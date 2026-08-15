# CI publication profile

This repository publishes itself through `github-delivery-loop`, so it owns the
same inputs any consumer owns. This directory contains the profile plus a
non-executable compatibility route; the executable contract has one canonical
path in the parent directory:

| file | owns |
|---|---|
| [`profile.json`](profile.json) | immutable repository id, stable check identity, the exact publication intents, the billing stop rule, and where receipts land |
| [`verification-contract.json`](verification-contract.json) | route-only pointer; never pass this file to a verifier |
| [`../local-verification-contract.json`](../local-verification-contract.json) | the single executable argv-array contract used by both profile and live publish policy |

`ci-policy.json` in the parent directory seals workflow triggers and the live
publish route. The profile checker requires their overlapping repository,
workflow, check, and contract identities to agree exactly.

## Commands

Local verification receipt and its evidence sidecar, zero network, exact clean
HEAD required:

```bash
python3 skills/github-delivery-loop/scripts/local_verification.py verify \
  --repo-root . \
  --contract .github-delivery/local-verification-contract.json \
  --repository-id 1326262274 \
  --receipt .git/github-delivery/local-verification.json \
  --evidence .git/github-delivery/local-verification-evidence.json
```

Provider-bound GitHub snapshot. `capture` is the only step that touches the
network and it preserves the raw transport. `replay-transport` re-derives the
observation and snapshot from that transport without network access. Plain
`replay` accepts an already-derived observation and is only a local diagnostic;
it is not provider provenance:

```bash
python3 skills/github-delivery-loop/scripts/github_actions_snapshot.py capture \
  --repository ed3c/skills-shared --branch <branch> --check-name contract --strict \
  --transport-output .git/github-delivery/github-state.transport.json \
  --observation-output .git/github-delivery/github-state.observation.json \
  --output .git/github-delivery/github-state.snapshot.json

python3 skills/github-delivery-loop/scripts/github_actions_snapshot.py replay-transport \
  --transport .git/github-delivery/github-state.transport.json --strict \
  --observation-output .git/github-delivery/github-state.observation.json \
  --output .git/github-delivery/github-state.snapshot.json
```

Publication decision:

```bash
python3 skills/github-delivery-loop/scripts/ci_publish_gate.py evaluate \
  --repo-root . \
  --snapshot .git/github-delivery/github-state.snapshot.json \
  --verification .git/github-delivery/local-verification.json \
  --evidence .git/github-delivery/local-verification-evidence.json \
  --verification-contract .github-delivery/local-verification-contract.json \
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
