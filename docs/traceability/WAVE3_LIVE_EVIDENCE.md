# Wave 3 live-evidence control plane — Tech Lead + Shadow trace

Status: `STATIC_INFRA_ADMITTED / GITHUB_REMOTE_CANARY_EXERCISED`.

This document records the public-repository mechanism and current evidence for live Codex SDK, GitHub Issue Dependencies, Herdr lifecycle, and source-claim lanes. The static/deterministic Wave‑3 control plane is admitted on `main`; the GitHub dependency lane now also has one bounded remote add/readback/remove/restore receipt. Codex, Herdr, source/provider, release, promotion, and production lanes remain separate and are not promoted by the GitHub receipt. Machine authority remains exact Git ancestry, contracts/checkers, current GitHub metadata, exact-head hosted workflows, runtime receipts, source readback, and Human repository policy.

## Molecular DAG

At Wave‑3 fork time the four leaves directly consumed #455 exact head `847e56c3418fce920c42d983e84ee44fdc6e8971`, so each is a real `TRUE_CHILD` of that historical fork-time parent. They remain siblings of one another because none consumes another leaf.

```text
#455 fork-time parent 847e56c3418fce920c42d983e84ee44fdc6e8971
│
├─ #464 / PR #469  Codex live acceptance carrier       TRUE_CHILD / SIBLING
│  d239d17d1d718f3e5e8c1975307665cae43d3b09
├─ #465 / PR #470  GitHub DAG reversible live canary   TRUE_CHILD / SIBLING
│  f4c3215b6c52c2e6106070eaa1121dee1dbd48e3
├─ #466 / PR #471  Herdr lifecycle carrier             TRUE_CHILD / SIBLING
│  9eb70b2b62193b62a28f243de91e51337f1906b3
└─ #467 / PR #472  immutable source-claim compiler     TRUE_CHILD / SIBLING
   44d779a02e1749aa88a502d946646c22af38a026
       │
       └──── exact selected bytes ────┐
                                      ▼
#468 / PR #480 static convergence    HUMAN_ADMITTED / MERGED
                                      │
                                      └─ #465 hosted execution plane
                                         #490 / #494 / #496
                                         │
                                         └─ event-only PR #492
                                            run 32296935756
                                            LIVE_GITHUB_DEPENDENCY_CANARY_PASS
```

Fork-time multi-parent integration remains immutable evidence:

```text
commit 691b342c44c9c6c4e61a9997e778ae4ed6e920d5
tree   ba6ef27631546af466284f44af7c81cd347765dd
parents:
  847e56c3418fce920c42d983e84ee44fdc6e8971
  d239d17d1d718f3e5e8c1975307665cae43d3b09
  f4c3215b6c52c2e6106070eaa1121dee1dbd48e3
  9eb70b2b62193b62a28f243de91e51337f1906b3
  44d779a02e1749aa88a502d946646c22af38a026
```

That ancestry proves byte consumption only. #455 was later Human-admitted and merged, #473 was later rejected by commit-role provenance, and #480 was rebuilt/revalidated against current main before admission. `WAVE3_PARENT_ADMISSION.md` and `WAVE3_ADMISSION.md` own those authority transitions.

## Directory → responsibility map

```text
skills/agentic-tech-lead-orchestration/
├── scripts/
│   ├── run_codex_sdk_worker.py                existing #375 executor
│   ├── compile_codex_live_acceptance.py       #464 live-result + controller readback binder
│   ├── github_issue_dag_projection.py         existing #376 semantic projection
│   ├── github_issue_dag_live_canary.py        #465 one-edge reversible remote canary
│   ├── herdr_runtime_observer.py              existing #377 observation reducer
│   ├── collect_herdr_lifecycle.py             #466 bounded multi-sample lifecycle binder
│   ├── compile_source_claims.py               #467 immutable source → closure-ledger compiler
│   └── check_problem_closure.py               existing #378 closure authority
├── references/contracts/
│   ├── codex-live-acceptance-receipt.schema.json
│   ├── github-dag-live-canary-receipt.schema.json
│   ├── herdr-lifecycle-receipt.schema.json
│   └── source-claims-input.schema.json
├── references/examples/source-claims.example.json
├── references/wave3-live-handoff-queue.json   historical/local-runtime continuation packet
└── tests/
    ├── codex_live_acceptance_selftest.py
    ├── github_issue_dag_live_canary_selftest.py
    ├── herdr_lifecycle_selftest.py
    ├── source_claim_compiler_selftest.py
    └── run-all.sh                              shared deterministic denominator owner

.github/canaries/
└── wave3-github-dependency-live-plan.json      repo-owned fixed #486/#487 fixture binding

.github/workflows/
├── wave3-github-dependency-live-canary.yml     permission-bounded hosted execution plane
└── wave3-github-dependency-live-canary-governance.yml
                                                read-only static/commit-role gate
```

## End-to-end State Machine

```text
STATIC_CONTROL_PLANE_ADMITTED                 #455/#379
→ LIVE_EVIDENCE_PLAN_BOUND
→ EXACT_FORK_SUBJECT_BOUND
→ LIVE_CARRIER_SELECTED
    ├─ CODEX_RUNTIME_RESULT                  #464
    │   → LEASE_READBACK_PASS
    │   → CONTROLLER_SOURCE_DIFF_TEST_READBACK
    │   → LIVE_RUNTIME_AND_CONTROLLER_READBACK_CANDIDATE
    ├─ GITHUB_CANARY_PREFLIGHT               #465
    │   → OWNED_EDGE_ADDED
    │   → EXACT_REMOTE_READBACK
    │   → OWNED_EDGE_REMOVED
    │   → ORIGINAL_DENOMINATOR_RESTORED
    │   → LIVE_GITHUB_DEPENDENCY_CANARY_PASS   ACHIEVED: run 32296935756
    ├─ HERDR_LIFECYCLE                       #466
    │   → IDENTITY_STABLE
    │   → FRESHNESS_LIVENESS_STABLE
    │   → CLEAN_TERMINAL_OR_FALLBACK
    │   → LIVE_HERDR_LIFECYCLE_OBSERVED_CANDIDATE | UNAVAILABLE_FALLBACK
    └─ SOURCE_CLAIMS                         #467
        → IMMUTABLE_SOURCE_IDENTITY
        → CLAIM_DIGESTS
        → COMPLETE_SOURCE_MANIFEST_DIGEST
        → EXISTING_PROBLEM_CLOSURE_LEDGER
        → OPEN | IMPLEMENTED_UNVERIFIED | NOT_APPLICABLE | PARTIAL | HUMAN_ADMIT_REQUIRED
→ INDEPENDENT_SHADOW_READBACK
→ CURRENT_MAIN_CONSUMED
→ EXACT_HEAD_HOSTED_GATES
→ LOCAL_HANDOFF_FOR_UNEXECUTED_LIVE_LANES
→ READY_FOR_HUMAN_ADMIT | HOLD | REJECT
```

No branch, PR, terminal state, model prose, issue state, article/PDF prose, workflow green result, or generated Markdown may skip a transition.

## Deterministic denominator

```text
Wave 2 retained:
  Codex SDK adapter          4 positive / 14 mutations
  GitHub DAG projection      6 positive / 17 mutations
  Herdr observer             4 positive / 18 mutations
  problem closure            6 positive / 22 mutations

Wave 3 current:
  Codex live acceptance      1 positive / 12 mutations
  GitHub DAG live canary     1 positive / 10 mutations
  Herdr lifecycle            2 positive / 7 mutations
  source claim compiler      4 source kinds / 11 mutations

GitHub hosted-canary governance:
  fixed repository plan + exact trigger/permission/base-checkout contract
  read-only governance workflow + commit-role enforcement
  versioned Issue Dependencies REST transport

Shared shape gate:
  10 Draft-2020-12 control-plane schemas
  source-claims input example → compiler → existing problem-closure checker
  Wave-3 Local Handoff Queue assertion
```

These controls are deterministic/offline unless an exact runtime receipt says otherwise. The GitHub dependency lane has the additional remote receipt below; that does not promote the other lanes.

## Live carrier authority boundaries

### Codex

`compile_codex_live_acceptance.py` accepts only an `EXERCISED` worker result whose exact task/attempt/repo/base/tree, changed-file denominator, lease readback, and controller-owned source/diff/test verification all agree. The output remains `LIVE_RUNTIME_AND_CONTROLLER_READBACK_CANDIDATE` with `shadow_review_required=true`.

Raw model prose, prompts, reasoning, auth state, API keys, tokens, credentials, and ChatGPT subscription/session material are forbidden durable fields.

### GitHub Issue Dependencies

The canary owns only one explicitly labeled fixture edge. Both issues must be OPEN, both must carry the canary ownership label, and repository identity/visibility/default branch plus the entire original `blockedBy` denominator must match before mutation. After adding the owned edge, exact readback is mandatory. Cleanup removes only the owned edge and must restore the original denominator. Unexpected drift or cleanup failure is terminal.

The admitted remote carrier uses the dedicated versioned GitHub Issue Dependencies REST surface for complete denominator read/add/remove, while the repository-owned hosted workflow provides the narrowly scoped `issues: write` execution authority. The event PR head is never executed; the workflow checks out the exact base/main subject and re-reads current main before mutation.

Current bounded remote receipt:

```text
issue                         #465
fixture blocker               #486
fixture blocked target        #487
exact executor base/main      81041d1b88283fabdc1c4db05efaf8dd945e24df
event-only PR                 #492  CLOSED_UNMERGED
workflow run                  32296935756
receipt sha256                da227e94215a1b28a9e550546242c8a482bd718f7b35d67f159ccaa95f23efe5
before.blockedBy              []
applied.blockedBy             [486]
cleanup.blockedBy             []
execution                     EXERCISED
canary_state                  LIVE_GITHUB_DEPENDENCY_CANARY_PASS
semantic_authority            false
evidence_ceiling              REMOTE_CANARY_EDGE_ONLY
```

Attempt `32295401831` is retained as fail-closed pre-mutation evidence for the earlier CLI response-shape mismatch. It is not a PASS and no edge had been added when it failed.

The successful canary proves only the reversible remote fixture edge and cleanup/readback contract. It never becomes semantic DAG authority and does not prove release or production readiness.

### Herdr

The lifecycle carrier reuses the existing observer. Across bounded samples, task/attempt/repository/Git/worktree/target and pane/workspace/PID-start/native-session identity must stay fixed; timestamps cannot regress; nonterminal states require a live process; terminal state requires clean cleanup and zero residue; no sample may appear after terminal state.

`DONE_CANDIDATE` remains advisory. `UNAVAILABLE_FALLBACK` remains non-success.

### Issue / article / PDF / PRD source compiler

GitHub issues use exact `owner/repo#number` identity. Article/PDF/PRD inputs require caller-supplied immutable `sha256:<64hex>` identity plus exact locator. Claim bytes are hashed individually; the complete source manifest is content-bound. Output is the existing `problem-closure` schema, with no invented verification/receipt/merge evidence.

Compiler PASS proves binding and shape only, not source truth or closure.

## Local Handoff Execution Queue

`skills/agentic-tech-lead-orchestration/references/wave3-live-handoff-queue.json` is the immutable fork-time/local-runtime continuation packet and retains its historical predecessor ordering. It is not current mutable evidence authority. The #465 GitHub lane was later satisfied independently through the admitted hosted GitHub execution plane above, so its successful receipt is read from current GitHub/runtime evidence rather than inferred from queue position.

The remaining local/runtime handoff obligations are still #464 signed-in Codex/controller acceptance and #466 real Herdr lifecycle. #467 source/provider truth remains evidence-dependent. Queue presence, historical predecessor state, static validation, or another lane's PASS cannot promote them.

Queue advance, provider activation, merge, force push, semantic conflict resolution, release, permission change, and rollback remain outside unattended Worker authority.

## Current publication rule

Static/deterministic Wave‑3 infrastructure was Human-admitted through #480 and post-merge reconciliation. The #465 remote receipt is a later runtime/evidence subject; it does not reopen or rewrite #468/#480 ancestry. Any future mechanism change must still bind current `main`, preserve the admitted denominator, pass exact-head governance, and receive its own Shadow/Human admission before it can affect main.

## Evidence ceiling

```text
Wave-3 public carrier code                    ADMITTED_ON_MAIN
Wave-3 deterministic controls                 PASS_ON_ADMITTED_CURRENT_IMPLEMENTATION
live Codex SDK execution                      NOT_EXERCISED
live controller acceptance                    NOT_EXERCISED
live GitHub dependency canary                 LIVE_GITHUB_DEPENDENCY_CANARY_PASS
                                               REMOTE_CANARY_EDGE_ONLY
live Herdr lifecycle                          NOT_EXERCISED
real article/PDF/PRD truth                    SOURCE_PROPOSAL / EVIDENCE_DEPENDENT
real article/PDF/provider closure              EVIDENCE_DEPENDENT
static infrastructure Human Admit             COMPLETED
release / promotion / production safety       NOT_PERFORMED
```

The GitHub live receipt is bounded to one owned reversible fixture edge. It cannot promote Codex, Herdr, source/provider, semantic DAG, release, promotion, or production claims.
