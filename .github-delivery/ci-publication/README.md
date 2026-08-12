# skills-shared private GitHub publication profile

This directory is the repository-owned consumer configuration for the shared `github-delivery-loop` publication policy.

## Ownership

```text
skills/github-delivery-loop/
  owns: portable producers, publication decision policy, schemas and reusable tests

.github-delivery/ci-publication/
  owns: skills-shared repository identity, stable check name, fixed local commands and runtime-output location

trusted operator
  owns: GitHub capture credentials, billing recovery, PR ready transition, push and merge
```

Do not copy the shared Skill into this directory. Do not commit live observations, verification receipts, recovery receipts, tokens, check logs or machine-specific paths.

## Data flow

```text
clean exact local HEAD
  → local-verification.contract.json
  → local_verification.py
  → runtime/local-verification.{receipt,evidence}.json

trusted GitHub read lane
  → github_actions_snapshot.py capture
  → runtime/github-observation.json
  → runtime/github-state.snapshot.json

receipt + snapshot + intent
  → ci_publish_gate.py evaluate
  → ALLOW one publication boundary or BLOCK
```

## Fixed profile

[`profile.json`](profile.json) binds repository ID `1326262274`, the stable check name `contract`, the three admitted intents, the local verification contract and the billing circuit policy. Validate it before producing evidence:

```bash
python3 .github-delivery/ci-publication/scripts/check_profile.py
python3 .github-delivery/ci-publication/scripts/check_profile.py --selftest
```

## Produce local evidence

```bash
mkdir -p .github-delivery/ci-publication/runtime
python3 skills/github-delivery-loop/scripts/local_verification.py verify \
  --repo-root . \
  --contract .github-delivery/ci-publication/local-verification.contract.json \
  --repository-id 1326262274 \
  --receipt .github-delivery/ci-publication/runtime/local-verification.receipt.json \
  --evidence .github-delivery/ci-publication/runtime/local-verification.evidence.json
```

The working tree must be clean. The output directory is ignored. A PASS receipt authorizes nothing by itself.

## Capture GitHub state

Only a trusted network lane may run:

```bash
python3 skills/github-delivery-loop/scripts/github_actions_snapshot.py capture \
  --repository ed3c/skills-shared \
  --branch <HEAD_BRANCH> \
  --check-name contract \
  --observation-output .github-delivery/ci-publication/runtime/github-observation.json \
  --output .github-delivery/ci-publication/runtime/github-state.snapshot.json
```

Capture is read-only. Replay is zero-network. Multiple PRs, stale checks, public-repository state and unknown observations fail closed.

## Decide publication

```bash
python3 skills/github-delivery-loop/scripts/ci_publish_gate.py evaluate \
  --repo-root . \
  --snapshot .github-delivery/ci-publication/runtime/github-state.snapshot.json \
  --verification .github-delivery/ci-publication/runtime/local-verification.receipt.json \
  --intent ready-for-review \
  --json
```

The detailed sidecar is produced and retained for audit. Mandatory gate-side recomputation of that sidecar is tracked separately; until it lands, compact-receipt-to-sidecar binding is `NOT_IMPLEMENTED`, not silently assumed.

## Evidence boundary

- Draft local commits and `git town sync --no-push` do not request GitHub runners.
- `billing-open` blocks push, rerun and no-op commit until an owner recovery receipt exists.
- A recovery receipt permits one later attempt; it does not prove billing or runner availability.
- GitHub-hosted exact-head execution, Forgejo equivalence, merge and release remain separate evidence lanes.
