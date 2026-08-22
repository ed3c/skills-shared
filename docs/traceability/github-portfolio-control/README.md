# github-portfolio-control — epoch PORTFOLIO-EPOCH-20260822-B receipts

This directory is the durable Local Handoff receipt set for the #560 Repository
Portfolio Control program (queue #566/#567/#568/#569/#559/#570), produced on the
convergence branch that landed the queue. Machine truth stays in the JSON files;
this README only routes.

**Every JSON file here is a frozen dated observation of epoch
`PORTFOLIO-EPOCH-20260822-B` (`observed_at` 2026-08-22T00:00:00Z), not a claim
about the current repository.** Its issue/PR state rows were superseded the same
day; the later readback is recorded below under
[2026-08-22 post-convergence readback](#2026-08-22-post-convergence-readback).
Read the rows with their epoch, and do not rewrite them — a dated snapshot is
evidence only while it stays dated.

## Subject binding

Base main `28f394785aa8b13c4e6d2f21ad74c5e32a6a6dc5` (tree `8343d988…`).
Frozen contract plane: `skills/github-portfolio-control` at tree
`795de8e9ada4d0927f9a792760232ef75dda84e4`. Portfolio-core (#566) candidate
`aad3ff0728b9519615b63be80c225389005bfc1d`, an ancestor of this branch.

## 2026-08-22 post-convergence readback

This section is the human-readable half of the observation refresh that
`epoch.json` (`superseded_epochs[0].issue_state_skew`) asked for. The
machine-readable half is `epoch.json` → `observation_refresh`: the same 16-unit
readback as typed rows, each carrying its own `evidence_grade` so a direct
provider readback never blurs into one derived from denominator absence. Read
that block, not this prose, when you need the rows. Both refresh the
**observation** lane only; publication, merge and issue closure remain their own
later-stage subjects.

**Source and window.** Frozen `gh` dumps taken during the DTCR handoff-queue
convergence between 2026-08-22T05:22Z and 2026-08-22T06:02Z, plus local `git`
object facts. This is a *composed* readback across a ~40-minute window, not a
single-instant epoch — which is exactly why it is recorded as dated prose rather
than compiled into an epoch-C `snapshot.json`: the snapshot contract's
`MIXED_SNAPSHOT_EPOCH` bound (300 s) is designed to refuse a window this wide,
and a fresh `acceptance.json` would have to invent acceptance semantics no
source supplies. A future publication epoch needs one single-instant readback of
issues + PRs + workflows before an epoch-C snapshot may be compiled.

**Denominator scope (do not widen).** The 16 units audited here are exactly the
`epoch.json` `scope` line — issues 560/566/559/567/568/569/570 and PRs
565/564/562/450/420/419/412/396/395 of the #560 Local Handoff Execution Queue.
They are **not** a repository-wide denominator: the same readback shows 65 open
issues in `ed3c/skills-shared`, none of which this receipt set audits. A reader
who needs repository-wide state must compile it elsewhere.

**Current main.** `5341885f26b5e8e7baf5087a4d661e324f878242`, tree
`a18e12507f9e621efd5354f58384eded1f1e2a9a`. Epoch B's base `28f3947` is two
first-parent merges behind it (`9fe3c6d` = PR #573, `5341885` = PR #574; 158
commits total).

**Tracked issues.** All seven are closed. `#559/#560/#566/#567/#568` were read
back individually as `CLOSED` with `stateReason: COMPLETED`; `#569/#570` are
absent from the complete 65-number open-issue denominator, so their closure is
derived and their `stateReason` was **not** read. Every `"state": "OPEN"` row in
`snapshot.json` and every `"observed_state": "OPEN"` in `acceptance.json` is
therefore epoch-B history.

**Tracked pull requests.** No tracked PR is open.

| PR | Readback state | Byte fate against admitted main `5341885f` |
|---|---|---|
| `#395` | MERGED | head `d411d2a9…` is an ancestor |
| `#396` `#412` `#419` `#420` `#450` | CLOSED, not merged | each head (`98a6c53c…`, `01067581…`, `94426cee…`, `206ee94f…`, `6f0a96f4…`) is an ancestor: the bytes landed by replay, not by merging the PR |
| `#562` `#564` `#565` | not open; **merged-vs-closed distinction NOT read** | heads `caedeb9e…`, `efb224dd…`, `bcafebe3…` are **not** ancestors — no merged-bytes claim is available for them. `decisions.json` `supersessions_at_publication` planned `close SUPERSEDED` for all three and `foundation_adoption.salvage_plan` records their compiler/acceptance lines being absorbed into #566; the provider terminal itself was not read back |

**Open-PR set at readback.** `{#577}` — draft `agent/dtcr-handoff-audit`, head
`bca08001…` (admitted main is its ancestor), consumed by the DTCR handoff-queue
convergence. Nothing else in `ed3c/skills-shared` was open.

**Disclosed divergence from the plan (PR #395).** `acceptance.json`'s `PR-395`
packet allows only the terminal `CONSUMED_BY_CONVERGENCE`; the real outcome was
a GitHub merge. `skills/agentic-tech-lead-orchestration/references/closure-audit/issue-568.json`
already records it as `merged: true` / `HISTORICAL` ("395 auto-merged by
reachability"). The acceptance packet is left as the frozen plan it was; the
closure packet is the outcome authority.

## Files

| File | What it is | Validated by |
|---|---|---|
| `epoch.json` | snapshot-epoch manifest: runtime delta (CODEX_CLI_LOCAL → CLAUDE_CODE_LOCAL, Human-admitted, itemized), model-alias table, local writer map, superseded epoch A delta, and the dated `observation_refresh` block (2026-08-22 readback of all 16 units, with per-row `evidence_grade`) | prose ledger; subjects re-derivable by `git rev-parse`, ancestry rows by `git merge-base --is-ancestor` |
| `decisions.json` | Tech Lead decision ledger: typed deltas (BASE_MAIN_DRIFT, ACCEPTANCE_SURFACE_DELTA, provenance-premise falsification), foundation adoption (PR #562 compiler line + PR #564 acceptance line, composed with ghpc), supersession set, hard constraints, B1 verification record, publication shape | prose ledger |
| `snapshot.json` | real repository-portfolio-snapshot: 7 issues + 9 PRs, one epoch | `scripts/assert_repository_portfolio_snapshot.py` |
| `acceptance.json` | 16 real issue-pr-acceptance packets (typed dependency edges) | `scripts/assert_issue_pr_acceptance.py` per packet |
| `multigraph.json` | compiled G1–G7 + 8 ready waves over the 16 units | `scripts/assert_portfolio_multigraph.py` |
| `l2-join-receipt.json` | #567 subagent join denominator: 27 requested agents — 20 Claude-carrier exercised, 1 Codex-carrier (codex-cli 0.148.0, self-reported model "GPT-5", read-only) exercised, 6 Codex-carrier AVAILABLE_NOT_EXERCISED | `jsonschema` against `ghpc/subagent-join/v1` |
| `l2-codex-result.json` | the raw Codex CLI exercise result and identity receipts | cross-checked against candidate refs |
| `validation-report.txt` | exact commands + exit codes (20/20 exit 0, deterministic lane; carries 5 disclosed decision-vs-checker tensions — read them with the number) | itself |
| `one-shot-ci-epochs.json` | the real hosted epochs: epoch 1 CODE_FAILURE (body-neutrality) honestly closed, epoch 2 green 23/23, single Ready toggle, match-head merge, exact-main readback 9fe3c6d | ghpc/one-shot-ci-epoch/v1 vocabulary |

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
- The issue/PR state rows in `snapshot.json` and `acceptance.json` are epoch-B
  observations, superseded the same day by the
  [2026-08-22 post-convergence readback](#2026-08-22-post-convergence-readback)
  and its typed form in `epoch.json` → `observation_refresh`. No checker in this
  repository re-reads provider state, so a green
  `assert_repository_portfolio_snapshot.py` / `assert_issue_pr_acceptance.py`
  proves internal consistency at epoch B and never current provider truth.
- Those rows are **byte-frozen, not merely stale-and-tolerated**. Each
  `acceptance.json` packet's `digest` is the subject identity every
  `start_dependencies` / `completion_dependencies` edge cites, and
  `compile_repository_portfolio.py` fails closed on drift — verified 2026-08-22
  by mutating one packet's `evidence.ceiling`, which makes the compile exit 1
  with `acceptance:ISSUE-559: digest mismatch`. Rewriting an `observed_state` in
  place would silently re-point every admitted dependency at a subject that did
  not exist at admission time, so later observations are recorded beside these
  files and never inside them.
- `multigraph.json` reproduces byte-for-byte (digest `bb13426b…`) from
  `snapshot.json` plus the 16 acceptance packets via
  `compile_repository_portfolio.py`, and the same recompile goes red under a
  one-character packet mutation. That is an internal-consistency control, not a
  freshness control.
- `shared-skills-infra/tests/control-plane/verify.sh` is red in local
  single-branch clones on the authoring machine for both `main` and this
  branch (one-variable control, 2026-08-22): environmental, not a regression;
  pristine CI runners are the authority for that lane.
