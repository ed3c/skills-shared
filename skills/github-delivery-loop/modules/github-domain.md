# GitHub domain adapter

This module instantiates the forge-neutral `DL-01..DL-09` procedure from `../SKILL.md` for GitHub. GitHub-specific objects are domain bindings, not portable law.

## Domain mapping

| Portable atom | GitHub instance | Executable owner |
|---|---|---|
| `DL-01 INTENT_BOUND` | PRD/slice issue, PR scope, publication intent | `../scripts/github_delivery.py`, issue/PR contract |
| `DL-02 SUBJECT_BOUND` | repository ID, exact commit/tree, exact PR head | `../scripts/local_verification.py`, `../scripts/github_actions_snapshot.py` |
| `DL-03 EVIDENCE_CONTRACT_BOUND` | local verification contract, required checks, planted controls | `../scripts/local_verification.py`, `../tests/` |
| `DL-04 LOCAL_VERIFICATION` | exact-HEAD local command receipts | `../scripts/local_verification.py` |
| `DL-05 PUBLICATION_ADMISSION` | `initial-pr`, `ready-for-review`, `batched-repair` admission | `../scripts/ci_publish_gate.py` |
| `DL-06 REMOTE_PUBLICATION` | exact SHA push / PR create-or-ready / bounded workflow dispatch | `../scripts/ci_publish.py`, `../scripts/ci_publish_guard.py` |
| `DL-07 REMOTE_REOBSERVATION` | PR head, check run, workflow/job state, branch existence readback | `../scripts/github_actions_snapshot.py`, `../scripts/delivery_sync.py` |
| `DL-08 INTEGRATION_ADMISSION` | merge authority + exact reviewed head + required checks | `../scripts/merge_gate.py` |
| `DL-09 TERMINAL_RECEIPT` | delivery receipt / publication snapshot / merge readback | `../scripts/github_delivery.py`, `../scripts/merge_gate.py` |

## GitHub-specific invariants

These are domain rules and must not be copied into the forge-neutral bounded core.

- A PR lookup does not prove that a remote branch exists or does not exist; inspect the exact branch ref when that fact is load-bearing.
- A workflow definition is not a workflow execution receipt.
- A successful local verification receipt is not a GitHub check.
- A GitHub Actions provider/billing no-runner state is neither repository `PASS` nor repository `FAIL`.
- Do not create no-op commits or repeated reruns to probe a provider circuit.
- Merge authority is layered: repository/Human or bounded owner policy, host tool policy, GitHub state, then the merge operation itself.
- An accepted merge API/CLI request is not `LANDED`; re-read the PR and exact head until the merged state is observed.
- Existing private-repository publication controls must keep local commit cadence independent from remote Actions cadence.

## Specialist modules

- [`ci-publication.md`](ci-publication.md): publication intent and exact-head private-repository path.
- [`github-actions-cost-control.md`](github-actions-cost-control.md): Actions/provider circuit, evidence producers, and remote-cost controls.
- [`host-permissions.md`](host-permissions.md): Claude/Codex/GitHub permission and hook planes.
- [`commit-role.md`](commit-role.md): commit driver/host identity and trailers.
- [`delivery-mechanism.md`](delivery-mechanism.md): registry, receipt, metrics, dashboard, and merge authority model.

## Evidence boundary

This module can establish GitHub-specific mechanism or live GitHub evidence only when the corresponding executable actually runs on the bound subject. It cannot proxy Forgejo, another CI provider, a local Agent host, production deployment, or Human release authority.
