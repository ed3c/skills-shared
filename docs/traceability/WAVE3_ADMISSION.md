# Wave 3 live-evidence infrastructure — admission record

Status: `STATIC_DETERMINISTIC_INFRASTRUCTURE_ADMITTED / GITHUB_REMOTE_CANARY_EXERCISED`.

This record closes the public/static Wave‑3 infrastructure phase for issues #464–#468 and records the later bounded live GitHub Issue Dependencies receipt for #465. It records exact Human-admitted Git subjects, post-merge reconciliation, and one real reversible remote fixture-edge execution. It does **not** claim that live Codex, Herdr, source/provider, release, promotion, or production effects occurred.

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
  GitHub DAG projection      7 positive / 23 mutations (#497 live_readback producer controls)
  Herdr observer             4 positive / 18 mutations
  problem closure            6 positive / 22 mutations

Wave 3 current implementation
  Codex live acceptance      1 positive / 12 mutations
  GitHub DAG live canary     1 positive / 10 mutations
  Herdr lifecycle            2 positive / 7 mutations
  source claim compiler      4 source kinds / 11 mutations

GitHub hosted-canary governance
  fixed #486/#487 repository plan
  exact same-repo branch/title Ready trigger
  base/main checkout + current-main freshness guard
  read-only static governance workflow
  repository commit-role gate
  versioned Issue Dependencies REST transport

Shared shape/integration
  10 Draft-2020-12 control-plane schemas
  source claims → existing problem-closure checker
  Wave‑3 Local Handoff Queue assertion
```

The extra GitHub live-canary controls were admitted after the original static Wave‑3 merge through the #465 hosted execution/repair line. They strengthen the same bounded mechanism and do not widen authority.

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
→ #465 HOSTED_EXECUTOR_ADMITTED
→ WORKFLOW_REGISTRATION_REPAIRED
→ VERSIONED_DEPENDENCY_REST_CARRIER_ADMITTED
→ REMOTE_FIXTURE_EDGE_ADDED
→ EXACT_REMOTE_READBACK
→ OWNED_EDGE_REMOVED
→ ORIGINAL_DENOMINATOR_RESTORED
→ LIVE_GITHUB_DEPENDENCY_CANARY_PASS
```

The post-admission live transitions above apply only to #465. They do not advance #464, #466, or #467.

## Post-admission live evidence — #465

A dedicated public hosted execution plane was admitted after the static Wave‑3 merge. It binds fixture issues #486/#487 and grants only the `issues: write` authority required for the reversible canary; trigger-head code is never executed.

The first remote attempt, run `32295401831`, failed closed during the initial dependency-denominator read before any add operation. That failure exposed a live CLI projection-shape mismatch and is retained as negative evidence.

The carrier was then repaired to use GitHub's dedicated versioned Issue Dependencies REST surface, with complete paginated denominator reads, same-repository row validation, dedicated POST/DELETE mutation, and mandatory cleanup. The repaired carrier was Human-admitted on current main before retry.

The successful remote receipt is:

```text
issue                         #465
fixture blocker               #486
fixture blocked target        #487
executor base/main             81041d1b88283fabdc1c4db05efaf8dd945e24df
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

All mutation, receipt-validation, and evidence-publication workflow steps succeeded. The event PR was then closed unmerged by design. The two fixture issues remained OPEN with their ownership label after cleanup, independently confirming their state did not move during the canary; they were retired/closed only after #465 closure.

This establishes one real reversible GitHub Issue Dependencies fixture edge and cleanup/readback contract. It does not establish semantic task-DAG truth, arbitrary issue-mutation safety, Codex/Herdr execution, source/provider closure, release, promotion, or production safety.

## Successor ownership reconciliation — #485

Wave‑3 is the sole mutable owner of the live/evidence lanes that extend the admitted Wave‑2 mechanisms. `CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md` retains immutable Wave‑2 Git history and deterministic denominators, but it no longer owns future live receipts except for the separately retained #376 residual below.

```text
Wave-2 mechanism lineage                     Wave-3 live/evidence successor
#375 Codex SDK adapter                       #464 live Codex SDK/controller acceptance
#376 GitHub Issue Dependencies projection    #465 reversible GitHub dependency canary
#377 Herdr observer                          #466 live Herdr lifecycle
#378 problem-closure mechanism               #467 article/PDF/PRD + source/provider evidence
```

This transfer does not promote evidence. The current successor states remain exactly those shown below. #375, #377, and #378 may close as completed static mechanism parents after #485 admission; #376 must remain open because generic development-link ownership was not transferred and remains a distinct residual.

```text
#376 generic development-link ownership      RESIDUAL / still owned by #376
```

A Wave‑3 successor receipt appends new evidence only in its successor lane. It never retroactively rewrites the Wave‑2 static admission or turns a different residual into PASS.

## Remaining evidence owners

```text
#464 live Codex SDK/controller acceptance       NOT_EXERCISED
#465 live GitHub add/readback/remove canary      LIVE_GITHUB_DEPENDENCY_CANARY_PASS
                                                  REMOTE_CANARY_EDGE_ONLY
#466 live Herdr lifecycle                        NOT_EXERCISED
#467 article/PDF/PRD truth                       SOURCE_PROPOSAL / EVIDENCE_DEPENDENT
#467 real source/provider closure                EVIDENCE_DEPENDENT
#376 generic development-link residual           RESIDUAL
release / production promotion                   NOT_PERFORMED
```

`wave3-live-handoff-queue.json` remains the immutable fork-time/local-runtime continuation packet. Its historical predecessor ordering is not mutable evidence authority: #465 was later satisfied through the independently admitted hosted GitHub lane. The queue remains useful for the unresolved #464/#466 local runtime obligations; queue presence or another lane's PASS cannot promote them.

## Agent read order after admission

For #375–#379 lineage or #464–#468 live work after this admission:

1. read this record for the immutable admitted Wave‑3 subject, bounded #465 remote receipt, and current successor ownership;
2. read `CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md` for immutable Wave‑2 admission facts and the same successor map;
3. re-read current `main`, issue/PR state, workflows, and runtime receipts from GitHub/runtime authority;
4. use `WAVE3_PARENT_ADMISSION.md` for fork/current-main transition history;
5. use `WAVE3_LIVE_EVIDENCE.md` for carrier contracts, State Machine, deterministic denominator, #465 receipt, and Local Handoff semantics;
6. load the selected Agentic Tech Lead modules/scripts/contracts only when their trigger matches;
7. keep #376's generic development-link residual separate from #465's bounded Issue Dependencies canary.

If prose conflicts with current GitHub metadata, exact Git subjects, executable contracts, or runtime receipts, the machine/external subjects win.

Driven-By: human
Driven-On: chatgpt-github-connector
