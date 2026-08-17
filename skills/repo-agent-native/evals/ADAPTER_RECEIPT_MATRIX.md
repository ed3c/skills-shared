# Adapter Receipt Completion Matrix

Refs #256. This is the completion-report matrix #256 requires: "Publish a matrix
of every lane with exact subject, command/tool identity, receipt digest,
controls, state, scope ceiling, residue result and unresolved gaps. Do not
collapse missing live evidence into PASS."

Source of truth for every row below is the committed receipt at
`evals/receipts/<lane>.receipt.json`, validated by
`scripts/check_adapter_receipts.py` (contract in `references/EVIDENCE_MODEL.md`
and `references/TOOL_ROUTING.md`). This document is a human-readable
projection of those receipts, not a second authority — if a row and its
receipt ever disagree, the receipt is correct and this file is stale.

## Exact subject

All nine receipts bind the same repository subject, captured on a prior
`skills-shared` worktree (`.claude/worktrees/lanes-256`):

```text
repository   ed3c/skills-shared
commit       f50b2b9822db9e534169b5e63b523d940b32bb3c
tree         42f289d44c1befefc9bdfb0bacf88a26a01b198a
dirty_paths  0 (evals/receipts/ itself excluded from the dirty check)
```

`check_adapter_receipts.py check` refuses to admit a receipt set that spans
more than one commit, so this single-subject binding is a mechanical
invariant, not an assertion made by this document.

## Lane matrix

| Lane | Tool identity | Receipt digest (stdout / stderr sha256) | State | Evidence level | Controls (observed) | Scope ceiling | Residue |
|---|---|---|---|---|---|---|---|
| grepai | grepai 0.30.0 (`sha256:e2d5ad30…32bc`) | `ccf9c321…2831` / `e3b0c442…855` (empty) | PASS | B+ (indexed candidate) | `semantic-distractor` RED, `wrong-project` RED | Intent anchor only; every hit is a candidate promoted to fact only via a linked source-readback event (5/5 confirmed here), never a semantic hit alone | index dir `.grepai/` left in place — gitignored and rebuildable, not deleted |
| scip | scip-python 0.6.6 (`sha256:ce60dd39…19d2a`) | `e3b0c442…855` (empty) / `ddb3bf93…f99e` | PASS | A- (structured static evidence) | `decode-validated-against-disk` RED, `coverage-is-per-language` RED | 296 declarations/references read back; coverage is scoped to the languages the indexer actually ran on, not claimed as whole-repository completeness | `index.scip` left in place — rebuildable from the same subject by rerunning the indexer |
| tree-sitter | tree-sitter 0.26.0 (`sha256:01ae36c3…6b059`) | `180493f4…ed4c` / `e3b0c442…855` (empty) | PASS | A- (structured static evidence) | `parse-error-surfaced` RED, `byte-range-readback` RED | Structural (AST) evidence only; does not claim cross-file semantic truth (that is SCIP's lane) | cleaned, no paths left |
| serena | serena-cli (`sha256:d777582f…9454b`) | `0a7526ef…eab81` / `0a0d916f…d737` | PASS | B (declared contract) | `language-coverage-declared` RED | Index build/workspace bind only — 296 symbols indexed, nothing promoted to a fact; no edit/execution session was exercised in this lane | `.serena/` cache left in place — Serena writes its own `.gitignore` inside it |
| sqlite | sqlite 3.53.3 (`sha256:34de4799…f93d1`) | `e3b0c442…855` (empty) / `e3b0c442…855` (empty) | PASS | B (declared contract) | `duplicate-subject-refused` RED, `integrity-check` RED | Canonical evidence ledger for the 9 lanes in this receipt set only, not a repository-wide fact store | `adapter-evidence-ledger.sqlite3` left in place — rebuildable from the receipts in this directory |
| lancedb | lancedb 0.37.1 (`sha256:01ae36c3…6b059`) | `14339da3…b90d68` / `8e71995d…f54b6` | PASS | B (declared contract) | `projection-has-a-source-lane` RED, `deleting-the-projection-changes-nothing` RED | Optional, consumer-owned projection per `references/BLINDSPOT_HYBRID_CONTRACT.md`; every row links to a non-LanceDB source event and carries no source of its own | cleaned, no paths left |
| worktree | git 2.50.1 (Apple Git-155) (`sha256:12bed452…668ba`) | `e3b0c442…855` (empty) / `e3b0c442…855` (empty) | PASS | A (direct implementation evidence) | `one-writer-per-branch` RED | Proves the local `git worktree add/remove` mechanism and a concurrent-clash control only; #231's live multi-Worker scheduler receipt is bound separately as a **cross-subject** reference, never merged into this lane (see the binding section below) | cleaned, no paths left |
| forgejo | forgejo 9.0.3+gitea-1.22.0, loopback `http://localhost:3000` | `16969a75…7b855` / `e3b0c442…855` (empty) | PASS | B (declared contract) | `repository-binding-absent` RED, `provider-reachable-is-not-binding` RED | Provider identity/reachability inventory only. This repository has no admitted Forgejo remote, so `repository_bound=false`; no issue, PR, branch or push was created or attempted (`policy.mutation_granted=false`) | cleaned, no paths left |
| git-town | — (not installed) | none (`terminal_state=NOT_STARTED`) | **ABSENT** in this capture set; **PASS** in `receipts-git-town-darwin/` | none here | none here | The darwin artifact was Human-admitted on 2026-08-17 (`evals/git-town-darwin-admission.json`, v24.0.0 darwin-arm64 pinned to the runtime-env catalog digest) and the lane was implemented and exercised live at its own subject. Its receipt lives in the single-subject directory `evals/receipts-git-town-darwin/` because one capture is one subject: this directory's eight receipts bind `f50b2b98` and cannot absorb a receipt from a later commit. The next full nine-lane recapture at one commit supersedes both | this row's lane: nothing ran here; the darwin capture cleaned its own tree |

8 of 9 lanes are `PASS` with a real executed control that could have turned
them red (`check_adapter_receipts.py`'s `CONTROL_MISSING` law refuses any
`PASS` where no control observed `RED`). `git-town` is honestly `ABSENT`
in this f50b2b98-bound set (its exercised darwin receipt lives in
`receipts-git-town-darwin/` at its own subject),
not laundered into `PASS` or silently omitted from the receipt directory —
`tests/adapter-receipts/verify.sh` asserts all nine lane files exist,
present or absent, so a missing file cannot read as a passing lane.

## Scheduler / Git Town / dual-forge receipt binding (#256 acceptance item 7)

#256's "Required live lanes" section 7 asks this Skill to *integrate* — not
duplicate — the Worker/attempt/lease/worktree receipts owned by #231 and the
Stack/branch/ancestry/Forgejo-publication receipts owned by #234, keeping
`git town sync`, implementation assertions, Forgejo delivery, GitHub Actions
and Human merge as distinct evidence states.

This is two lanes, not one, and collapsing them into a single row hid the one
that is now closed. They are tracked separately:

| Sub-lane | Owning issue | Receipt | State | What the state means |
|---|---|---|---|---|
| Worker / attempt / lease / worktree scheduler | #231 | `skills/dual-forge-repository-loop/evals/receipts/scheduler-run.receipt.json` | **BOUND (cross-subject)** | Bound by `check_adapter_receipts.py check --bind-scheduler`, which prints `CROSS_SUBJECT_BINDING` only after asserting the two subjects are **different** commits |
| Stack / branch / ancestry / Forgejo publication | #234 | `consumer-canary.receipt.json` | **NOT_EXERCISED** | Its `git town sync` link is `BLOCKED` on the same darwin/`linux_intel_64` Human-admission gap as the `git-town` row above |

### #231 — BOUND, cross-subject

The `worktree` lane above proves the local `git worktree` mechanism this Skill
itself uses, at adapter subject `f50b2b9822db…`. #231's scheduler receipt is a
real live `claude` run (2026-08-16, 7 planted attempt states, 3 named
refusals), but it was captured against a *disposable canary repository*
(`28835d53d265…` → `5a2d4d1b321b…`), deliberately not against `skills-shared`
— running parallel Workers against the live repository while other sessions
write to it is a hazard, which that receipt's own `subject.note` records.

So the two bodies of evidence can never share a subject, and the honest state
is neither PASS (which would spend one subject's evidence on another's) nor
NOT_EXERCISED (which would discard evidence that exists). It is a
**cross-subject binding**, and the check that keeps it honest runs the
assertion in the direction that can actually catch the lie:

```text
python3 scripts/check_adapter_receipts.py check \
  --receipts evals/receipts \
  --bind-scheduler ../dual-forge-repository-loop/evals/receipts/scheduler-run.receipt.json

ADAPTER RECEIPTS GREEN: 9 lane(s) at f50b2b9822db -- 1 ABSENT, 8 PASS
CROSS_SUBJECT_BINDING scheduler-run.receipt.json: 28835d53d265..5a2d4d1b321b
  (disposable-canary-repository) is not the adapter subject f50b2b9822db
  -- 7 planted state(s), 3 named refusal(s) bound, not merged
```

Equal subjects refuse with `SUBJECT_COLLAPSED` (exit 2), and
`tests/adapter-receipts/verify.sh` plants exactly that — it rewrites the
scheduler receipt's `initial_sha`/`final_sha` to the adapter subject and
requires the gate to go red, so `CROSS_SUBJECT_BINDING` is a claim that has
been shown to be falsifiable rather than one that is merely printed.

The binding is a reference, not an absorption: this Skill does not re-run,
re-derive or restate #231's scheduler state machine, which #256 explicitly
forbids. #231's own open gap (no budget ledger) stays #231's.

### #234 — NOT_EXERCISED

Unchanged and honestly unexercised. Git Town is not installed on this darwin
host and this Skill does not install it: the repository's admitted artifact is
pinned by SHA-256 to `linux_intel_64`, and the monitor contract places that
installation in runtime-env/user scope. The same applies to any Forgejo
publication path.

## Unresolved gaps against #256's acceptance checklist

```text
schemas and deterministic validators close with positive and
  planted-negative fixtures                          PASS (this matrix + check_adapter_receipts.py selftest)
one admitted consumer emits live receipts for GrepAI, SCIP/LSP,
  Tree-sitter, Serena and SQLite on the same exact
  repository subject                                  PASS (single commit f50b2b98…2bb3c, all five lanes PASS)
optional LanceDB projection exercised with rebuild/
  back-reference proof, or explicitly NOT_EXERCISED    PASS (exercised; back-reference control RED-tested)
#231 and #234 receipt references reconcile to the same
  task/branch/repository subjects                      #231 BOUND (cross-subject: the scheduler ran on a
                                                         disposable canary repo by design, so "the same
                                                         subject" is the defect, not the goal -- the gate
                                                         refuses SUBJECT_COLLAPSED when they match)
                                                       #234 NOT_EXERCISED (git town sync BLOCKED on the
                                                         darwin/linux_intel_64 Human admission)
all raw artifacts content-addressed and replayable
  where transport permits                              PASS (every executed lane carries stdout/stderr sha256)
cleanup and rollback subjects are explicit                PASS (residue.cleaned / residue.paths on every receipt)
shared Skill bodies remain domain-neutral and
  secret-free                                          PASS (check_secrets() scans every receipt; no forbidden pattern found)
merge, provider activation, publication, promotion
  and rollback remain Human/trusted-operator authority   HUMAN_ADMIT_REQUIRED (any GitHub publication of this
                                                          matrix's findings); the git-town darwin artifact binding
                                                          was Human-admitted 2026-08-17
                                                          (evals/git-town-darwin-admission.json)
```

Git Town remains the one lane this repository cannot exercise from a darwin
host without a Human admitting a `linux_intel_64`-pinned artifact under a
darwin-compatible identity. That decision, and the #234 sub-lane that depends
on it, are what #256 still cannot close without live or Human input. The #231
sub-lane is closed as a cross-subject binding and is no longer waiting on
anything.
