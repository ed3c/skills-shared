# Wave 3 replacement convergence — current authority

Status: `REPLACEMENT_CANDIDATE_PENDING_EXACT_HEAD_GATES`.

Read this file before treating any Wave-3 PR number or convergence state in older traceability, Git Town, or Shadow snapshots as current.

## Why a replacement exists

PR #473 established the Wave-3 semantic implementation and, after its queue-shape repair, passed the functional/static denominator including:

```text
10 control-plane Draft-2020-12 schemas
Wave-2 selftests: Codex 4/14, GitHub DAG 6/17, Herdr 4/18, problem closure 6/22
Wave-3 selftests: Codex live 1/12, GitHub canary 1/6, Herdr lifecycle 2/7, source compiler 4-source/11
source compiler → existing problem-closure checker integration
Wave-3 Local Handoff Queue semantic assertion
Skill Suites
Shared Skills Infra
Git Town Stacked PR Worker
document routing
```

Its final `Skill Eval Contract` correctly rejected one accidental historical noop commit:

```text
3fe0a79aaeed78b8e529773b241eff07d1c2a4d4
```

because it lacked repository-required `Driven-By` / `Driven-On` trailers. The file created by that commit had already been deleted and was absent from the final tree, but provenance is part of the denominator. The gate was not weakened and the commit was not added to an exception list.

Therefore:

```text
#473 = HISTORICAL / REJECTED_COMMIT_ROLE
#479 = CURRENT REPLACEMENT CONVERGENCE CANDIDATE
```

## Current parent authority

Wave-3 leaves were forked as true children of #455 exact head `847e56c3418fce920c42d983e84ee44fdc6e8971`. #455 was later Human-admitted and merged, then PR #475 admitted the post-merge #379 documentation record.

At the replacement reconciliation epoch, current main is:

```text
4be4d6744fe432e4be24d94750bb4fc034aab189
```

PR #479 semantically reconciles the current #475 routes instead of overwriting them. Immutable reconciliation checkpoint:

```text
e8cdd46c073df87ce80582ed91ae8f56d28eb001
parents:
  5897fdc5b43c732d1a325961fe6d685e1495408a  provenance-clean Wave-3 replacement
  4be4d6744fe432e4be24d94750bb4fc034aab189  admitted current main at reconciliation
```

The replacement preserves the four selected leaf subjects:

```text
#469 d239d17d1d718f3e5e8c1975307665cae43d3b09
#470 f4c3215b6c52c2e6106070eaa1121dee1dbd48e3
#471 9eb70b2b62193b62a28f243de91e51337f1906b3
#472 44d779a02e1749aa88a502d946646c22af38a026
```

## Snapshot precedence

Earlier `WAVE3_LIVE_EVIDENCE.md`, `TRACEABILITY_INDEX.md`, `procedural-shadow-runtime/README.md`, or `git-town-stacked-pr-worker/README.md` passages that name PR #473 as the current Wave-3 convergence are retained as historical snapshot/provenance until this replacement lands. For **current** decisions, this file and live GitHub metadata take precedence.

The Molecular relation itself has not changed:

```text
#455 fork-time TRUE_PARENT; now admitted historical parent
├─ #469 TRUE_CHILD / sibling
├─ #470 TRUE_CHILD / sibling
├─ #471 TRUE_CHILD / sibling
└─ #472 TRUE_CHILD / sibling
      ↓ exact selected bytes
#479 CURRENT CONVERGENCE
```

The leaves are not serial children of one another.

## Required final gate

The mutable #479 head must be read live and freshly pass all configured exact-head workflows after the final route update:

```text
Skill Suites
Shared Skills Infra
Skill Eval Contract
Git Town Stacked PR Worker
```

Shadow must also re-read current main, selected leaf heads, changed-file denominator, rejected #473 lineage, document routes and evidence ceilings before issuing a stage verdict.

## Evidence ceiling

```text
Wave-3 deterministic/live-evidence infrastructure   candidate only
live Codex SDK + controller acceptance              NOT_EXERCISED
live GitHub reversible dependency canary            NOT_EXERCISED
live Herdr lifecycle                                NOT_EXERCISED
article/PDF/PRD truth/provider verification         EVIDENCE_DEPENDENT
#479 Human Admit                                    NOT_PERFORMED
#479 merge/release/promotion                        NOT_PERFORMED
```

A successful #479 hosted gate may authorize only a static/deterministic runtime-handoff stage. It cannot fabricate live receipts or Human authority.
