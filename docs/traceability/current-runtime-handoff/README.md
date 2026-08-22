# Tech Lead + Shadow Architect current closure audit

Status: `HISTORICAL_SNAPSHOT_AT_129f53c / SUPERSEDED_BY_PORTFOLIO-EPOCH-20260822-B`.

This was the cold-start route for issue/PR closure decisions after PR #516 executed the three sibling Local Handoff Execution Queues bound by #511 and merged into main as `129f53c`. `main` has since advanced three times more — to `28f3947` (PR #571, Wave-8 ghpc landing), to `5341885` (PR #574, the #560 Repository Portfolio Control wave), and to `674cfe1` (PR #577, the DTCR handoff-queue truth-surface repair) — and the #560 wave merged or closed every PR this document still lists as Draft/HOLD below. Read `docs/traceability/github-portfolio-control/README.md` first for anything postdating `28f3947`; the PR decisions table below has been annotated with the current terminal state but is not itself the current epoch's authority. It records what was admitted at `129f53c`, what was closed only as consumed lineage, and what still required a local/runtime or source-evidence lane at that time. It does not replace current GitHub metadata or executable receipts.

## Exact subjects

```text
repository                 ed3c/skills-shared
current admitted main      674cfe1435c4bd1c29e8f07308266fe5c6284973 (PR #577; chain: 129f53c -> 28f3947 -> 5341885 -> 674cfe1)
current tree               217bf950a57701235f761223e9466b9774aa6194
rollback / pre-#577 main   5341885f26b5e8e7baf5087a4d661e324f878242
rollback / pre-#516 main   88ce642a7f198d88019aa8ae19e63631ae4999c2
Wave-3 queue subject       249abc47847f8295b1c75c9d4c84457c5126fd89 (the subject the #508/#466/#512 continuation queues were compiled against and executed on under PR #516; #511 was the docs-only movement. It is the #508 receipt's `parent_commit` — the receipt binds its implementation to `2436358…` — and later waves rebound or superseded several queues, so read each queue's own `subject` field rather than assuming this one)

#507 checked head          e306797fdbf4875bafd410fd415e6bcb3587ff9b
#507 merge subject         249abc47847f8295b1c75c9d4c84457c5126fd89

#516 merge subject         129f53c23a3ab15354763167b25bddc45f724c00
```

PR #507 was reviewed on its exact head, passed Skill Eval Contract, Shared Skills Infra, Skill Suites, and the `agentic-tech-lead-orchestration` matrix leg, then merged without head substitution. It repairs the central first-live-run false PASS by binding acceptance to a Git result tree whose exact base-to-result changed-path denominator is independently recomputed.

PR #516 executed the three ACTIVE Local Handoff Execution Queue items — #508, #466, #512 — on the exact bound implementation subject `249abc47847f8295b1c75c9d4c84457c5126fd89` (branches cut from that subject; the docs-only delta to current main verified as an empty diff against the owning scripts), then integrated into current main as `129f53c23a3ab15354763167b25bddc45f724c00`. Independent Shadow readback on the candidate: `ADMIT` (forbidden delta absent; live lanes truthfully `NOT_EXERCISED`; noncritical findings owned by #512 and #466).

## Real-problem closure ledger

| Problem | Current state | Evidence and boundary |
|---|---|---|
| Worker/controller JSON could agree while the bound Git tree lacked the claimed change | `CLOSED_DETERMINISTICALLY` | #505 / PR #507; private index + `git write-tree`; binder resolves base tree, result tree, and exact changed paths; `1 positive / 16 mutations` |
| Detached result tree may not survive cleanup, clone transfer, or Git pruning | `CLOSED_DETERMINISTICALLY / #508 PASS via PR #516` | `codex_result_carrier.py` publishes parentless evidence commits + a content-addressed Git bundle/manifest; `replay` resolves the result tree in a bare scratch repo with all `GIT_*` inheritance stripped; self-demo replayed after the originating worktree was `shutil.rmtree`'d; receipt `data/handoff/codex-v2/issue-508-result-carrier-receipt.json`, verdict `PASS`; live #464 acceptance of a fresh run remains `NOT_EXERCISED` |
| Receipt does not bind the exact Codex executable/package/build | `CLOSED_DETERMINISTICALLY / #508 PASS via PR #516` | `executor_provenance` binds adapter/SDK/binary identity and recomputes `adapter_blob_sha256`/`codex_binary_sha256`; a signed-in session is explicitly excluded from provenance; only exercised against a stub SDK module, so a real `openai-codex` binary identity remains unobserved |
| Worker-result shape is defined by code arrival rather than a strict standalone receipt contract | `CLOSED_DETERMINISTICALLY / #508 PASS via PR #516` | committed closed Draft 2020-12 schema `references/contracts/codex-worker-result-v2.schema.json`; `check_codex_worker_result.py` is the semantic gate; 10 planted controls red-for-reason |
| Real GitHub Issue Dependencies add/readback/remove/restore | `VERIFIED_LIVE / #465 CLOSED` | run `32296935756`, base `81041d1b88283fabdc1c4db05efaf8dd945e24df`, receipt SHA-256 `da227e94215a1b28a9e550546242c8a482bd718f7b35d67f159ccaa95f23efe5`; semantic authority remains false |
| Real Herdr managed-agent lifecycle | `NOT_EXERCISED / #466 OPEN (blocker RECLASSIFIED via PR #516)` | corrected finding: the blocker is not host permission — Herdr 0.8.0's `AgentInfo` surface publishes no observation timestamp, process id, liveness, start time, or cleanup/residue facts, so the frozen observer contract can never emit a sample; a host-isolation denial on setting `HOME` is a second, independent blocker; receipt `data/handoff/herdr-v2/herdr-lifecycle-receipt.json`, `sample_count: 0`, evidence ceiling `NO_HERDR_LIFECYCLE_SAMPLE` |
| Source compiler/binding method | `COMPLETED / #467 CLOSED` | GitHub issue #485 compiled and passed the existing closure checker; this proves deterministic binding, not source truth |
| ARTICLE/PDF/PRD or further Issue truth/applicability | `EVIDENCE_DEPENDENT / #512 OPEN (first packet executed via PR #516)` | first immutable source packet executed: GitHub issue #435 bytes + provenance + claim packet compiled against `#467`'s method into `data/handoff/source-evidence/problem-closure-ledger.json`; compiler/closure-checker exit 0 (binding PASS only); dispositions `OPEN` (six unclassified commits still need `evals/commit-roles.json` repair), `OPEN` (repair not yet executed), `NOT_APPLICABLE` (scope-only evidence-boundary claim); compiler PASS is not source truth |
| Repository entropy method + deterministic gate + domain ports + controls + CI/registry arrival | `HUMAN_ADMITTED_ON_MAIN` | rebuilt and landed through UCR admission PR #477; old C/K/A/E/X PRs remain closed-unmerged lineage |
| Entropy nearest Agent/README routes and terminal Molecular index | `IMPLEMENTED_BY_THIS_AUDIT_CANDIDATE` | issue #403 / PR #404 is closed only after this exact candidate lands and hosted routing gates pass |
| codex-v2 queue's ACTIVE item is complete on an admitted subject | `RECOMPILED_AND_EXECUTED (2026-08-22)` | per the subject-mutation law the NEW #464 queue was compiled fresh as `runtime-handoff/codex-v2-live-464-local-handoff-queue.json` against its own merged implementation head (never the stale `129f53c` — always re-derive current `main` via `git rev-parse`); its live run executed with receipt verdict `PASS`, Shadow pending. `references/wave3-live-handoff-queue.json` used to invoke `run_codex_sdk_worker.py --execute` without `--carrier-out-dir` and died at argparse; the flag has since been added, so that argparse death is historical |

## Issue decisions

```text
#465  CLOSED / COMPLETED
      exact remote one-edge canary PASS with cleanup and denominator restoration

#467  CLOSED / COMPLETED
      deterministic source compiler/binding method complete; source truth is not implied

#468  CLOSED / COMPLETED
      Wave-3 static/deterministic convergence only

#505  CLOSED / COMPLETED
      central deterministic result-tree false-PASS repair merged as #507

#464  OPEN
      #508 now closed on an admitted subject; the next step is compiling a NEW queue
      against current main (re-derive via git rev-parse main; 129f53c is stale — main
      has since advanced to 28f3947 then 5341885 then 674cfe1, PR #577), then a fresh
      signed-in v2 run

#466  OPEN
      live Herdr lane attempted; blocker RECLASSIFIED via PR #516 from host-permission
      to a herdr-0.8.0 API contract mismatch (no observation timestamp, process identity,
      or cleanup facts on AgentInfo); durable NOT_EXERCISED receipt landed, sample_count 0

#508  ELIGIBLE_TO_CLOSE
      PR #516 landed durable result carrier, executor provenance, and strict
      worker-result schema; receipt data/handoff/codex-v2/issue-508-result-carrier-receipt.json,
      verdict PASS; live #464 acceptance of a fresh run remains a separate NOT_EXERCISED lane

#512  OPEN / EVIDENCE_DEPENDENT
      first immutable source packet executed via PR #516 (GitHub issue #435 bytes);
      problem-closure-ledger.json dispositions OPEN x2 / NOT_APPLICABLE x1; deterministic
      binding PASS is not source truth; issue remains open pending the repair itself
```

## PR decisions

| PR | Decision | Reason |
|---|---|---|
| #507 | `MERGED` | exact-head deterministic Method-Plane repair; merge `249abc47847f8295b1c75c9d4c84457c5126fd89` |
| #516 | `MERGED` | executed the #508/#466/#512 Local Handoff Execution Queues on the bound subject; merge `129f53c23a3ab15354763167b25bddc45f724c00`; independent Shadow `ADMIT` |
| #388 | `CLOSED_UNMERGED / CONSUMED` | K checker blob is byte-identical on current main |
| #389 | `CLOSED_UNMERGED / CONSUMED` | A domain-profile blob is byte-identical on current main |
| #390 | `CLOSED_UNMERGED / CONSUMED` | E control suite is present on current main |
| #391 | `CLOSED_UNMERGED / SUPERSEDED` | registry/CI integration was rebuilt on current governance and admitted through #477 |
| #404 | `CLOSE_AFTER_THIS_CANDIDATE_LANDS` | its nearest entropy routes are integrated here with current state corrected |
| #412 | `DRAFT / HOLD` (as of 129f53c) → **now `CLOSED_UNMERGED / SUPERSEDED`** | GitHub reports `state=CLOSED` (`prs-open.json` has zero open PRs); the #560 portfolio wave commit `c27f8c3` ("merge(#419,#412): land the replayed ICPG bridge carrier (supersedes #412 bytes)") confirms the supersession in-repo — original #511-era reasoning no longer applies ("`MERGEABLE` per current readback; returned to Draft per the #511 audit decision because its own close gates remain incomplete and #411 live Shadow remains open") |
| #419 | `DRAFT / HOLD` (as of 129f53c) → **now `CLOSED_UNMERGED / CONSUMED`** | GitHub reports `state=CLOSED`; consumed into main via the #560 portfolio wave (commit `c27f8c3`, "merge(#419,#412): land the replayed ICPG bridge carrier (supersedes #412 bytes)") — original #511-era reasoning no longer applies ("`MERGEABLE` per current readback; its `docs/INDEX.md` conflict against base `agent/spatial-intent-case-proof-graph-v1` was resolved by merge commit `94426ce` (unioned route-index prose, `check_document_routes.py` green); true child of #412, whose own close gates remain incomplete") |
| #420 | `DRAFT / HOLD` (as of 129f53c) → **now `CLOSED_UNMERGED / CONSUMED`** | GitHub reports `state=CLOSED`; consumed into main via the #560 portfolio wave (commit `6685da6`, "merge(#420): land the replayed machine-projection contracts") — original #511-era reasoning no longer applies ("`MERGEABLE` per current readback; design artifact only; deterministic/runtime close gates remain incomplete") |
| #450 | `DRAFT / HOLD` (as of 129f53c) → **now `CLOSED_UNMERGED / CONSUMED`** | GitHub reports `state=CLOSED`; consumed into main via the #560 portfolio wave (commit `f6103e3`, "merge(#450): land the replayed case-delivery binding") — original #511-era reasoning no longer applies ("`MERGEABLE` per current readback; #448 exact-head hosted receipt and later traversal/runtime lanes remain missing") |
| #434 | `CLOSED_UNMERGED (2026-08-21)` | closed on GitHub before this pass; Productization rebuild remains owned by #436 |
| #395 | `DRAFT / HOLD` (as of 129f53c) → **now `MERGED`** | GitHub reports `state=MERGED`, `mergedAt=2026-08-21T20:00:23Z`, landed directly via the #560 portfolio wave (commit `1621b2f`, "merge(#395): land the replayed human-led design control plane") |
| #396 | `DRAFT / HOLD` (as of 129f53c) → **now `CLOSED_UNMERGED / CONSUMED`** | GitHub reports `state=CLOSED`; consumed into main via the #560 portfolio wave (commit `04756de`, "merge(#396): land the replayed Kenn traceability and stack index") — original #511-era combined-row reasoning no longer applies ("both `MERGEABLE` per current readback; human-led Agentic Engineering method + trace child have no current-main refresh and no current exact-head admission") |

As of this document's own pass (main `129f53c`), the five PRs above (#412, #419, #420, #450, #395/#396) read `MERGEABLE` Draft on GitHub, each against its own base branch. That reading is now historical: the #560 Repository Portfolio Control wave (main `129f53c` → `28f3947` → `5341885`) subsequently merged `#395` directly and closed `#412`/`#419`/`#420`/`#450`/`#396` unmerged (consumed) — GitHub reports zero open PRs on this repository as of `5341885` (`prs-open.json = []`). Main has since advanced once more to `674cfe1` (PR #577, the DTCR handoff-queue truth-surface repair); no fresh GitHub PR-state dump exists at that commit in this pass, so the zero-open-PRs count above is asserted only as of `5341885`, not `674cfe1`. See `docs/traceability/github-portfolio-control/` for that epoch's disposition of each. Old green runs and old `MERGEABLE` readbacks do not follow a moving base — re-read current GitHub state before citing any line of this section as live.

## Directory → responsibility map

```text
docs/traceability/current-runtime-handoff/
├── AGENTS.md
│   └── closure, writer, Shadow, and queue admission law
└── README.md
    └── current immutable subjects, problem ledger, issue/PR decisions, handoff map

skills/agentic-tech-lead-orchestration/runtime-handoff/
├── AGENTS.md
├── README.md
├── codex-v2-local-handoff-queue.json
├── herdr-local-handoff-queue.json
└── source-evidence-local-handoff-queue.json
    └── exact local/runtime continuation contracts

skills/repository-entropy-reclamation/
├── AGENTS.md
└── README.md
    └── nearest Agent route plus current State Machine, DAG, data flow, and evidence ceiling

skills/git-town-stacked-pr-worker/molecular-indexes/codex-v2/
└── README.md
    └── terminal Molecular PR index for entropy, Wave-3/Codex v2, and held Draft stacks
```

## Current task/process DAG

```text
#505 / PR #507  result-tree binder repair  MERGED
        ↓ process + implementation dependency
#508 / PR #516  durable carrier + executor provenance + result schema  PASS / ELIGIBLE_TO_CLOSE
        ↓ subject since re-admitted past 129f53c to 28f3947 then 5341885 then 674cfe1
        ↓ (PR #577); recompile queue against current main, not 129f53c
#464             fresh signed-in Codex v2 execution + controller + Shadow  OPEN / QUEUE_RECOMPILE_REQUIRED

#466 / PR #516   Herdr managed lifecycle receipt   SIBLING / EXTERNAL_RUNTIME; NOT_EXERCISED, blocker RECLASSIFIED
#467             source compiler method             COMPLETE / HISTORICAL METHOD
#512 / PR #516   immutable source packet + closure  SIBLING / SOURCE_EVIDENCE; first packet EXECUTED (issue #435)
#465             remote GitHub canary               COMPLETE / HISTORICAL RECEIPT
```

The Codex queue's ACTIVE item (#508) is now complete on an admitted subject. Per the subject-mutation law, the next step is compiling a NEW #464 queue against current `main` (re-derive via `git rev-parse main`; `129f53c` is stale — main has since advanced to `28f3947` then `5341885` then `674cfe1`, PR #577) rather than advancing the existing #508 queue.

## Local Handoff queues

| Queue | ACTIVE item | Exit |
|---|---|---|
| `codex-v2-local-handoff-queue.json` | #508 durable result carrier/provenance/schema — `PASS` via PR #516; issue #508 itself is now `CLOSED` on GitHub (`closedAt 2026-08-21T07:19:45Z`, `stateReason COMPLETED`) | queue's own item is complete; `main` has since advanced past `129f53c` to `28f3947` then `5341885` then `674cfe1` (PR #577, DTCR truth-surface repair) — a NEW #464 queue must be compiled against **current `main`** (re-derive via `git rev-parse main` at compile time; do not bind to the now-stale `129f53c23a3ab15354763167b25bddc45f724c00`), also adding `--carrier-out-dir` to `references/wave3-live-handoff-queue.json`'s live command |
| `herdr-local-handoff-queue.json` | #466 real managed-agent lifecycle — `NOT_EXERCISED` durable blocked receipt via PR #516 | terminal clean lifecycle PASS still required; blocker is now the herdr-0.8.0 `AgentInfo` API contract, not host permission |
| `source-evidence-local-handoff-queue.json` | #512 immutable source packet → existing closure ledger using #467 compiler — first packet (`issue #435`) `EXECUTED` via PR #516 | deterministic binding PASS landed (dispositions `OPEN`×2 / `NOT_APPLICABLE`×1); truth/verification and the repair itself remain separately typed and open |

The three queue JSON files themselves are unchanged by this pass (out of this document's writable lease); the table above describes their outcome, not their content. All queues still bind the receipt subject `249abc47847f8295b1c75c9d4c84457c5126fd89` / `a24b9b7ace6f4022967d41262ecdc704d5c11646` and rollback `d5993267e03b217dcdab9702dab0400ab03df860`. Queue validation proves only the continuation contract.

## Runtime data flow

```text
current admitted implementation subject
→ owning issue and exact queue
→ local capability/permission/source materialization
→ bounded command execution
→ content-bound receipt
→ independent controller or source readback
→ independent Shadow on the same subject
→ issue-specific close gate
→ repository Human admission when code changes
```

## Evidence ceilings

```text
#507 deterministic result-tree repair         PASS / MERGED
#508 durability + executor/result schema      PASS / CLOSED_DETERMINISTICALLY (PR #516); live #464 acceptance separate
#464 fresh signed-in v2 acceptance            NOT_EXERCISED; queue recompile required against
                                               current main (re-derive via git rev-parse main; do
                                               not bind to 129f53c — stale, main has since advanced
                                               to 28f3947 then 5341885 then 674cfe1, PR #577)
#466 terminal clean Herdr lifecycle           NOT_EXERCISED / blocker RECLASSIFIED to herdr-0.8.0 API contract mismatch
#467 source compiler/binding method            COMPLETED_DETERMINISTICALLY
#512 Issue/Article/PDF/PRD truth execution     EVIDENCE_DEPENDENT / OPEN; first packet (issue #435) EXECUTED, dispositions OPEN x2 / NOT_APPLICABLE x1
entropy method                                ADMITTED_ON_MAIN
general cross-repository safe deletion        NOT_CLAIMED
Draft knowledge/AE stacks                     HOLD (as of 129f53c) → **now CLOSED/MERGED**: the #560 portfolio
                                               wave merged #395 and closed #412/#419/#420/#450/#396 unmerged
                                               (consumed/superseded); no Draft remains open in this stack; #434
                                               was already closed unmerged before this pass
release / production promotion                NOT_PERFORMED
```

Rollback for the #507 implementation is `d5993267e03b217dcdab9702dab0400ab03df860`. Rollback for #516 is `88ce642a7f198d88019aa8ae19e63631ae4999c2` (the #511 merge; rolling back further would also revert the #511 admission). A future queue or documentation update must read current `main` again before acting.
