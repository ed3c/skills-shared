# skills-shared private GitHub publication profile

This directory is the repository-owned consumer configuration for the shared `github-delivery-loop` publication policy.

## Ownership

```text
skills/github-delivery-loop/
  owns: portable evidence producers, strict publication decision entrypoint,
        billing circuit, schemas and reusable tests

.github-delivery/ci-publication/
  owns: skills-shared repository identity, stable check name, fixed local
        commands, publication profile and runtime-output location

trusted operator
  owns: GitHub capture credentials, owner recovery receipt, PR ready
        transition, admitted push, Human Admit and merge
```

Do not copy the shared Skill into this directory. Do not commit live observations, verification receipts, evidence sidecars, recovery receipts, tokens, check logs or machine-specific paths.

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

snapshot + compact receipt + detailed sidecar + intent
  → ci_publish_admitted.py evaluate
  → ALLOW one publication boundary or BLOCK
```

## Validate configuration

[`profile.json`](profile.json) binds repository ID `1326262274`, stable check name `contract`, the three admitted intents, exact entrypoints, billing behavior and evidence states.

```bash
python3 .github-delivery/ci-publication/scripts/check_profile.py
python3 .github-delivery/ci-publication/scripts/check_profile.py --selftest
```

## Produce exact-HEAD local evidence

```bash
mkdir -p .github-delivery/ci-publication/runtime
python3 skills/github-delivery-loop/scripts/local_verification.py verify \
  --repo-root . \
  --contract .github-delivery/ci-publication/local-verification.contract.json \
  --repository-id 1326262274 \
  --receipt .github-delivery/ci-publication/runtime/local-verification.receipt.json \
  --evidence .github-delivery/ci-publication/runtime/local-verification.evidence.json
```

The worktree must be clean. The producer executes fixed argv arrays without a shell and emits bounded content-addressed evidence. A local PASS receipt authorizes nothing by itself.

## Capture or replay GitHub state

Trusted read-only capture:

```bash
python3 skills/github-delivery-loop/scripts/github_actions_snapshot.py capture \
  --repository ed3c/skills-shared \
  --branch <HEAD_BRANCH> \
  --check-name contract \
  --observation-output .github-delivery/ci-publication/runtime/github-observation.json \
  --output .github-delivery/ci-publication/runtime/github-state.snapshot.json
```

Zero-network replay:

```bash
python3 skills/github-delivery-loop/scripts/github_actions_snapshot.py replay \
  --observation .github-delivery/ci-publication/runtime/github-observation.json \
  --check-name contract \
  --output .github-delivery/ci-publication/runtime/github-state.snapshot.json
```

Multiple open PRs, stale/incomplete checks, public-repository state, malformed annotations and remote-branch-without-PR ambiguity fail closed.

## Decide one publication boundary

```bash
python3 skills/github-delivery-loop/scripts/ci_publish_admitted.py evaluate \
  --repo-root . \
  --snapshot .github-delivery/ci-publication/runtime/github-state.snapshot.json \
  --verification .github-delivery/ci-publication/runtime/local-verification.receipt.json \
  --verification-evidence .github-delivery/ci-publication/runtime/local-verification.evidence.json \
  --intent ready-for-review \
  --json
```

The admitted entrypoint validates compact receipt shape, recomputes sidecar digests, binds repository ID/HEAD/tree and only then evaluates publication intent and billing policy. It returns a decision; it never performs the operation.

## Evidence boundary

- Draft local commits and `git town sync --no-push` do not request GitHub runners.
- Only `initial-pr`, `ready-for-review`, or one feedback-bound `batched-repair` can be admitted.
- `billing-open` blocks push, rerun and no-op commit until an owner recovery receipt exists.
- Recovery permits one later attempt; it does not prove billing or runner availability.
- Runtime evidence is ignored and untracked.
- GitHub-hosted exact-head execution, GitHub/Forgejo equivalence, Human Admit and merge remain separate evidence lanes.
