# dual-forge-repository-loop

Portable orchestration for a private GitHub repository plus a local Forgejo implementation plane.

## Data flow

```text
ChatGPT iOS/macOS or other GitHub-connected host
        ↓ GitHub private repo + issues/PRs + remote main SHA
GitHub ingress snapshot
        ↓
local checkout + Forgejo mirror
        ↓
Forgejo issues
        ↓
isolated worktrees / one writer
        ↓
verification + negative controls
        ↓
Forgejo PRs
        ↓
LOCAL MAIN
        ↓
re-fetch GitHub main + enumerate open GitHub PRs/issues
        ↓
ancestry/conflict/issue reconciliation
        ↓
publication candidate
        ↓
GitHub Actions exact-head verification
        ↓
GitHub issue/PR publication
        ↓
repository merge policy / Human Admit
```

## Authority map

| Plane | Authority | Not authority for |
|---|---|---|
| GitHub connector/app | private-repo ingress, issues/PR metadata and allowed mutations | local Forgejo state, local test execution |
| GitHub Actions | remote CI evidence for exact head | local implementation history, semantic merge correctness |
| Local checkout | Git object integration and local main | remote GitHub publication state |
| Forgejo | local implementation issues/PR receipts | GitHub issue/PR identity or Actions truth |
| Worktree | one issue/branch writer | global main or another worker branch |

## Documents

- [`SKILL.md`](SKILL.md): procedure and hard laws.
- [`references/system-prompt.md`](references/system-prompt.md): project-level agent instruction.
- [`references/repo-binding.template.json`](references/repo-binding.template.json): repo-owned binding/receipt shape.
- [`scripts/check_dual_forge_contract.py`](scripts/check_dual_forge_contract.py): deterministic publication-order checker.
- [`scripts/export_git_proof.py`](scripts/export_git_proof.py): canonical four-ref Git ancestry/tree proof producer.
- [`scripts/capture_origin_ref.py`](scripts/capture_origin_ref.py): canonical GitHub API, authenticated loopback Forgejo API, and local Git default-ref observation producer.
- [`evals.json`](evals.json), [`tests/`](tests/): positive and planted-negative controls.

## Evidence boundary

```text
portable orchestration contract     IMPLEMENTED
deterministic publication gate      IMPLEMENTED
positive/mutation controls          IMPLEMENTED
canonical Git proof export/replay   IMPLEMENTED
ChatGPT private-GitHub ingress       NOT_EXERCISED by this Skill's tests
local Forgejo mutation              NOT_EXERCISED
real consumer worktree integration  NOT_EXERCISED
consumer GitHub Actions             NOT_EXERCISED
final merge                         HUMAN_ADMIT_REQUIRED
```

The machine checker treats an empty or partial history as a draft receipt:
`NOT_EXERCISED`, exit `3`. Only the complete publication-ready history can
return `PASS`; a legal state-name prefix is not evidence that its transitions ran.
