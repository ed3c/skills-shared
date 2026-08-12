# Exact remote branch proof for initial publication

An absent open Pull Request does not prove that the GitHub branch is absent. A remote branch may have been pushed earlier, orphaned after a PR was closed, or created by another Worker. Treating those states as the same would admit repeated `initial-pr` publication.

`github_actions_snapshot_strict.py` adds an independent read-only query for:

```text
refs/heads/<exact branch>
```

before it delegates PR/check/billing normalization to `github_actions_snapshot.py`.

## Allowed state pairs

| Exact remote ref | Open PR | Result |
|---|---|---|
| absent | absent | trusted initial-publication boundary |
| present | one PR at the same SHA | draft/ready snapshot |
| present | absent | BLOCK: remote branch exists without PR |
| absent | one PR | BLOCK: PR cannot be tied to selected branch ref |
| present | PR at a different SHA | BLOCK: ref/PR disagreement |
| any | multiple PRs | BLOCK: ambiguous identity |

## Capture

```bash
python3 skills/github-delivery-loop/scripts/github_actions_snapshot_strict.py capture \
  --repository OWNER/REPO \
  --branch feature/branch \
  --check-name contract \
  --observation-output runtime/github-observation.json \
  --output runtime/github-state.snapshot.json
```

The branch name is URL-encoded for the exact Git-ref API. HTTP 404 means the ref is absent; other API failures remain `FATAL`, not absence. The command is read-only and cannot push, rerun, transition, merge, change billing, or change permissions.

## Replay

```bash
python3 skills/github-delivery-loop/scripts/github_actions_snapshot_strict.py replay \
  --observation runtime/github-observation.json \
  --check-name contract \
  --output runtime/github-state.snapshot.json
```

Replay is zero-network and re-applies the exact branch/PR invariants. A hand-edited observation that changes branch state, PR head, check head or billing annotation must turn red.

## Consumer rule

A private-repository publication profile must point to the strict producer before `initial-pr` is admitted. The v1 producer remains the normalization module; it is not enough by itself to prove remote non-publication.
