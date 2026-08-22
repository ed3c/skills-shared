# Codex SDK Tech Lead Control Plane — Shadow-monitored trace

Status: `HISTORICAL / PRE-ADMISSION TRACE` — the #455 convergence it gates was admitted and merged (`ca31e0b1e640f0dba2c3d94da9d9786fbed32f2c`). Admitted-subject authority is [`CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md`](CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md); [`docs/INDEX.md`](../INDEX.md) already routes this file as the pre-admission trace.

This is the human trace for issues #375–#379. Machine/runtime authority remains exact Git ancestry, schemas/checkers, current GitHub metadata, exact-head workflow runs, runtime/provider receipts, and Human repository policy. A convergence branch may consume unmerged candidate bytes for integration proof; that consumption is not admission or merge.

## Convergence epoch (HISTORICAL — superseded by the #455 admission)

Repository base observed for this family at compile time — historical, 364 commits behind the current admitted `main` `5341885f26b5e8e7baf5087a4d661e324f878242` (2026-08-22 readback):

```text
main@4ca9417b1da5ff32f1d4d3e7af64a15908749024
```

Selected sibling candidates, with the terminal state each reached (see [`AGENTS.md`](AGENTS.md), Wave-2 control-plane admission):

```text
#375 / PR #451  86f9e8d940b76cb71b713c098ff09cb68eb4e0c1  SIBLING / CLOSED_UNMERGED / CONSUMED by #455
#376 / PR #452  426fb6f6f548f71572d4402e73e0b05ecf6f8aa8  SIBLING / CLOSED_UNMERGED / CONSUMED by #455
#377 / PR #456  6a2ebcbe87078cecaf67f82f3c9c10643bcc9123  SIBLING / CLOSED_UNMERGED / CONSUMED by #455
#378 / PR #457  ac5ddc0287eb4e4156a7c7eef178b7be8bbd1d34  SIBLING / CLOSED_UNMERGED / CONSUMED by #455
PR #380            7a9d68fcd58b1ed78ed6d05595a8df7eae53f5a5  DOCUMENTATION SIBLING / CLOSED_UNMERGED / CONSUMED
#379 / PR #455     847e56c3418fce920c42d983e84ee44fdc6e8971  MERGED / HUMAN_ADMITTED, merge ca31e0b1e640f0dba2c3d94da9d9786fbed32f2c
```

The fixed #377 reconciliation ancestor is:

```text
fc40cf833609328ded0141dd8d9629c9a727a159
parents:
  d52ab2aad8e20be0c738e77356f75633813ad444  prior #455 route/index head
  6a2ebcbe87078cecaf67f82f3c9c10643bcc9123  repaired #456 candidate
```

The final PR #455 head was deliberately not self-embedded while #455 was mutable. It has since merged as `ca31e0b1e640f0dba2c3d94da9d9786fbed32f2c`. The checkpoint above proves exact byte consumption only; #451/#452/#456/#457 were never merged individually — they closed unmerged as consumed siblings.

## Historical denominator

Historical convergence and rejected/superseded candidates remain visible:

```text
c0f6979f80038394350aea724c598c8dba5ac338  epoch-1 integration
35874af7a6d04783983b05c8f1b1e402471b4451  historical all-green convergence
5d21ecab137cb26586ef1636dc279ee29733e913  #451/#452 hardened-parent refresh
c306b3b4cea797f5f4d1323f8ec7fcd94a94f3ec  pre-#456/#457 convergence head
ed852502437570c7c86bae12c07c16a3f5d37ea8  rejected: corrupted Herdr source reached shared suite

d52ab2aad8e20be0c738e77356f75633813ad444  route/index projection over rejected Herdr bytes
fc40cf833609328ded0141dd8d9629c9a727a159  repaired Herdr reconciliation; hosted synchronize gates green

#444 → #451
#445 → #452
#446 → #453 → #456
#447 → #454 → #457
```

#446/#447 were rejected provenance candidates. #453/#454 were provenance-correct replacements later closed unmerged. `ed852502...` is retained because the shared ATL suite exposed non-printable corruption in the then-current Herdr script; its green predecessor evidence is not reused. These subjects remain historical evidence and are not current merge candidates.

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

The first v3 published candidate (`23b03826...`) contained corrupted non-printable script bytes that its own branch workflow did not execute because the shared `run-all.sh` wiring lives in #379. The #455 shared suite caught the `SyntaxError`; #456 was repaired to `6a2ebcbe...` without changing the 4/18 test denominator.

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

Hosted synchronize gate observed at repaired integration ancestor `fc40cf83...`:

```text
Skill Suites                         PASS
Shared Skills Infra                  PASS
Git Town Stacked PR Worker           PASS
```

`Skill Eval Contract` is sealed to `pull_request: ready_for_review`, so after the final documentation/index bytes stabilize the PR must be toggled Draft → Ready and that exact final head must pass the contract. A missing run is never PASS.

Every selected sibling head move supersedes earlier convergence workflow and Shadow evidence.

## Molecular relations

```text
#375 SIBLING / closed unmerged, consumed by #455
#376 SIBLING / closed unmerged, consumed by #455
#377 SIBLING / closed unmerged, consumed by #455
#378 SIBLING / closed unmerged, consumed by #455
#380 DOCUMENTATION SIBLING / closed unmerged, consumed by #455
#379 CONVERGENCE OWNER, merged ca31e0b1…, consuming exact selected heads
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

## Residual / evidence ceiling at Wave-2 pre-admission (historical)

Live-lane ownership has since transferred to the Wave-3 successors #464–#467 through the admitted #485 reconciliation; current ownership authority is [`WAVE3_ADMISSION.md`](WAVE3_ADMISSION.md). The rows below are the pre-admission Wave-2 snapshot.

```text
#375 deterministic mechanism candidate             IMPLEMENTED / shared suite PASS
#375 live Codex SDK execution                      NOT_EXERCISED
#376 deterministic projection candidate            IMPLEMENTED / shared suite PASS
#376 generic linked-PR ownership                   RESIDUAL
#376 live GitHub dependency mutation/readback      NOT_EXERCISED
#377 deterministic observer candidate v3           IMPLEMENTED / shared suite PASS after corruption repair
#377 live Herdr observation                        NOT_EXERCISED
#378 deterministic closure candidate v3            IMPLEMENTED / shared suite PASS
#378 real article/PDF/provider closure             EVIDENCE_DEPENDENT
#379 route/test/index convergence                  FINAL GOVERNANCE REVALIDATION
#451/#452/#456/#457 admission/merge                RESOLVED: closed unmerged / consumed by #455
#455 merge                                         MERGED / HUMAN_ADMITTED (ca31e0b1…)
#455 release                                       NOT_PERFORMED
```

The pre-admission gate read: only after the final #455 head passes the complete hosted denominator and independent Shadow readback may this static/deterministic convergence become `READY_FOR_HUMAN_ADMIT`. That gate was satisfied and #455 was admitted; the admission still merged no sibling individually and proved no live lane.

## Successor: Wave-3 live-evidence infrastructure

The static/deterministic #455 subject is the explicit true parent for the next program. Detailed machine/human routing is in [`WAVE3_LIVE_EVIDENCE.md`](WAVE3_LIVE_EVIDENCE.md); this parent trace only records the successor boundary.

```text
#455 / #379
├─ #464 / PR #469  Codex live-acceptance carrier         TRUE_CHILD
├─ #465 / PR #470  GitHub reversible dependency canary  TRUE_CHILD
├─ #466 / PR #471  Herdr lifecycle carrier              TRUE_CHILD
└─ #467 / PR #472  immutable source-claim compiler      TRUE_CHILD
          ↓ selected exact bytes
#468 / PR #473     CONVERGENCE
```

All four Wave-3 leaves consume #455 bytes and are therefore true children of #455, but they remain siblings of each other. #468 is the only shared writer for Wave-3 contracts, `run-all`, Agent routes, Shadow projection, Git Town Molecular index, traceability and Local Handoff Queue.

Immutable Wave-3 integration checkpoint:

```text
691b342c44c9c6c4e61a9997e778ae4ed6e920d5
parents:
  847e56c3418fce920c42d983e84ee44fdc6e8971  #455
  d239d17d1d718f3e5e8c1975307665cae43d3b09  #469
  f4c3215b6c52c2e6106070eaa1121dee1dbd48e3  #470
  9eb70b2b62193b62a28f243de91e51337f1906b3  #471
  44d779a02e1749aa88a502d946646c22af38a026  #472
```

This successor exists to make future live receipts safely executable and admissible. It does not retroactively change #455's historical verdict and does not itself prove Codex, Herdr, GitHub mutation or external-source truth.