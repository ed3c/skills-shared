# Codex SDK Tech Lead Control Plane — Shadow-monitored trace

Status: `STATIC_IMPLEMENTATION_CONVERGENCE_IN_PROGRESS`.

The provider-specific mechanisms for issues #375–#378 are implemented on exact sibling subjects and consumed by the #379 multi-parent convergence subject. Their **live** runtime/effect lanes remain `NOT_EXERCISED` or evidence-dependent until exact receipts exist. This document is navigation/traceability, not runtime authority.

## Exact implementation and convergence subjects

Frozen sibling heads, all based directly on `main@ccef97dedd7ea8b1873e3afa130ca82b8eabb413`:

```text
#375 / PR #451  339ae874b070fb3a8a5fa89b0241d90434257e99  SIBLING
#376 / PR #452  b5295df681d6471b19775db38860b2d151339879  SIBLING
#377 / PR #453  5b6e58d1e7e9e127123dbb4a9189b98e5ff973cf  SIBLING
#378 / PR #454  32c5425de1cf4f083bd998e81873a86af8771e1e  SIBLING
```

Each of #451–#454 independently reached exact-head:

```text
Skill Suites          SUCCESS
Shared Skills Infra   SUCCESS
Skill Eval Contract   SUCCESS
Shadow verdict        STATIC_ADMITTED
```

Their rejected predecessor candidates remain visible rather than rewritten away:

```text
#444 → #451
#445 → #452
#446 → #453
#447 → #454
```

The first #379 integration commit is:

```text
c0f6979f80038394350aea724c598c8dba5ac338
```

Its parents are current main plus all four sibling heads. Its tree `37cb2c56e7dfc939cacaa0f65cf8f9b0f8318b22` contains the exact admitted sibling blobs. Therefore Git itself records the convergence dependency without serializing the siblings into a false Stack.

PR #380 is a documentation sibling. Its exact head `7a9d68fcd58b1ed78ed6d05595a8df7eae53f5a5` is admitted as an additional documentation parent by immutable integration commit:

```text
af427a13a7096df91d74a48c0a4ca6ce3f3e2ac9
```

Both PR #380 non-merge commits carry valid `Driven-By: human` / `Driven-On: chatgpt-github-connector` trailers, so the documentation ancestry does not weaken the repository commit-role gate.

## Ownership

```text
skills-shared
  portable method + trigger-selected contracts/modules/checkers/evals + Agent routes

runtime-env / consumer runtime
  Codex SDK installation/auth state, Herdr installation, process/session execution,
  local worktree/tool/provider capabilities

consumer repository
  issue/PR identities, worktrees, branches, path/resource leases, exact commands,
  provider/session receipts and business acceptance

Human / repository authority
  semantic conflict, merge, release, visibility/access/license/permission widening,
  destructive dependency removal, rollback and promotion
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
│   └── execution-packets/375..378                        frozen zero-context task contracts
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
│   └── render_problem_closure.py                         #378 human projection
└── tests/
    ├── codex_sdk_controller_selftest.py                  #375
    ├── github_issue_dag_selftest.py                      #376
    ├── herdr_observer_selftest.py                        #377
    └── problem_closure_selftest.py                       #378

skills/procedural-shadow-runtime/
└── independent same-subject applicability/contradiction/evidence-ceiling review

skills/git-town-stacked-pr-worker/
└── Molecular relation/index vocabulary and terminal branch/PR traceability

docs/traceability/
└── human projections that route to exact Git/schema/receipt/workflow subjects
```

## End-to-end control-plane State Machine

```text
SOURCE / ISSUE / ARTICLE / PDF / PRD
→ REAL_PROBLEM_BOUND
→ SYSTEM_CONTRACT_EXTRACTED
→ TASK_DAG_COMPILED
→ TASK_DAG_ASSERTED
→ GITHUB_PROJECTION_COMPILED                  #376
→ REMOTE_READBACK_REQUIRED
→ READY_WAVE_COMPUTED
→ SESSION_PACKET_COMPILED                     #375
→ ISOLATED_WORKTREE_BOUND
→ CODEX_THREAD_STARTED | COMPATIBLE_RESUME
→ ATTEMPT_EXECUTED
→ STRUCTURED_RESULT_COLLECTED
→ CONTROLLER_SOURCE_DIFF_TEST_READBACK_REQUIRED
→ HERDR_OBSERVATION_OPTIONAL                  #377
→ INDEPENDENT_SHADOW_RECONCILIATION
→ PR / CONVERGENCE DELIVERY
→ CI / EXACT-HEAD READBACK
→ PROBLEM_CLOSURE_RECOMPUTED                  #378
→ NEXT_WAVE | LOCAL_HANDOFF | HUMAN_ADMIT_REQUIRED
```

A Herdr terminal `done`, Codex model prose, issue close, PR merge, workflow green, Google/CodexDoc link, article/PDF prose, or documentation update cannot skip a state.

## Dual DAG and GitHub projection

The controller maintains two semantic edge classes:

```text
start-readiness
  predecessor output is readable enough to begin downstream work

completion-readiness
  predecessor must be independently admitted before downstream completion
```

GitHub exposes one dependency relation. The #376 adapter therefore projects only explicitly marked `completion` edges to `blockedBy`.

```text
portable semantic dual DAG
→ validate cycle/self/duplicate/unknown-node + graph digest
→ desired GitHub blockedBy set
→ exact remote readback
→ missing managed edges may be added only on explicit --apply
→ extra remote blockers fail closed; they are never auto-deleted
→ ready-wave projection
```

GitHub dependency state is a durable collaboration projection, not semantic truth by itself.

## Codex SDK session execution

#375 binds a frozen task to one worktree/session attempt:

```text
task_id + attempt_id
repo/base/tree + worktree
allowed/read-only paths
prompt + prompt digest
predecessor receipts
new | resume-compatible thread policy
→ official openai-codex SDK
→ existing signed-in Codex/ChatGPT authentication
→ TurnResult identifiers/status
→ RUNTIME_RESULT_ONLY
→ controller source/diff/test readback still required
```

Repository paths reject absolute/`..` escapes and ancestor/descendant writable/read-only overlap. Credentials, refresh/access tokens, full model prose and private reasoning are forbidden durable control-plane fields. The adapter does not require a repository-stored API key.

## Herdr observer

Herdr is optional and non-authoritative:

```text
worktree allocated
→ optional Herdr target
→ pane/workspace/process/native-session/foreground_cwd identity
→ RUNNING | BLOCKED | IDLE | DONE_CANDIDATE | UNKNOWN
→ controller readback required
```

`foreground_cwd` binds the observed process to the expected worktree by default. Herdr absence emits `UNAVAILABLE_FALLBACK` and preserves the direct Codex SDK + git worktree path. No transcript/private reasoning/credential body becomes durable receipt truth.

## Problem closure chain

```text
source identity + exact location
→ problem id
→ applicability / superseded route where applicable
→ exact repo/commit/tree subject
→ task nodes + DAG nodes + GitHub issues
→ session / attempt / worktree trace
→ implementation evidence
→ typed verification evidence + matching receipts
→ merge subjects as provenance only
→ Shadow verdict
→ residual gaps
→ independently recomputed closure state
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

`issue closed == solved`, `PR merged == verification`, and `local/CI == provider-live` are forbidden substitutions. `render_problem_closure.py` emits a human projection only after the JSON ledger passes deterministic checking.

## #379 shared deterministic convergence gate

The convergence subject owns shared routes and test wiring after it contains the exact sibling bytes:

```text
six Draft-2020-12 control-plane schemas validated
→ problem-closure positive example validated
→ codex_sdk_controller_selftest.py             2 positive / 8 mutations
→ github_issue_dag_selftest.py                 5 positive / 9 mutations
→ herdr_observer_selftest.py                   4 positive / 9 mutations
→ problem_closure_selftest.py                  4 positive / 11 mutations
→ deterministic closure checker
→ Markdown projection non-authority marker
→ existing ATL full suite
```

Required selftests are unconditional. A missing file must make the suite fail; `if file exists` is not an accepted convergence strategy.

## Molecular delivery relations

```text
#375  SIBLING
#376  SIBLING
#377  SIBLING
#378  SIBLING
#380  SIBLING / DOCUMENTATION
#379  CONVERGENCE consuming exact sibling heads
Shadow EXTERNAL_EVIDENCE / PROCESS_DEPENDENCY for admission
live provider receipts EXTERNAL_EVIDENCE
```

A `TRUE_CHILD` appears only if an actual branch consumes another branch's named unmerged bytes as its base dependency. The current implementation siblings do not.

## Cold-start read route

```text
root AGENTS.md
→ CONTEXT.md / ARCHITECTURE.md
→ docs/INDEX.md + docs/architecture/STATE_MACHINES.md
→ docs/traceability/AGENTS.md
→ this trace
→ agentic-tech-lead-orchestration/AGENTS.md + README + SKILL.md
→ selected execution packet + selected module/contracts only
→ procedural-shadow-runtime README
→ git-town-stacked-pr-worker README
→ issues #375–#379 / current PR metadata
→ exact Git/workflow/runtime/receipt subjects
```

Chat history is not a required dependency.

## Current Shadow verdict / residual work

```text
portable Tech Lead core                         IMPLEMENTED
issue dual-DAG contract                         IMPLEMENTED
Molecular Stack method                          IMPLEMENTED
independent Shadow procedure                    IMPLEMENTED
#375 static Codex SDK mechanism                 STATIC_ADMITTED / CONSUMED_BY_#379
#376 static GitHub DAG mechanism                STATIC_ADMITTED / CONSUMED_BY_#379
#377 static Herdr observer mechanism            STATIC_ADMITTED / CONSUMED_BY_#379
#378 deterministic closure mechanism            STATIC_ADMITTED / CONSUMED_BY_#379
#380 documentation foundation                   CONSUMED_BY_#379
#379 shared route/test/index convergence        IN_PROGRESS on exact integration subject
live Codex SDK session execution                NOT_EXERCISED
live GitHub dependency mutation/readback         NOT_EXERCISED
live Herdr observation                          NOT_EXERCISED
real article/PDF/provider closure               EVIDENCE_DEPENDENT
merge/release                                   HUMAN_ADMIT_REQUIRED
```

#376 still owns live repository/default-branch/visibility, stale issue and duplicate linked-PR preflight proof. #377 still owns live stale/orphan/residue observation. #378 real source/provider claims can legitimately stay OPEN/PARTIAL/HUMAN_ADMIT_REQUIRED.

## Evidence ceiling

This trace can report exact Git ancestry, file routes, deterministic tests and hosted workflow states only after those subjects are observed. It cannot prove live Codex, live Herdr, GitHub dependency effects, provider behavior, production safety, Human Admit, merge or release.
