# Wave 3 live-evidence control plane — Tech Lead + Shadow trace

Status: `STATIC_LIVE_EVIDENCE_INFRASTRUCTURE_REVALIDATING_REPLACEMENT`.

This document records the public-repository mechanism that prepares live Codex SDK, GitHub Issue Dependencies, Herdr lifecycle, and source-claim evidence without pretending those external/runtime effects occurred. Machine authority remains exact Git ancestry, contracts/checkers, current GitHub metadata, exact-head hosted workflows, runtime receipts, source readback, and Human repository policy.

Read `WAVE3_PARENT_ADMISSION.md` first for current parent/replacement authority. This file preserves fork-time architecture and current Wave-3 mechanism details.

## Parent and molecular DAG

Wave 3 was forked while #455 was still unmerged, so each implementation leaf is a real historical `TRUE_CHILD` of #455 exact head `847e56c3418fce920c42d983e84ee44fdc6e8971`. The four leaves never consume each other and remain siblings. #455 was subsequently Human-admitted; that later admission does not rewrite the fork-time dependency.

```text
#455 / #379  fork-time TRUE_PARENT; now HUMAN_ADMITTED / MERGED
head consumed by leaves: 847e56c3418fce920c42d983e84ee44fdc6e8971
│
├─ #464 / PR #469  Codex live acceptance carrier       TRUE_CHILD / SIBLING
│  head d239d17d1d718f3e5e8c1975307665cae43d3b09
├─ #465 / PR #470  GitHub DAG reversible live canary   TRUE_CHILD / SIBLING
│  head f4c3215b6c52c2e6106070eaa1121dee1dbd48e3
├─ #466 / PR #471  Herdr lifecycle carrier             TRUE_CHILD / SIBLING
│  head 9eb70b2b62193b62a28f243de91e51337f1906b3
└─ #467 / PR #472  immutable source-claim compiler     TRUE_CHILD / SIBLING
   head 44d779a02e1749aa88a502d946646c22af38a026
        │
        └──── exact selected bytes ────┐
                                       ▼
#468 / PR #473  HISTORICAL / REJECTED_COMMIT_ROLE
#468 / PR #479  CURRENT REPLACEMENT CONVERGENCE
```

Original immutable byte-integration checkpoint retained as provenance:

```text
commit 691b342c44c9c6c4e61a9997e778ae4ed6e920d5
tree   ba6ef27631546af466284f44af7c81cd347765dd
parents:
  847e56c3418fce920c42d983e84ee44fdc6e8971  #455 fork-time parent contract
  d239d17d1d718f3e5e8c1975307665cae43d3b09  #469
  f4c3215b6c52c2e6106070eaa1121dee1dbd48e3  #470
  9eb70b2b62193b62a28f243de91e51337f1906b3  #471
  44d779a02e1749aa88a502d946646c22af38a026  #472
```

PR #473 later produced a functionally green Wave-3 semantic tree after queue repair, but its `Skill Eval Contract` correctly rejected accidental historical noop commit `3fe0a79aaeed78b8e529773b241eff07d1c2a4d4` for missing commit-role trailers. PR #479 rebuilds the same Wave-3 mechanism without that ancestry and reconciles current PR #475 post-merge admission routes.

This ancestry proves byte consumption only. It does not prove a live effect, Human Admit for Wave 3, merge, release, or production safety.

## Directory → responsibility map

```text
skills/agentic-tech-lead-orchestration/
├── scripts/
│   ├── run_codex_sdk_worker.py                existing admitted #375 executor
│   ├── compile_codex_live_acceptance.py       #464 live-result + controller readback binder
│   ├── github_issue_dag_projection.py         existing admitted #376 semantic projection
│   ├── github_issue_dag_live_canary.py        #465 one-edge reversible remote canary
│   ├── herdr_runtime_observer.py              existing admitted #377 single observation reducer
│   ├── collect_herdr_lifecycle.py             #466 bounded multi-sample lifecycle binder
│   ├── compile_source_claims.py               #467 immutable source → closure-ledger compiler
│   └── check_problem_closure.py               existing admitted #378 closure authority
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
ADMITTED_STATIC_CONTROL_PLANE                #455 on main
→ LIVE_EVIDENCE_PLAN_BOUND
→ EXACT_PARENT_SUBJECT_BOUND
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
→ EXACT_HEAD_HOSTED_GATES                    #468 / #479
→ LOCAL_HANDOFF_FOR_UNEXECUTED_LIVE_LANES
→ READY_FOR_RUNTIME_HANDOFF | HOLD | REJECT
→ later HUMAN_ADMIT only when separately authorized
```

No branch, PR, terminal state, model prose, issue state, article/PDF prose, workflow green result, or generated Markdown may skip a transition.

## Deterministic denominator

```text
Wave 2 retained and admitted:
  Codex SDK adapter          4 positive / 14 mutations
  GitHub DAG projection      6 positive / 17 mutations
  Herdr observer             4 positive / 18 mutations
  problem closure            6 positive / 22 mutations

Wave 3 added:
  Codex live acceptance      1 positive / 12 mutations
  GitHub DAG live canary     1 positive / 6 mutations
  Herdr lifecycle            2 positive / 7 mutations
  source claim compiler      4 source kinds / 11 mutations

Shared shape/integration gate:
  10 Draft-2020-12 control-plane schemas
  source-claims input example → compiler → existing problem-closure checker
  Wave-3 Local Handoff Queue semantic assertion
```

These are deterministic/offline controls unless an exact runtime receipt says otherwise.

## Live carrier authority boundaries

### Codex

`compile_codex_live_acceptance.py` accepts only an `EXERCISED` worker result whose exact task/attempt/repo/base/tree, changed-file denominator, lease readback, and controller-owned source/diff/test verification all agree. The output is still `LIVE_RUNTIME_AND_CONTROLLER_READBACK_CANDIDATE` with `shadow_review_required=true`.

Raw model prose, prompts, reasoning, auth state, API keys, tokens, credentials, and ChatGPT subscription/session material are forbidden durable fields.

### GitHub Issue Dependencies

The canary owns only one explicitly labeled fixture edge. Both issues must be OPEN, both must carry the canary ownership label, and repository identity/visibility/default branch plus the entire original `blockedBy` denominator must match before mutation. After adding the owned edge, exact readback is mandatory. Cleanup removes only the owned edge and must restore the original denominator. Unexpected drift or cleanup failure is terminal.

The canary never becomes semantic DAG authority.

### Herdr

The lifecycle carrier reuses the existing observer. Across bounded samples, task/attempt/repository/Git/worktree/target and pane/workspace/PID-start/native-session identity must stay fixed; timestamps cannot regress; nonterminal states require a live process; terminal state requires clean cleanup and zero residue; no sample may appear after terminal state.

`DONE_CANDIDATE` remains advisory. `UNAVAILABLE_FALLBACK` remains non-success.

### Issue / article / PDF / PRD source compiler

GitHub issues use exact `owner/repo#number` identity. Article/PDF/PRD inputs require caller-supplied immutable `sha256:<64hex>` identity plus exact locator. Claim bytes are hashed individually; the complete source manifest is also content-bound. Output is the existing `problem-closure` schema, with no invented verification/receipt/merge evidence.

Compiler PASS proves binding and shape only, not source truth or closure.

## Local Handoff Execution Queue

`skills/agentic-tech-lead-orchestration/references/wave3-live-handoff-queue.json` binds local/runtime continuation to immutable fork-time integration commit `691b342c...` and tree `ba6ef276...`.

```text
ACTIVE  codex-live-receipt
  → herdr-live-lifecycle
  → github-dag-live-canary
  → queue terminal
```

Each item has concrete bounded commands plus a canonical `CONCRETE_COMMAND_CONTRACT` unresolved materialization operation for runtime-specific manifest/target/fixture identities. Queue advance, provider activation, issue close, merge, force push, semantic conflict resolution, release, permission change, and rollback remain outside unattended Worker authority.

The queue is a continuation contract, not a claim that the three runtime actions have happened. A runtime execution must rebind freshness to the exact admitted/current subject before producing a receipt.

## Rejected and replacement convergence lineage

```text
#473 / 703fc4d00d913512d0886a710305238462a23fd8
  functional/static gates:
    Skill Suites              PASS
    Shared Skills Infra       PASS
    Git Town                  PASS
    document routing          PASS
  Skill Eval commit-role      FAIL on accidental 3fe0a79... noop ancestry

#479 replacement
  removes that accidental ancestry without gate exception
  preserves exact leaf heads #469–#472
  reconciles current main post-merge #475 admission docs
  current exact head must be read live from GitHub before any verdict
```

The rejected #473 lineage remains immutable evidence. PR #479 does not retroactively turn #473 green.

## Evidence ceiling

```text
Wave-3 public carrier code                    IMPLEMENTED_CANDIDATE
Wave-3 deterministic controls                 MUST_PASS_ON_EXACT_REPLACEMENT_HEAD
live Codex SDK execution                      NOT_EXERCISED unless runtime receipt exists
live controller acceptance                    NOT_EXERCISED unless matching receipt + Shadow exists
live GitHub dependency canary                 NOT_EXERCISED unless remote add/readback/remove receipt exists
live Herdr lifecycle                          NOT_EXERCISED unless real process receipt exists
real article/PDF/PRD truth                    SOURCE_PROPOSAL / EVIDENCE_DEPENDENT
real article/PDF/provider closure              EVIDENCE_DEPENDENT
Human Admit for #479                          NOT_PERFORMED
#479 merge/release/production safety          NOT_PERFORMED
```

PR #479 may prove static/deterministic Wave-3 live-evidence infrastructure convergence only. Its mutable head must be read from GitHub and must freshly pass all configured hosted gates after the final documentation/index edit.
