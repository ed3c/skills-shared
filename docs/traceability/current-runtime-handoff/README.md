# Tech Lead + Shadow Architect current closure audit

Status: `CURRENT_MAIN_REBOUND_2026-08-22 / LOCAL_HANDOFF_QUEUES_EXECUTED`.

This is the current cold-start route for issue/PR closure decisions after PR #516 executed the three sibling Local Handoff Execution Queues bound by #511 and merged into main. It records what is admitted, what was closed only as consumed lineage, and what still requires a local/runtime or source-evidence lane. It does not replace current GitHub metadata or executable receipts.

## Exact subjects

```text
repository                 ed3c/skills-shared
observed_at                2026-08-22 (GitHub per-issue/per-PR readback plus local Git readback)
current admitted main      5341885f26b5e8e7baf5087a4d661e324f878242
current tree               a18e12507f9e621efd5354f58384eded1f1e2a9a
rollback / pre-convergence 9fe3c6daf53dcdd61123d5d7a4eeedbdf37b5d7c
```

HISTORICAL subjects — receipt- and queue-bound, not current `main`:

```text
#507 checked head          e306797fdbf4875bafd410fd415e6bcb3587ff9b
#507 merge subject         249abc47847f8295b1c75c9d4c84457c5126fd89
#516 merge subject         129f53c23a3ab15354763167b25bddc45f724c00
                           (this document previously pinned it as "current admitted main"; it is 284 commits behind the epoch above)

#508 result-carrier receipt (data/handoff/codex-v2/issue-508-result-carrier-receipt.json)
  implementation_commit    243635885f7bcff64c606dffe7fcbe09ada9c5b2
  parent_commit            249abc47847f8295b1c75c9d4c84457c5126fd89
```

`249abc47…` is the receipt's `parent_commit` and the subject the Wave-3 continuation queues were executed on under PR #516 — it is not the commit the #508 receipt binds its implementation to. Do not describe it as "the receipt-bound subject", and do not assume any queue still binds it: read each queue's own `subject` field.

PR #507 was reviewed on its exact head, passed Skill Eval Contract, Shared Skills Infra, Skill Suites, and the `agentic-tech-lead-orchestration` matrix leg, then merged without head substitution. It repairs the central first-live-run false PASS by binding acceptance to a Git result tree whose exact base-to-result changed-path denominator is independently recomputed.

PR #516 executed the three ACTIVE Local Handoff Execution Queue items — #508, #466, #512 — on the exact bound queue subject `249abc47847f8295b1c75c9d4c84457c5126fd89` (branches cut from that subject; the docs-only delta to the then-current main verified as an empty diff against the owning scripts), then integrated into main as `129f53c23a3ab15354763167b25bddc45f724c00`. Independent Shadow readback on the candidate: `ADMIT` (forbidden delta absent; live lanes truthfully `NOT_EXERCISED`; noncritical findings owned by #512 and #466). Both subjects are historical: `main` has since advanced to the epoch above.

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
| ARTICLE/PDF/PRD or further Issue truth/applicability | `EVIDENCE_DEPENDENT / #512 OPEN (first packet executed via PR #516)` | first immutable source packet executed: GitHub issue #435 bytes + provenance + claim packet compiled against `#467`'s method into `data/handoff/source-evidence/problem-closure-ledger.json`; compiler/closure-checker exit 0 (binding PASS only); dispositions `OPEN` (six unclassified commits still need `evals/commit-roles.json` repair), `OPEN` (repair not yet executed), `NOT_APPLICABLE` (scope-only evidence-boundary claim); compiler PASS is not source truth — and at this epoch that boundary has **no deterministic checker**: `check_problem_closure.py` has no `--source-dir` flag (`grep -c 'source_dir\|source-dir'` on the script → 0), so its digest chain closes entirely inside the ledger file and no gate re-derives `claim_sha256` from the persisted bytes under `data/handoff/source-evidence/sources/`. The checker-side repair is owned by #512, not by this document |
| Repository entropy method + deterministic gate + domain ports + controls + CI/registry arrival | `HUMAN_ADMITTED_ON_MAIN` | rebuilt and landed through UCR admission PR #477; old C/K/A/E/X PRs remain closed-unmerged lineage |
| Entropy nearest Agent/README routes and terminal Molecular index | `IMPLEMENTED_BY_THIS_AUDIT_CANDIDATE` | issue #403 / PR #404 is closed only after this exact candidate lands and hosted routing gates pass |
| codex-v2 queue's #508 item is complete on an admitted subject | `RECOMPILED_ONTO_THE_EPOCH` | per the subject-mutation law the successor #464 queue must bind the **current** admitted subject `5341885f26b5e8e7baf5087a4d661e324f878242` / tree `a18e12507f9e621efd5354f58384eded1f1e2a9a` — not `129f53c2…`, which this document used to name and which is itself stale. That recompile is the queue writer's work and landed in this convergence; read the queue file for its current ACTIVE item. Separately, `references/wave3-live-handoff-queue.json` used to invoke `run_codex_sdk_worker.py --execute` without `--carrier-out-dir`, which `run_codex_sdk_worker.py:435-436` rejects with an unconditional `parser.error`; this convergence repaired the queued command to carry the flag, so the argparse death is historical. The live run itself remains `NOT_EXERCISED` and is owned by #464 |

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
      #508 is now CLOSED/COMPLETED on an admitted subject; its successor queue must bind
      the current admitted subject 5341885f26b5e8e7baf5087a4d661e324f878242
      (tree a18e12507f9e621efd5354f58384eded1f1e2a9a), never the stale 129f53c2;
      then a fresh signed-in v2 run remains required and NOT_EXERCISED

#466  OPEN
      live Herdr lane attempted; blocker RECLASSIFIED via PR #516 from host-permission
      to a herdr-0.8.0 API contract mismatch (no observation timestamp, process identity,
      or cleanup facts on AgentInfo); durable NOT_EXERCISED receipt landed, sample_count 0

#508  CLOSED / COMPLETED (2026-08-22 readback; this document previously read ELIGIBLE_TO_CLOSE)
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
| #412 | `CLOSED_UNMERGED / SUPERSEDED` | the stated provenance blocker was falsified (`988a4e7` carve-out, gate GREEN on #412's own range); its bytes landed through the replayed #419; branch preserved as forensic source — `references/closure-audit/issue-568.json:8,17` |
| #419 | `CLOSED_UNMERGED / CONSUMED` | merge-forward into the #573 landing, superset proven per-path — `references/closure-audit/issue-568.json:9,18` |
| #420 | `CLOSED_UNMERGED / CONSUMED` | re-parented onto the replayed #419 (restoring `assert_case_obligations.py`), then consumed — `references/closure-audit/issue-568.json:9,19` |
| #450 | `CLOSED_UNMERGED / CONSUMED` | consumed through the same replay chain — `references/closure-audit/issue-568.json:9,20` |
| #434 | `CLOSED_UNMERGED (2026-08-21)` | closed on GitHub before this pass; Productization rebuild remains owned by #436, which is itself now CLOSED |
| #395 | `MERGED` | auto-merged by reachability at the #573 landing — `references/closure-audit/issue-568.json:12,21` |
| #396 | `CLOSED_UNMERGED / CONSUMED` | trace child consumed by the same landing — `references/closure-audit/issue-568.json:22` |
| #573 | `MERGED` | landing subject for the whole set: commit `9fe3c6daf53dcdd61123d5d7a4eeedbdf37b5d7c`, tree `c17678166cee2adba2f92f6099011ec52716ece7` — `references/closure-audit/issue-568.json:16,24` |
| #577 | `DRAFT / CONSUMED_BY_THIS_CONVERGENCE` | branch `agent/dtcr-handoff-audit`, head `bca08001`; its bytes are the base of this convergence and it is expected to read `MERGED` by reachability once the convergence lands. Until that happens it is not merged |

At the 2026-08-22 readback there is **exactly one open PR in the repository: #577**, the carrier of this convergence. The five PRs this table previously listed as open `DRAFT / HOLD` (#412, #419, #420, #450, #395→#396) all reached terminal states above; no `MERGEABLE` claim in this document is a current fact any more, and `MERGEABLE` never meant readiness in the first place. Old green runs do not follow a moving base.

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
├── git-at-any-scale-local-handoff-queue.json
├── herdr-local-handoff-queue.json
├── source-evidence-local-handoff-queue.json
└── spatial-407-local-handoff-queue.json
    └── exact local/runtime continuation contracts; every queue JSON in that
        directory is one, and each binds its own subject

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
#508 / PR #516  durable carrier + executor provenance + result schema  PASS / CLOSED / COMPLETED
        ↓ subject admitted; main has since advanced to 5341885f — successor queue binds that
#464             fresh signed-in Codex v2 execution + controller + Shadow  OPEN / QUEUE_RECOMPILE_REQUIRED

#466 / PR #516   Herdr managed lifecycle receipt   SIBLING / EXTERNAL_RUNTIME; NOT_EXERCISED, blocker RECLASSIFIED
#467             source compiler method             COMPLETE / HISTORICAL METHOD
#512 / PR #516   immutable source packet + closure  SIBLING / SOURCE_EVIDENCE; first packet EXECUTED (issue #435)
#465             remote GitHub canary               COMPLETE / HISTORICAL RECEIPT
```

The Codex queue's #508 item is complete on an admitted subject, and #508 itself is CLOSED/COMPLETED. Per the subject-mutation law the #464 successor is a NEW queue bound to the current admitted subject `5341885f26b5e8e7baf5087a4d661e324f878242` / tree `a18e12507f9e621efd5354f58384eded1f1e2a9a`, not an advance of the #508 queue and not a binding to `129f53c2…`, which this document previously named and which is now itself 284 commits behind.

## Local Handoff queues

| Queue | ACTIVE item | Exit |
|---|---|---|
| `codex-v2-local-handoff-queue.json` | #508 durable result carrier/provenance/schema — `PASS` via PR #516; successor #464 lane recompiled onto the epoch subject in this convergence | the #464 queue must bind `5341885f26b5e8e7baf5087a4d661e324f878242`; the live command in `references/wave3-live-handoff-queue.json` was repaired in this convergence to carry `--carrier-out-dir` (it previously died at `run_codex_sdk_worker.py:436`); the fresh signed-in run stays `NOT_EXERCISED` |
| `herdr-local-handoff-queue.json` | #466 real managed-agent lifecycle — `NOT_EXERCISED` durable blocked receipt via PR #516 | terminal clean lifecycle PASS still required; blocker is now the herdr-0.8.0 `AgentInfo` API contract, not host permission |
| `source-evidence-local-handoff-queue.json` | #512 immutable source packet → existing closure ledger using #467 compiler — first packet (`issue #435`) `EXECUTED` via PR #516 | deterministic binding PASS landed (dispositions `OPEN`×2 / `NOT_APPLICABLE`×1); truth/verification and the repair itself remain separately typed and open |
| `spatial-407-local-handoff-queue.json` | #407/#411 Spatial lane — recompiled onto the epoch subject in this convergence | read `current.active_item` in the queue file; its previous ACTIVE item was a rebuild of PR #412, which is now `CLOSED_UNMERGED / SUPERSEDED` |
| `git-at-any-scale-local-handoff-queue.json` | #531/#532 Git-at-any-scale lane — recompiled onto the epoch subject in this convergence | read `current.active_item` in the queue file; the earlier committed form used `schema`/`bound_main`/`law` keys instead of the schema's required `schema_version`/`subject`/`authority`/`current` and its own gate exited 2 |

The queue JSON files are not in this document's writable lease; the table above describes each lane's outcome, not the file's content. **Each queue binds its own subject.** There is no shared subject and no fixed queue count — read the `subject` and `current.active_item` fields of the exact queue you are acting on, and never infer either from a sibling queue or from this table (`runtime-handoff/AGENTS.md:28` states the rule for the Spatial queue explicitly: do not substitute the older shared subject for it). This document previously claimed "all queues still bind the receipt subject `249abc47…`"; that was false for at least the Spatial and Git-at-any-scale queues, and the claim has been removed rather than re-pinned. Queue validation proves only the continuation contract.

`docs/traceability/dual-track-code-review-loop/LOCAL_HANDOFF_EXECUTION_QUEUE.json` is **not** one of these queues despite its filename: its `schema` is `dtcr/open-lane-index/v2` and its own `_authority` field declares it a non-authoritative navigation projection. No DTCR typed queue exists yet; compiling one is #528's deliverable.

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
#464 fresh signed-in v2 acceptance            NOT_EXERCISED; its queue must bind the current admitted subject 5341885f
#466 terminal clean Herdr lifecycle           NOT_EXERCISED / blocker RECLASSIFIED to herdr-0.8.0 API contract mismatch
#467 source compiler/binding method            COMPLETED_DETERMINISTICALLY
#512 Issue/Article/PDF/PRD truth execution     EVIDENCE_DEPENDENT / OPEN; first packet (issue #435) EXECUTED, dispositions OPEN x2 / NOT_APPLICABLE x1
entropy method                                ADMITTED_ON_MAIN
general cross-repository safe deletion        NOT_CLAIMED
Draft knowledge/AE stacks                     TERMINAL (2026-08-22): #412 SUPERSEDED, #419/#420/#450/#396 CONSUMED, #395 MERGED, all via the #573 landing 9fe3c6d; #434 closed unmerged. No open Draft stack remains
release / production promotion                NOT_PERFORMED
```

Rollback for this epoch is `9fe3c6daf53dcdd61123d5d7a4eeedbdf37b5d7c` (the #573 landing that precedes admitted main `5341885f`). Historical rollbacks: `d5993267e03b217dcdab9702dab0400ab03df860` for the #507 implementation, `88ce642a7f198d88019aa8ae19e63631ae4999c2` for #516 (the #511 merge; rolling back further would also revert the #511 admission).

Every subject and state in this document is a dated readback, not a standing guarantee: no gate enforces its freshness, and the `129f53c2…` pin it carried until 2026-08-22 went 284 commits stale without anything going red. A future queue or documentation update must re-read current `main` and current provider state before acting, and must restamp `observed_at` above when it does.
