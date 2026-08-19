# Wave 3 live-evidence control plane — Tech Lead + Shadow trace

Status: `STATIC_LIVE_EVIDENCE_INFRASTRUCTURE_REVALIDATING_CURRENT_MAIN`.

This document records the public-repository mechanism that prepares live Codex SDK, GitHub Issue Dependencies, Herdr lifecycle, and source-claim evidence without pretending those external/runtime effects occurred. Machine authority remains exact Git ancestry, contracts/checkers, current GitHub metadata, exact-head hosted workflows, runtime receipts, source readback, and Human repository policy.

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
#468 current publication candidate   CONVERGENCE
                                      ↑
                          current main freshness input
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

That ancestry proves byte consumption only. #455 was later Human-admitted and merged, #473 was later rejected by commit-role provenance, and #480 predecessor evidence became stale when current main advanced through #477. `WAVE3_PARENT_ADMISSION.md` owns those authority transitions.

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
├── references/wave3-live-handoff-queue.json
└── tests/
    ├── codex_live_acceptance_selftest.py
    ├── github_issue_dag_live_canary_selftest.py
    ├── herdr_lifecycle_selftest.py
    ├── source_claim_compiler_selftest.py
    └── run-all.sh                              #468 shared denominator owner
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
    │   → LIVE_GITHUB_DEPENDENCY_CANARY_PASS
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
→ CURRENT_MAIN_CONSUMED                      #468 freshness
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

Wave 3 added:
  Codex live acceptance      1 positive / 12 mutations
  GitHub DAG live canary     1 positive / 6 mutations
  Herdr lifecycle            2 positive / 7 mutations
  source claim compiler      4 source kinds / 11 mutations

Shared shape gate:
  10 Draft-2020-12 control-plane schemas
  source-claims input example → compiler → existing problem-closure checker
  Wave-3 Local Handoff Queue assertion
```

These are deterministic/offline controls unless an exact runtime receipt says otherwise.

## Live carrier authority boundaries

### Codex

`compile_codex_live_acceptance.py` accepts only an `EXERCISED` worker result whose exact task/attempt/repo/base/tree, changed-file denominator, lease readback, and controller-owned source/diff/test verification all agree. The output remains `LIVE_RUNTIME_AND_CONTROLLER_READBACK_CANDIDATE` with `shadow_review_required=true`.

Raw model prose, prompts, reasoning, auth state, API keys, tokens, credentials, and ChatGPT subscription/session material are forbidden durable fields.

### GitHub Issue Dependencies

The canary owns only one explicitly labeled fixture edge. Both issues must be OPEN, both must carry the canary ownership label, and repository identity/visibility/default branch plus the entire original `blockedBy` denominator must match before mutation. After adding the owned edge, exact readback is mandatory. Cleanup removes only the owned edge and must restore the original denominator. Unexpected drift or cleanup failure is terminal.

The canary never becomes semantic DAG authority.

### Herdr

The lifecycle carrier reuses the existing observer. Across bounded samples, task/attempt/repository/Git/worktree/target and pane/workspace/PID-start/native-session identity must stay fixed; timestamps cannot regress; nonterminal states require a live process; terminal state requires clean cleanup and zero residue; no sample may appear after terminal state.

`DONE_CANDIDATE` remains advisory. `UNAVAILABLE_FALLBACK` remains non-success.

### Issue / article / PDF / PRD source compiler

GitHub issues use exact `owner/repo#number` identity. Article/PDF/PRD inputs require caller-supplied immutable `sha256:<64hex>` identity plus exact locator. Claim bytes are hashed individually; the complete source manifest is content-bound. Output is the existing `problem-closure` schema, with no invented verification/receipt/merge evidence.

Compiler PASS proves binding and shape only, not source truth or closure.

## Local Handoff Execution Queue

`skills/agentic-tech-lead-orchestration/references/wave3-live-handoff-queue.json` remains a bounded continuation packet for actual live Codex, Herdr and reversible GitHub canary execution. Its historical immutable input is reproducible, but a live receipt intended to establish current repository closure must be rebound/read against the exact runtime subject used for that execution and independently reviewed.

Queue advance, provider activation, issue close, merge, force push, semantic conflict resolution, release, permission change, and rollback remain outside unattended Worker authority.

## Current publication rule

The current #468 publication subject must be built from the current admitted `main` plus the selected #469–#472 bytes. If current main moves, the head is stale even when its own workflow runs are green. A new current-main convergence epoch and fresh exact-head hosted denominator are mandatory before Human Admit.

## Evidence ceiling

```text
Wave-3 public carrier code                    IMPLEMENTED_CANDIDATE
Wave-3 deterministic controls                 MUST_PASS_ON_EXACT_CURRENT_HEAD
live Codex SDK execution                      NOT_EXERCISED unless runtime receipt exists
live controller acceptance                    NOT_EXERCISED unless matching receipt + Shadow exists
live GitHub dependency canary                 NOT_EXERCISED unless remote add/readback/remove receipt exists
live Herdr lifecycle                          NOT_EXERCISED unless real process receipt exists
real article/PDF/PRD truth                    SOURCE_PROPOSAL / EVIDENCE_DEPENDENT
real article/PDF/provider closure              EVIDENCE_DEPENDENT
Human Admit                                    HUMAN_ADMIT_REQUIRED
merge/release/production safety                NOT_PERFORMED
```

A green hosted result may prove static/deterministic Wave‑3 infrastructure convergence only. It cannot promote any live lane.
