# Codex SDK Tech Lead Control Plane — Shadow-monitored trace

Status: `STATIC_DETERMINISTIC_CONVERGENCE_REVALIDATING`.

This is the human trace for issues #375–#379. Machine/runtime authority remains exact Git ancestry, schemas/checkers, current GitHub metadata, exact-head workflow runs, runtime/provider receipts, and Human repository policy. A convergence branch may consume unmerged candidate bytes for integration proof; that consumption is not admission or merge.

## Current convergence epoch

Repository base observed for this family:

```text
main@4ca9417b1da5ff32f1d4d3e7af64a15908749024
```

Selected sibling candidates:

```text
#375 / PR #451  86f9e8d940b76cb71b713c098ff09cb68eb4e0c1  SIBLING / UNMERGED CANDIDATE
#376 / PR #452  426fb6f6f548f71572d4402e73e0b05ecf6f8aa8  SIBLING / UNMERGED CANDIDATE
#377 / PR #456  23b03826b1bf8fe66bd731716466a9349d3242d6  SIBLING / UNMERGED CANDIDATE
#378 / PR #457  ac5ddc0287eb4e4156a7c7eef178b7be8bbd1d34  SIBLING / UNMERGED CANDIDATE
PR #380            7a9d68fcd58b1ed78ed6d05595a8df7eae53f5a5  DOCUMENTATION SIBLING
```

The current #379 integration ancestry checkpoint is:

```text
ed852502437570c7c86bae12c07c16a3f5d37ea8
parents:
  c306b3b4cea797f5f4d1323f8ec7fcd94a94f3ec  prior #455 convergence head
  23b03826b1bf8fe66bd731716466a9349d3242d6  #456 exact candidate
  ac5ddc0287eb4e4156a7c7eef178b7be8bbd1d34  #457 exact candidate
```

The final mutable PR #455 head is deliberately not self-embedded. Read it from GitHub after every convergence edit. The checkpoint proves exact byte consumption only; #456/#457 remain unmerged candidates.

## Historical denominator

Historical convergence and rejected/superseded candidates remain visible:

```text
c0f6979f80038394350aea724c598c8dba5ac338  epoch-1 integration
35874af7a6d04783983b05c8f1b1e402471b4451  historical all-green convergence
5d21ecab137cb26586ef1636dc279ee29733e913  #451/#452 hardened-parent refresh
c306b3b4cea797f5f4d1323f8ec7fcd94a94f3ec  pre-#456/#457 convergence head

#444 → #451
#445 → #452
#446 → #453 → #456
#447 → #454 → #457
```

#446/#447 were rejected provenance candidates. #453/#454 were provenance-correct replacements later closed unmerged. They remain historical evidence and are not current merge candidates.

## Ownership planes

```text
agentic-tech-lead-orchestration
  semantic task/capability/dual-DAG law, leases, Worker admission, convergence, handoff

#375 Codex SDK adapter
  one bounded task/session attempt + runtime-result receipt

#376 GitHub Issue DAG adapter
  durable completion-edge projection/readback + remote preflight

#377 Herdr observer
  optional worktree/process/session/freshness/liveness/cleanup observation only

#378 problem-closure ledger
  frozen source/problem denominator + exact-subject evidence reconciliation

#379 convergence
  exact sibling-byte consumption + shared tests/routes/README/Shadow/Git Town/traceability

Shadow
  independent same-subject contradiction/denominator/evidence-ceiling review; no second writer

Human / repository authority
  semantic conflict, unmanaged dependency deletion, sibling admission, merge, release, promotion, rollback
```

## Directory → State Machine responsibility

```text
skills/agentic-tech-lead-orchestration/
├── SKILL.md
│   └── provider-neutral request/task/capability/dual-DAG/lease/convergence/handoff law
├── references/
│   ├── core task/capability/scheduler/queue contracts
│   ├── contracts/
│   │   ├── codex-session-manifest.schema.json            #375
│   │   ├── codex-worker-result.schema.json               #375
│   │   ├── github-issue-dag-receipt.schema.json          #376
│   │   ├── github-ready-wave.schema.json                 #376
│   │   ├── herdr-observer-receipt.schema.json            #377
│   │   └── problem-closure.schema.json                   #378
│   ├── examples/
│   │   ├── herdr-runtime-binding.example.json            #377
│   │   └── problem-closure.example.json                  #378
│   └── execution-packets/375..378
├── modules/
│   ├── codex-sdk-controller.md                           #375
│   ├── github-issue-dag-projection.md                    #376
│   ├── herdr-runtime-observer.md                         #377
│   └── problem-closure-ledger.md                         #378
├── scripts/
│   ├── run_codex_sdk_worker.py                           #375
│   ├── github_issue_dag_projection.py                    #376
│   ├── herdr_runtime_observer.py                         #377
│   ├── check_problem_closure.py                          #378
│   └── render_problem_closure.py                         #378
└── tests/
    ├── codex_sdk_controller_selftest.py                  #375
    ├── github_issue_dag_selftest.py                      #376
    ├── herdr_observer_selftest.py                        #377
    └── problem_closure_selftest.py                       #378
```

## End-to-end State Machine

```text
SOURCE / ISSUE / ARTICLE / PDF / PRD
→ REAL_PROBLEM_BOUND
→ SYSTEM_CONTRACT_EXTRACTED
→ TASK_DAG_ASSERTED
→ GITHUB_PROJECTION_COMPILED                  #376
→ REMOTE_PREFLIGHT_BOUND
→ REMOTE_READBACK_REQUIRED
→ READY_WAVE_COMPUTED
→ SESSION_PACKET_COMPILED                     #375
→ EXACT_WORKTREE_SUBJECT_BOUND
→ CODEX_THREAD_STARTED | COMPATIBLE_RESUME
→ ATTEMPT_EXECUTED
→ STRUCTURED_RESULT_COLLECTED
→ POST_TURN_LEASE_READBACK
→ CONTROLLER_SOURCE_DIFF_TEST_READBACK_REQUIRED
→ HERDR_OBSERVATION_OPTIONAL                  #377
→ FRESHNESS_LIVENESS_CLEANUP_ASSERTED
→ INDEPENDENT_SHADOW_RECONCILIATION
→ PROBLEM_DENOMINATOR_RECOMPUTED              #378
→ EXACT_HEAD_HOSTED_REVALIDATION              #379
→ NEXT_WAVE | LOCAL_HANDOFF | HUMAN_ADMIT_REQUIRED
```

A Herdr terminal `done`, Codex model prose, issue close, PR merge, workflow green, article/PDF prose, or documentation update cannot skip a state.

## #375 — Codex SDK runtime adapter

Deterministic mechanism:

```text
task/attempt/repo
+ exact 40-hex base commit/tree
+ clean Git worktree
+ repository-relative writable/read-only leases
+ prompt digest + predecessor receipts
+ new | resume-compatible thread policy
→ optional live SDK turn
→ changed/staged/untracked path readback
→ refuse read-only or out-of-lease mutation
```

Deterministic denominator: `positive=4 / mutations=14`.

Evidence ceiling: live SDK `NOT_EXERCISED`; even a live turn is `RUNTIME_RESULT_ONLY` until independent source/diff/test acceptance.

## #376 — GitHub Issue Dependencies projection

Only completion-readiness edges may project to `blockedBy`. Before mutation the adapter binds repository owner/name, visibility, default branch, issue identity/expected state and closing-PR references. Missing/extra edge drift, stale issue state and extra unmanaged blockers fail closed; `--apply` never auto-deletes unmanaged blockers.

Deterministic denominator: `positive=6 / mutations=17`.

Evidence ceiling: live dependency mutation/readback `NOT_EXERCISED`; generic development-link ownership beyond `closedByPullRequestsReferences` remains residual.

## #377 — Herdr optional observer v3

Current v3 candidate binds:

```text
exact 40-hex base/tree
+ owner/name repo
+ foreground worktree
+ pane/workspace/PID/native session
+ PID start-time identity
+ bounded observation timestamp/freshness
+ nonterminal process liveness
+ terminal cleanup_state + residue_count
```

Stale/future observation, PID reuse, dead nonterminal process, orphan session, dirty cleanup or residue fail closed. `DONE_CANDIDATE` requires clean terminal evidence but remains advisory and still requires controller source/diff/test readback. Herdr absence emits `UNAVAILABLE_FALLBACK`.

Deterministic denominator: `positive=4 / mutations=18`.

Evidence ceiling: live Herdr observation `NOT_EXERCISED`.

## #378 — problem-closure ledger v3

Current v3 candidate binds:

```text
frozen problem denominator
+ canonical source manifest digest
+ per-claim digest
+ exact source kind/identity/location
+ exact 40-hex repo commit/tree
+ task/DAG/issue lineage
+ portable session/attempt/worktree identity
+ CURRENT/HISTORICAL/SUPERSEDED implementation evidence
+ exact-subject verification evidence and matching receipts
+ Shadow verdict + residual gaps
→ independently recomputed closure
```

Deleting a problem row, changing source bytes/location, using abbreviated/stale subjects, persisting machine-local paths, reusing stale verification receipts, duplicate evidence, hidden fields, or supersession to a missing/cyclic target fails closed. `SUPERSEDED` is residual (`PARTIAL`), not terminal success.

Deterministic denominator: `positive=6 / mutations=22`.

Evidence ceiling: real article/PDF/provider claim closure remains `EVIDENCE_DEPENDENT`.

## #379 shared convergence gate

The convergence subject must contain the selected exact sibling bytes **before** the shared gate runs. Required deterministic gates are unconditional:

```text
6 Draft-2020-12 control-plane schemas
problem-closure example
codex_sdk_controller_selftest.py             4 / 14
github_issue_dag_selftest.py                 6 / 17
herdr_observer_selftest.py                    4 / 18
problem_closure_selftest.py                   6 / 22
closure checker + Markdown non-authority marker
existing ATL full suite
```

No `if file exists` bypass is accepted.

Hosted final-head denominator:

```text
Skill Suites
Shared Skills Infra
Skill Eval Contract
Git Town Stacked PR Worker
```

Every selected sibling head move supersedes earlier convergence workflow and Shadow evidence. The final PR #455 head must rerun the hosted denominator after this epoch's route/index refresh.

## Molecular relations

```text
#375 SIBLING / unmerged candidate
#376 SIBLING / unmerged candidate
#377 SIBLING / unmerged candidate
#378 SIBLING / unmerged candidate
#380 DOCUMENTATION SIBLING
#379 CONVERGENCE CANDIDATE consuming exact selected heads
Shadow EXTERNAL_EVIDENCE / PROCESS_DEPENDENCY
live Codex / GitHub mutation / Herdr / real source closure EXTERNAL_EVIDENCE
```

A multi-parent convergence records byte consumption without making the siblings children of one another or admitted by ancestry alone.

## Cold-start route

```text
root AGENTS.md
→ CONTEXT.md / ARCHITECTURE.md
→ docs/INDEX.md + docs/architecture/STATE_MACHINES.md
→ docs/traceability/AGENTS.md
→ this trace
→ agentic-tech-lead-orchestration/AGENTS.md + README + SKILL.md
→ selected execution packet + module/contracts only
→ procedural-shadow-runtime README
→ git-town-stacked-pr-worker README
→ issues #375–#379 / current PR metadata
→ exact Git/workflow/runtime/receipt subjects
```

Chat history is not required.

## Current residual / evidence ceiling

```text
#375 deterministic mechanism candidate             IMPLEMENTED / convergence revalidating
#375 live Codex SDK execution                      NOT_EXERCISED
#376 deterministic projection candidate            IMPLEMENTED / convergence revalidating
#376 generic linked-PR ownership                   RESIDUAL
#376 live GitHub dependency mutation/readback      NOT_EXERCISED
#377 deterministic observer candidate v3           IMPLEMENTED / convergence revalidating
#377 live Herdr observation                        NOT_EXERCISED
#378 deterministic closure candidate v3            IMPLEMENTED / convergence revalidating
#378 real article/PDF/provider closure             EVIDENCE_DEPENDENT
#379 route/test/index convergence                  REVALIDATING current epoch
#451/#452/#456/#457 admission/merge                HUMAN_ADMIT_REQUIRED
#455 merge/release                                 HUMAN_ADMIT_REQUIRED
```

Only after the final current #455 head passes the complete hosted denominator and independent Shadow readback may this static/deterministic convergence become `READY_FOR_HUMAN_ADMIT`. That verdict still does not admit or merge any sibling and does not prove any live lane.
