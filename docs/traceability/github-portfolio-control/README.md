# github-portfolio-control — epoch PORTFOLIO-EPOCH-20260822-B receipts

This directory is the durable Local Handoff receipt set for the #560 Repository
Portfolio Control program (queue #566/#567/#568/#569/#559/#570), produced on the
convergence branch that landed the queue. Machine truth stays in the JSON files;
this README only routes.

## Subject binding

Base main `28f394785aa8b13c4e6d2f21ad74c5e32a6a6dc5` (tree `8343d988…`).
Frozen contract plane: `skills/github-portfolio-control` at tree
`795de8e9ada4d0927f9a792760232ef75dda84e4`. Portfolio-core (#566) candidate
`aad3ff0728b9519615b63be80c225389005bfc1d`, an ancestor of this branch.

## Files

| File | What it is | Validated by |
|---|---|---|
| `epoch.json` | snapshot-epoch manifest: runtime delta (CODEX_CLI_LOCAL → CLAUDE_CODE_LOCAL, Human-admitted, itemized), model-alias table, local writer map, superseded epoch A delta | prose ledger; subjects re-derivable by `git rev-parse` |
| `decisions.json` | Tech Lead decision ledger: typed deltas (BASE_MAIN_DRIFT, ACCEPTANCE_SURFACE_DELTA, provenance-premise falsification), foundation adoption (PR #562 compiler line + PR #564 acceptance line, composed with ghpc), supersession set, hard constraints, B1 verification record, publication shape | prose ledger |
| `snapshot.json` | real repository-portfolio-snapshot: 7 issues + 9 PRs, one epoch | `scripts/assert_repository_portfolio_snapshot.py` |
| `acceptance.json` | 16 real issue-pr-acceptance packets (typed dependency edges) | `scripts/assert_issue_pr_acceptance.py` per packet |
| `multigraph.json` | compiled G1–G7 + 8 ready waves over the 16 units | `scripts/assert_portfolio_multigraph.py` |
| `l2-join-receipt.json` | #567 subagent join denominator: 27 requested agents — 20 Claude-carrier exercised, 1 Codex-carrier (codex-cli 0.148.0, self-reported model "GPT-5", read-only) exercised, 6 Codex-carrier AVAILABLE_NOT_EXERCISED | `jsonschema` against `ghpc/subagent-join/v1` |
| `l2-codex-result.json` | the raw Codex CLI exercise result and identity receipts | cross-checked against candidate refs |
| `validation-report.txt` | exact commands + exit codes (20/20 exit 0) and 5 decision-vs-checker tensions | itself |

Checker scripts live in `skills/agentic-tech-lead-orchestration/scripts/`; the
join/one-shot-CI contract shapes live in `skills/github-portfolio-control` and
are composed, not duplicated (see the authority table in
`skills/agentic-tech-lead-orchestration/references/REPOSITORY_PORTFOLIO_CONTROL.md`).

## Evidence ceilings (honest boundaries)

- Everything here is DETERMINISTIC/SANDBOX-lane evidence. Hosted CI, merge,
  exact-main readback and issue closure are later-stage subjects with their own
  receipts; a green file here cannot raise those lanes.
- Claude-carrier read-only enforcement is `PROMPT_ONLY` (no tool-lockdown
  receipt). Codex lanes beyond the one release-auditor run are
  `AVAILABLE_NOT_EXERCISED`, never `ABSENT` (binary present at 0.148.0).
- Copied-body refusal in the #559 bootstrap is whole-file byte containment;
  partial copies pass (recorded ceiling). The bootstrap pin gate asserts
  literal SHAs before deriving ancestry; re-pinning edits its test in lockstep.
- `shared-skills-infra/tests/control-plane/verify.sh` is red in local
  single-branch clones on the authoring machine for both `main` and this
  branch (one-variable control, 2026-08-22): environmental, not a regression;
  pristine CI runners are the authority for that lane.
