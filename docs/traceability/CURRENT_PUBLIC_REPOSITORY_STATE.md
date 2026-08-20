# Current public repository state — 2026-08-20

Document role: `CURRENT_HANDOFF / HUMAN_PROJECTION`.

This file is the first human-readable current-state route for the public `skills-shared` repository after the #509 Tech Lead + Shadow closure audit. It is **not** a second machine authority. Current GitHub issue/PR/workflow metadata, Git commit/tree identity, executable schemas/scripts/tests, and exact runtime receipts win if this projection drifts.

## Frozen audit baseline

```text
repository   ed3c/skills-shared
main         249abc47847f8295b1c75c9d4c84457c5126fd89
tree         a24b9b7ace6f4022967d41262ecdc704d5c11646
audit issue  #509
```

The document may be merged on a later commit. Re-read `main` before any mutation; do not treat the baseline above as a floating alias.

## Current closure state

### Admitted / closed mechanism and evidence lines

| Programme | Current terminal evidence | Exact / durable subject | What it does **not** prove |
|---|---|---|---|
| Wave-2 Tech Lead control plane | `HUMAN_ADMITTED / MERGED` | #379 / PR #455, merge `ca31e0b1e640f0dba2c3d94da9d9786fbed32f2c` | live Codex/Herdr/source truth |
| Wave-3 live-evidence infrastructure | `HUMAN_ADMITTED / MERGED` | #468 / PR #480 + post-merge #484 | live lane execution by itself |
| GitHub Issue Dependencies canary | `LIVE_GITHUB_DEPENDENCY_CANARY_PASS / REMOTE_CANARY_EDGE_ONLY` | #465, run `32296935756`, receipt `da227e94215a1b28a9e550546242c8a482bd718f7b35d67f159ccaa95f23efe5` | semantic task-DAG authority |
| Wave-2 → Wave-3 live-owner transfer | `HUMAN_ADMITTED / MERGED` | #485 / PR #503; residual prose repair #504 | closure of successor live lanes |
| GitHub `blockedBy` producer repair | `COMPLETED` | #497 / PR #504; current deterministic denominator `7 positive / 23 mutations` | live generic Development-link mutation |
| Codex acceptance false-PASS repair | `HUMAN_ADMITTED / MERGED` | #505 / PR #507, merge `249abc47847f8295b1c75c9d4c84457c5126fd89` | a fresh signed-in Codex v2 run |
| Public consumer bootstrap | `REAL_PUBLIC_CONSUMER_HOSTED_BOOTSTRAP_CLOSED` | #366; `website-design-compiler` PR #53 merge `02e4f57c229660ffd551c831ce408420cd63ca0b`, tree `5e50c8a33197bf994f23e9a0ef888793629ca840` | local Codex/Claude discovery, Agent/model/provider execution |

Historical transport, rejected, stale and closed-unmerged subjects remain denominator evidence. They are not alternate current authorities.

### Current unresolved evidence owners

```text
#376  generic GitHub Development sidebar PR/branch link/unlink
      RESIDUAL / MANUAL_GITHUB_UI_OR_UNEXPOSED_MUTATION_API_REQUIRED

#464  fresh signed-in Codex SDK/controller acceptance using v2 result-tree receipt
      NOT_EXERCISED on the post-#507 contract

#466  real Herdr workspace/process lifecycle
      NOT_EXERCISED

#467  article/PDF/PRD claim truth + real source/provider closure
      SOURCE_PROPOSAL / EVIDENCE_DEPENDENT

release / production promotion
      NOT_PERFORMED
```

`#465` does not close `#376`: Issue Dependencies and the generic Development sidebar are different GitHub surfaces. A fixture-edge PASS cannot be promoted to an undocumented/manual link API.

## Current evidence State Machine

```text
SOURCE_OR_REQUEST_BOUND
→ EXACT_REPOSITORY_SUBJECT_BOUND
→ METHOD / CONTRACT IMPLEMENTED
→ DETERMINISTIC_CONTROLS_EXECUTED
→ HOSTED_EXACT_HEAD_REVALIDATED
→ LIVE_OR_PHYSICAL_LANE_EXECUTED when required
→ INDEPENDENT_SHADOW_READBACK
→ HUMAN_ADMIT when required
→ MERGED
→ POST_MERGE_READBACK
→ CLOSED only for the evidence scope actually earned
```

No transition can be skipped by issue UI state, PR mergeability, model prose, a source document, or a cheaper evidence lane.

## Agentic Tech Lead directory → State Machine / DAG / data flow

Canonical owner: [`../../skills/agentic-tech-lead-orchestration/README.md`](../../skills/agentic-tech-lead-orchestration/README.md).

```text
references/
  immutable task/capability/session/receipt/closure contracts
      ↓
modules/
  trigger-selected execution/projection/observer interpretations
      ↓
scripts/
  deterministic compilers, executors, reducers and readback gates
      ↓
tests/
  positive / hollow / mutation / integration falsifiers
      ↓
exact runtime / GitHub subjects
      ↓
controller + independent Shadow receipts
      ↓
convergence / Local Handoff / Human Admit
```

Current Codex v2 path:

```text
TASK/SUBJECT_BOUND
→ SIGNED_IN_CODEX_ATTEMPT
→ LEASE_READBACK
→ RESULT_TREE_MATERIALIZED
→ base_sha^{tree} READBACK
→ exact base→result-tree changed-file denominator
→ controller source/diff/test readback
→ codex-live-acceptance-receipt/v2
→ INDEPENDENT_SHADOW
→ ACCEPTED | BLOCKED | RETRYABLE
```

The v2 receipt requires `sdk_execution=EXERCISED`, `lease_readback=PASS`, `result_tree_readback=PASS`, `source_diff_readback=PASS`, `tests_readback=PASS`, and remains `LIVE_EXECUTION_OBSERVED_SHADOW_PENDING` until Shadow admission.

## Molecular Stack — current terminal public line

Canonical method/index: [`../../skills/git-town-stacked-pr-worker/README.md`](../../skills/git-town-stacked-pr-worker/README.md).

```text
Wave-2 sibling mechanisms
  #375 / #376 / #377 / #378
        ↓ exact selected bytes
  #379 / PR #455                 CONVERGENCE → MERGED
        ↓
Wave-3 live-evidence siblings
  #464 / #465 / #466 / #467
        ↓ exact selected bytes
  #468 / PR #480 + #484          CONVERGENCE / POST-MERGE → MERGED
        ↓
  #465 hosted executor/REST/live receipt      EXTERNAL_EVIDENCE → CLOSED
  #485 / PR #503 ownership transfer           CONVERGENCE → MERGED
  #497 / PR #504 generic readback repair      REPAIR → MERGED
  #505 / PR #507 Codex v2 result-tree repair  REPAIR → MERGED

external public consumer
  #366 → website-design-compiler PR #53       PROCESS/CONSUMER EVIDENCE → MERGED/CLOSED
```

These edges are not a fake serial Git stack. `SIBLING`, `TRUE_CHILD`, `CONVERGENCE`, `PROCESS_DEPENDENCY`, `EXTERNAL_EVIDENCE`, and `HISTORICAL` retain their normal meanings.

## Open PR / Stack classification

Do not merge old Stack ancestry merely because an old head was green. Current audit classifies these programme clusters as requiring a **current-main reconstruction/revalidation** before publication:

```text
Spatial / Knowledge Graph
  #412 → #419 / #420 → #450
  old base / long-lived ancestry; reconstruct on current main

Repository Entropy
  old C/K/A/E/X/D Stack around #387–#391 / #404
  root source PR closed-unmerged; reconstruct admitted method bytes on current main

Kenn Agentic Engineering
  #395 → #396
  reconstruct/revalidate on current main

Productization
  #434
  commit-role provenance blocker; owning repair remains separate
```

A reconstruction must preserve the old failed/stale denominator and prove exact byte consumption; it must not silently rebase stale green evidence into a current PASS.

## Source / article / PDF real-problem closure matrix

| Source programme | Earned closure | Still open |
|---|---|---|
| `STE100 檢查與改寫 LLM 應用.pdf` / #115 | portable CTL contracts, deterministic authority/evidence separation and modules exist | #115 remains open; integrated A/B, real proprietary/official pack, qualified Human semantics and any official ASD-STE100 compliance claim remain unproven |
| `双 Agent 架构：云端本地协同` / #359 | parent portable method is completed | child #362 remains open for exact local executable contract/worktree/gates; transport/cloud/provider/user/release remain separate |
| PDF-derived old/new Tech Lead behavioural proof / #316 | deterministic/hermetic lower layers exist | physical matched old/new Agent runs, enough repetitions and live delivery evidence remain open |
| `AI 编程新范式：并行 Agent 体验` / #368 | individual adapter identities/receipts exist | one causal grepai→SCIP→SQLite→Tree-sitter→Serena exact-task chain and independent Shadow remain open |
| Product Reverse / #357–#373 | method/program and exact Molecular plan are specified | C/K/E/D implementation and user/paid/live session/projection evidence are not fully admitted |
| Repository Entropy / #386 | source proposals and target method/DAG are specified; parts exist in stale Stack | issue remains `PARTIALLY_INTERNALIZED / NOT_CLOSED`; current-main C/K/A/E/X/D publication and live deletion/adoption/Git Town evidence remain open |

Source prose never earns repository truth. A PDF/article-derived statement becomes stronger only through exact applicability, implementation and verification receipts.

## Local Handoff

Historical `wave3-live-handoff-queue.json` remains immutable history. The current local execution epoch is [`../../skills/agentic-tech-lead-orchestration/references/public-main-local-handoff-queue-2026-08-20.json`](../../skills/agentic-tech-lead-orchestration/references/public-main-local-handoff-queue-2026-08-20.json).

Only true serial local work belongs in one queue. Independent manual/external lanes remain on their owning issues:

```text
queue ACTIVE     #464 signed-in Codex v2 acceptance
manual residual  #376 Development sidebar link/unlink
local parallel   #466 Herdr lifecycle
external truth   #467 source/provider evidence
```

## Human / trusted-operator boundary

This audit does not authorize or claim:

```text
provider activation
secret or credential mutation
production writes
release / promotion
semantic conflict auto-resolution
force push
unbounded browser/device automation
legal/compliance certification
```

Merge is allowed only after the exact candidate head remains current and passes its owning repository gates plus independent Shadow readback.