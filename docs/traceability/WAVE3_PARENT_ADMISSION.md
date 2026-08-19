# Wave 3 parent admission transition

Status: `CURRENT_MAIN_REFRESH_REQUIRED_BEFORE_WAVE3_ADMIT`.

This document records the authority transition for the #464–#468 live-evidence program. It separates fork-time ancestry from current repository authority so a later Agent does not treat an old green convergence as current.

## Fork-time parent

At Wave‑3 fork time, #464–#467 were real `TRUE_CHILD` leaves of the then-unmerged #455 exact head:

```text
#455 fork head  847e56c3418fce920c42d983e84ee44fdc6e8971
#455 tree       8a75271851f2e9dd47dd3a019c93e4a0f9272d24
```

Every leaf consumed those exact bytes and none consumed another Wave‑3 leaf, so #464–#467 remain siblings of one another.

## Wave‑2 admission

#455 was subsequently Human-admitted and merged:

```text
merge commit  ca31e0b1e640f0dba2c3d94da9d9786fbed32f2c
parents:
  4ca9417b1da5ff32f1d4d3e7af64a15908749024
  847e56c3418fce920c42d983e84ee44fdc6e8971
tree:
  8a75271851f2e9dd47dd3a019c93e4a0f9272d24
```

The merge tree equals the reviewed #455 candidate tree byte-for-byte. The post-merge admission route was then published through provenance-complete PR #475; rejected PR #474 remains historical commit-role evidence.

## Wave‑3 publication history

The first Wave‑3 convergence publication PR #473 preserved the four leaf bytes but carried a historical `noop` commit without repository-required provenance trailers. `Skill Eval Contract` correctly rejected that ancestry after document-routing had already passed. PR #473 is therefore historical/rejected publication evidence, not an admissible merge subject.

PR #480 replayed the same reconciled Wave‑3 tree on the then-current main as one provenance-complete commit. Its first exact-head gate epoch became stale when another Human-admitted program, PR #477, advanced `main` during validation.

The current refresh input for this epoch is:

```text
main@2bf90d7182d42dfc3a908ffa68d7ea4b26898042
main tree e002c1cad03df0c64ce87cff649fafabfdd2619c
```

That main movement is not a semantic Wave‑3 parent. It is a repository-freshness dependency: the final #468 publication subject must preserve the admitted #477 UCR/workflow/registry bytes and consume the Wave‑3 selected bytes before a new exact-head verdict can exist.

## Current law

```text
fork-time #455 ancestry                         HISTORICAL_TRUE_PARENT
#455/#379 static deterministic convergence     HUMAN_ADMITTED / MERGED
#475 admission route                           MERGED / ROUTING_INPUT
#477 UCR current-main movement                  ADMITTED_CURRENT_MAIN_INPUT
#469–#472 selected Wave‑3 leaf bytes            IMPLEMENTED_CANDIDATES
#473 provenance-defective convergence           HISTORICAL / REJECTED
#480 predecessor exact-head evidence            HISTORICAL_AFTER_MAIN_DRIFT
current #468 publication subject                MUST_CONSUME_CURRENT_MAIN_AND_SELECTED_LEAVES
```

Re-read `main`, the current #468 PR head, #469–#472 heads, review threads and hosted workflows immediately before Human Admit. A green predecessor head never follows a moving main automatically.

## Evidence ceiling

No authority transition above changes live evidence:

```text
live Codex SDK/controller acceptance       NOT_EXERCISED
live GitHub add/readback/remove canary      NOT_EXERCISED
live Herdr lifecycle                        NOT_EXERCISED
article/PDF/PRD truth                      SOURCE_PROPOSAL / EVIDENCE_DEPENDENT
real source/provider closure               EVIDENCE_DEPENDENT
release / production promotion             NOT_PERFORMED
```

Machine authority remains current GitHub metadata, Git ancestry, executable contracts, exact-head workflow runs and runtime receipts.
