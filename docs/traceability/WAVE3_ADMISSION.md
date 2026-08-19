# Wave 3 live-evidence infrastructure — admission record

Status: `STATIC_DETERMINISTIC_LIVE_EVIDENCE_INFRASTRUCTURE_ADMITTED_ON_MAIN`.

This record closes the public/static Wave‑3 infrastructure phase for issues #464–#468. It records the exact Human-admitted Git subjects and the post-merge reconciliation boundary. It does **not** claim that live Codex, GitHub dependency, Herdr, source/provider, release, promotion, or production effects occurred.

## Admitted subjects

```text
repository                    ed3c/skills-shared
convergence issue             #468
admitted PR                   #480
checked candidate head        8a33b9b3994a39e4ebb220a06fe17e33812661f0
checked candidate tree        b2347bf0af8e0bb768abcf2fe847e8844caed228
merge commit                  dd86861972f41f6d36c3de7ac156358ed5fae9d5
merge tree                    b05ead21c60cfc459dac5f823bd3ce1ca17ff318
actual first merge parent     36932ca9f8266f17cfd15ee20fb2621f6ef0e437
checked-head base observation 2bf90d7182d42dfc3a908ffa68d7ea4b26898042
```

The GitHub merge commit is verified and has two parents: the then-current `main` subject `36932ca9...` and the exact checked Wave‑3 candidate `8a33b9b...`.

## Merge-race reconciliation

The final Shadow read immediately before merge observed `main@2bf90d71...`. Another independently admitted post-merge UCR trace, PR #482, advanced `main` to `36932ca9...` before GitHub created the merge commit. The merge API therefore combined the exact checked #480 head with that newer current main.

This race was not hidden or treated as automatically safe. Post-merge comparison proves:

```text
36932ca9... → dd868619...
  exact changed-file denominator = the same 28 Wave‑3 paths

8a33b9b... → dd868619...
  additional paths only:
    skills/universal-refactor-controller/README.md
    skills/universal-refactor-controller/references/ucr-program-trace.json
```

Therefore the actual merge preserves the independently admitted #482 UCR trace while adding the reviewed Wave‑3 28-path delta. Candidate-tree inequality is explained by those two concurrent UCR trace files; it is not evidence that the Wave‑3 implementation was silently rewritten.

## Exact-head hosted evidence before Human Admit

All four required Ready-event workflows completed successfully on checked head `8a33b9b3994a39e4ebb220a06fe17e33812661f0`:

```text
Skill Suites                  run 32286000465  SUCCESS
Shared Skills Infra           run 32286000451  SUCCESS
Skill Eval Contract           run 32286000416  SUCCESS
Git Town Stacked PR Worker    run 32286000382  SUCCESS
```

`Skill Eval Contract` passed document routing, commit-role provenance, migration, intent-promotion, verifier calibration, mutation lineage, capability unlock, verified release, scorecard, shell assertions, eval suites, script compilation, JSON contracts, and safe-block checks.

## Deterministic denominator

```text
Wave 2 retained
  Codex SDK adapter          4 positive / 14 mutations
  GitHub DAG projection      6 positive / 17 mutations
  Herdr observer             4 positive / 18 mutations
  problem closure            6 positive / 22 mutations

Wave 3 admitted infrastructure
  Codex live acceptance      1 positive / 12 mutations
  GitHub DAG live canary     1 positive / 6 mutations
  Herdr lifecycle            2 positive / 7 mutations
  source claim compiler      4 source kinds / 11 mutations

Shared shape/integration
  10 Draft-2020-12 control-plane schemas
  source claims → existing problem-closure checker
  Wave‑3 Local Handoff Queue assertion
```

## Publication lineage

The selected leaf bytes were consumed into #480 and are now present on `main` through the convergence merge:

```text
#464 / PR #469  d239d17d1d718f3e5e8c1975307665cae43d3b09
#465 / PR #470  f4c3215b6c52c2e6106070eaa1121dee1dbd48e3
#466 / PR #471  9eb70b2b62193b62a28f243de91e51337f1906b3
#467 / PR #472  44d779a02e1749aa88a502d946646c22af38a026
```

Their final publication state observed before admission was closed-unmerged; this is lineage, not a requirement to merge those PRs independently. Current mutable PR state must always be re-read from GitHub.

Rejected/stale convergence history remains part of the denominator:

```text
PR #473 / 87d00514...  REJECTED_BY_COMMIT_ROLE
  historical noop commit 3fe0a79... lacked required provenance trailers

PR #480 predecessor / 1eae9b47...  HISTORICAL_AFTER_MAIN_DRIFT
  provenance-complete, but main advanced through admitted UCR work before final admission
```

No force rewrite erased either subject.

## Admission State Machine

```text
WAVE3_CARRIERS_IMPLEMENTED
→ SELECTED_LEAF_BYTES_CONVERGED
→ CURRENT_MAIN_RECONCILED
→ EXACT_HEAD_HOSTED_GATES_PASS
→ SHADOW_FRESHNESS_AND_DENOMINATOR_PASS
→ HUMAN_ADMIT
→ MERGED_ON_MAIN
→ POST_MERGE_RACE_RECONCILED
→ STATIC_DETERMINISTIC_WAVE3_PHASE_CLOSED
```

## Remaining evidence owners

```text
#464 live Codex SDK/controller acceptance       NOT_EXERCISED
#465 live GitHub add/readback/remove canary      NOT_EXERCISED
#466 live Herdr lifecycle                        NOT_EXERCISED
#467 article/PDF/PRD truth                       SOURCE_PROPOSAL / EVIDENCE_DEPENDENT
#467 real source/provider closure                EVIDENCE_DEPENDENT
release / production promotion                   NOT_PERFORMED
```

The committed Wave‑3 Local Handoff Queue remains a continuation contract for those live lanes. Queue presence, static validation, PR merge, or this admission record cannot promote a live receipt.

## Agent read order after admission

For #464–#468 work after this admission:

1. read this record for the immutable admitted static/deterministic subject;
2. re-read current `main`, issue/PR state, workflows, and runtime receipts from GitHub/runtime authority;
3. use `WAVE3_PARENT_ADMISSION.md` for fork/current-main transition history;
4. use `WAVE3_LIVE_EVIDENCE.md` for carrier contracts, State Machine, deterministic denominator, and Local Handoff semantics;
5. load the selected Agentic Tech Lead modules/scripts/contracts only when their trigger matches;
6. keep live #464–#467 evidence in the owning runtime/evidence lane.

If prose conflicts with current GitHub metadata, exact Git subjects, executable contracts, or runtime receipts, the machine/external subjects win.

Driven-By: human
Driven-On: chatgpt-github-connector
