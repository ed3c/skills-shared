# Codex SDK Tech Lead Control Plane — Shadow-monitored trace

Status: `STATIC_DETERMINISTIC_CONVERGENCE_REVALIDATION_REQUIRED`.

This document is the human trace for issues #375–#379. Machine/runtime authority remains with exact Git ancestry, schemas/checkers, current GitHub metadata, hosted workflows, provider/runtime receipts and Human repository policy. A green earlier convergence is historical the moment any consumed sibling head moves.

## Current epoch

Current repository base observed for this convergence family:

```text
main@4ca9417b1da5ff32f1d4d3e7af64a15908749024
```

Current sibling heads to be consumed by #379:

```text
#375 / PR #451  86f9e8d940b76cb71b713c098ff09cb68eb4e0c1  SIBLING
#376 / PR #452  426fb6f6f548f71572d4402e73e0b05ecf6f8aa8  SIBLING
#377 / PR #453  5b6e58d1e7e9e127123dbb4a9189b98e5ff973cf  SIBLING
#378 / PR #454  32c5425de1cf4f083bd998e81873a86af8771e1e  SIBLING
#380            7a9d68fcd58b1ed78ed6d05595a8df7eae53f5a5  DOCUMENTATION SIBLING
```

Current hardened-parent refresh already recorded in Git:

```text
5d21ecab137cb26586ef1636dc279ee29733e913
parents:
  prior #455 convergence head 35874af7a6d04783983b05c8f1b1e402471b4451
  #451 current head            86f9e8d940b76cb71b713c098ff09cb68eb4e0c1
  #452 current head            426fb6f6f548f71572d4402e73e0b05ecf6f8aa8
```

The mutable final #455 head is deliberately **not** self-embedded. Read it from GitHub after every convergence edit. The static/hardened epoch becomes current only after exact-head hosted gates and independent Shadow readback complete again.

## Historical convergence epochs

Epoch 1 remains immutable evidence, not current truth:

```text
c0f6979f80038394350aea724c598c8dba5ac338
parents:
  ccef97dedd7ea8b1873e3afa130ca82b8eabb413  historical main
  339ae874b070fb3a8a5fa89b0241d90434257e99  historical #451 head
  b5295df681d6471b19775db38860b2d151339879  historical #452 head
  5b6e58d1e7e9e127123dbb4a9189b98e5ff973cf  #453
  32c5425de1cf4f083bd998e81873a86af8771e1e  #454
union tree:
  37cb2c56e7dfc939cacaa0f65cf8f9b0f8318b22
```

Documentation was then admitted through:

```text
af427a13a7096df91d74a48c0a4ca6ce3f3e2ac9
parents: c0f6979f... + PR #380 head 7a9d68fc...
```

Shared routes/tests were added and current-main-at-the-time refreshed through `35874af7...`. That head passed Skill Suites, Shared Skills Infra, Skill Eval Contract and Git Town Stacked PR Worker, and received a Shadow `ELIGIBLE_FOR_HUMAN_ADMIT` verdict **for Epoch 1 only**. The verdict was superseded when #451/#452 moved.

Rejected first candidates remain visible:

```text
#444 → #451
#445 → #452
#446 → #453
#447 → #454
```

They were closed unmerged after commit-role provenance failed. Failure lineage is not erased to make the successful path appear cleaner.

## Ownership

```text
agentic-tech-lead-orchestration
  semantic task/capability/dual-DAG law, leases, Worker admission, convergence, handoff

Codex SDK adapter (#375)
  one bounded task/session attempt and runtime-result receipt

GitHub Issue DAG adapter (#376)
  durable completion-edge projection/readback plus remote preflight

Herdr observer (#377)
  optional process/worktree/session observation only

problem-closure ledger (#378)
  source→problem→task/DAG→session/evidence→Shadow reconciliation

#379 convergence
  shared run-all / Agent routes / README / Shadow / Git Town / traceability

Human / repository authority
  semantic conflict, unmanaged dependency deletion, merge, release, promotion, rollback
```

## Directory → State Machine responsibility

```text
skills/agentic-tech-lead-orchestration/
├── SKILL.md
│   └── provider-neutral request/contract/capability/task DAG/lease/convergence/handoff law
├── references/
│   ├── core task/capability/scheduler/dual-DAG/queue contracts
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
│   └── execution-packets/375..378                        frozen task packets
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

skills/procedural-shadow-runtime/
└── independent same-subject applicability/contradiction/evidence-ceiling review

skills/git-town-stacked-pr-worker/
└── molecular relation/index vocabulary and terminal branch/PR traceability

docs/traceability/
└── human projections; never a second machine authority
```

## End-to-end State Machine

```text
SOURCE / ISSUE / ARTICLE / PDF / PRD
→ REAL_PROBLEM_BOUND
→ SYSTEM_CONTRACT_EXTRACTED
→ TASK_DAG_COMPILED
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
→ INDEPENDENT_SHADOW_RECONCILIATION
→ PR / CONVERGENCE DELIVERY
→ CI / EXACT-HEAD READBACK
→ PROBLEM_CLOSURE_RECOMPUTED                  #378
→ NEXT_WAVE | LOCAL_HANDOFF | HUMAN_ADMIT_REQUIRED
```

A Herdr terminal `done`, Codex model prose, issue close, PR merge, workflow green, article/PDF prose or documentation update cannot skip a state.

## #375 — subscription-safe Codex SDK runtime adapter

Current deterministic mechanism binds:

```text
task_id + attempt_id
exact 40-hex base commit + tree
clean Git worktree
repository-relative allowed/read-only path leases
prompt + digest
predecessor receipts
new | resume-compatible thread policy
```

Before `openai-codex` is invoked, the adapter verifies the worktree exists, is a Git worktree, has exact `HEAD == base_sha`, exact `HEAD^{tree} == tree_sha`, and is clean. After the turn, it reads changed/untracked paths and rejects any read-only or out-of-lease mutation. `Sandbox.workspace_write` therefore does not make path leases documentary-only.

Durable control-plane state excludes API keys, access/refresh tokens, browser-login artifacts, full model prose and private reasoning. Existing signed-in Codex/ChatGPT authentication is reused on the live path; no repository API key is required.

Current deterministic selftest denominator:

```text
positive=4
mutations=14
live=NOT_EXERCISED
```

A live SDK turn remains `RUNTIME_RESULT_ONLY`; independent source/diff/test acceptance still follows.

## #376 — GitHub Issue Dependencies projection

The portable DAG retains two semantic edges:

```text
start-readiness
completion-readiness
```

Only explicitly marked completion-readiness edges may project to GitHub `blockedBy`.

Before live mutation, the adapter binds/re-reads:

```text
exact owner/name repository
visibility
expected default branch
every issue number + expected OPEN/CLOSED state
closing pull-request references exposed by closedByPullRequestsReferences
```

It refuses repository identity/visibility/default-branch drift, stale issue state, more than one open **closing-reference** PR, cycle/self/unknown-node defects, malformed readback, graph-digest drift and extra unmanaged remote blockers. `--apply` may add missing managed blockers only; extra blockers fail before mutation and are not auto-deleted. Preflight must remain stable across mutation/readback.

Important ceiling: `closedByPullRequestsReferences` proves the closing-reference surface. It does **not** by itself prove uniqueness across every possible GitHub development-link/cross-reference mechanism. Generic linked-PR ownership remains residual until a broader exact readback is implemented/admitted.

Current deterministic selftest denominator:

```text
positive=6
mutations=17
live=NOT_EXERCISED
```

Live dependency mutation/readback against an admitted issue graph remains separate evidence.

## #377 — Herdr optional observer

Herdr remains optional and non-authoritative:

```text
worktree allocated
→ optional target
→ pane/workspace/process/native-session/foreground_cwd identity
→ RUNNING | BLOCKED | IDLE | DONE_CANDIDATE | UNKNOWN
→ controller readback required
```

`foreground_cwd` binds the observed process to the expected worktree by default. Absence emits `UNAVAILABLE_FALLBACK` and preserves direct Codex SDK + standard git worktree execution. Transcript/private reasoning/credential bodies are not durable receipt truth.

Current deterministic denominator: `positive=4, mutations=9, live=NOT_EXERCISED`.

## #378 — problem closure

```text
source identity + exact location
→ problem id
→ applicability / superseded route
→ exact repo/commit/tree
→ task + DAG + GitHub issue
→ session / attempt / worktree
→ implementation evidence
→ typed verification evidence + matching receipts
→ merge provenance only
→ Shadow verdict
→ residual gaps
→ independently recomputed closure
```

Allowed closure values:

```text
OPEN
PARTIAL
IMPLEMENTED_UNVERIFIED
VERIFIED_LOCAL
VERIFIED_LIVE
NOT_APPLICABLE
HUMAN_ADMIT_REQUIRED
```

Issue close/PR merge are not verification lanes, local/CI cannot promote to provider-live, and the Markdown renderer remains a human projection after JSON validation.

Current deterministic denominator: `positive=4, mutations=11`; real article/PDF/provider claims remain evidence-dependent.

## #379 shared convergence gate

The exact convergence subject must contain the current sibling bytes **before** the shared gate is wired/read. Required gates are unconditional:

```text
6 Draft-2020-12 schemas
problem-closure example
codex_sdk_controller_selftest.py             4 / 14
github_issue_dag_selftest.py                 6 / 17
herdr_observer_selftest.py                   4 / 9
problem_closure_selftest.py                  4 / 11
closure checker + Markdown non-authority marker
existing ATL full suite
```

No `if file exists` bypass is accepted.

Hosted admission denominator for the **final current #455 head** must include:

```text
Skill Suites
Shared Skills Infra
Skill Eval Contract
Git Town Stacked PR Worker
```

The earlier all-green `35874af7...` run is historical after parent movement. The current hardened-parent convergence must rerun every required hosted gate before Shadow may emit a new current verdict.

## Molecular relations

```text
#375 SIBLING
#376 SIBLING
#377 SIBLING
#378 SIBLING
#380 DOCUMENTATION SIBLING
#379 CONVERGENCE consuming exact current sibling heads
Shadow EXTERNAL_EVIDENCE / PROCESS_DEPENDENCY
live Codex / GitHub mutation / Herdr / real source closure EXTERNAL_EVIDENCE
```

A multi-parent convergence records consumed sibling bytes without making the siblings children of one another.

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

## Current residual/evidence ceiling

```text
#375 static mechanism with worktree/lease readback      IMPLEMENTED / awaiting current convergence revalidation
#375 live Codex SDK execution                           NOT_EXERCISED
#376 static projection + remote preflight mechanism     IMPLEMENTED / awaiting current convergence revalidation
#376 generic linked-PR ownership beyond closing refs    RESIDUAL
#376 live GitHub dependency mutation/readback           NOT_EXERCISED
#377 static observer mechanism                          IMPLEMENTED / awaiting current convergence revalidation
#377 live stale/orphan/residue observation              NOT_EXERCISED
#378 deterministic closure mechanism                    IMPLEMENTED / awaiting current convergence revalidation
#378 real article/PDF/provider closure                  EVIDENCE_DEPENDENT
#379 shared route/test/index convergence                REVALIDATING current parent epoch
merge/release                                           HUMAN_ADMIT_REQUIRED
```

Only after the current final #455 head passes the complete hosted denominator and independent Shadow readback may the static/deterministic convergence return to `ELIGIBLE_FOR_HUMAN_ADMIT`. That verdict still does not prove any live lane or authorize merge/release.
