---
name: skill-refactor-proof-loop
description: |
  Portable procedure for proving that a Skill refactor preserves old strengths, keeps executable routes reachable, compares frozen treatments fairly on matched tasks, retains failed and stale attempts in the denominator, registers reusable golden proofs, and prevents structural or fixture evidence from being promoted into live runtime or delivery claims.
---

# Skill Refactor Proof Loop

<!-- PORTABLE_CORE_START -->

## Contract

A refactor is not admitted because the new directory is cleaner, the new `SKILL.md` is shorter, or a static checker is green. Admission requires proof appropriate to the claimed layer, with historical treatments frozen and old strengths retained as explicit assertions.

The portable core owns:

```text
treatment freeze
old-strength preservation
route and executable-contract assertions
matched-task fairness
denominator completeness
evidence-layer monotonicity
golden-proof registration
cleanup and authority ceilings
```

Concrete owner Skills, providers, repositories, branches, models, runtimes, commands, receipts, and PR identities remain modules, bindings, runtime environments, or issue/PR evidence.

## State machine

```text
REFRACTOR_PROPOSED
→ OLD_BEHAVIOR_FROZEN
→ TREATMENTS_FROZEN
→ OLD_STRENGTHS_BOUND
→ ROUTES_ASSERTED
→ CONTRACTS_ASSERTED
→ HERMETIC_TASK_EXECUTED
→ DENOMINATOR_RECONCILED
→ GOLDEN_PROOF_REGISTERED
→ ADOPTION_READY
→ LIVE_AB_PENDING
→ LIVE_AB_VERIFIED
→ DELIVERY_EVIDENCE_BOUND
→ HUMAN_ADMIT_REQUIRED
```

A missing prerequisite stops the transition. Do not continue from prose agreement.

## Proof layers

### L0 — source freeze

Freeze immutable bytes for at least:

```text
A   OLD_CANONICAL
B0  REFACTOR_AS_LANDED
B1+ REPAIRED_CANDIDATE
```

The first refactor-as-landed treatment remains visible even when it regressed. Historical treatments are data, not editable implementation.

### L1 — structural reachability

Prove the current route from entrypoint to owned mechanisms. A file existing under `references/`, `modules/`, `scripts/`, or `tests/` is not enough; the owning suite must make dead or hollow routes turn red.

### L2 — executable contract

Bind shape and semantic assertions separately when both exist. Prove trigger/selection, predecessor closure, exact subject, output consumption, evidence kind, and next-state admission. A module link or provider exit code is not causal completion.

### L3 — hermetic real task

Run frozen treatments against the same exact:

```text
repository base and tree
contracts and immutable tests
task graph and acceptance oracles
budget and Worker carrier policy
candidate denominator and tie-break rules
cleanup requirements
```

Use real subprocess/worktree mechanics when the claim includes them. Report output correctness separately from causal/evidence closure.

### L4 — matched live model/runtime

Only exact live receipts may enter this layer. Match model/runtime/task/context/budget/repetition policy and report success, false PASS, unsafe admission, decomposition quality, tool calls, tokens, latency, repair count, cost, candidate diversity, review burden and uncertainty.

### L5 — delivery and Human Admit

Git Town synchronization, Forgejo/GitHub publication, checks, review, merge, release, promotion and rollback are separate state machines. No lower proof layer grants these authorities.

## Mandatory invariants

1. Old strengths remain named and evaluated.
2. A, B0 and repaired candidates use immutable identities.
3. Failed, stale, blocked, cancelled and superseded attempts remain in the denominator.
4. A local task PASS cannot override a failed global objective.
5. A dependent result consumes verified predecessor artifacts, not only parent names.
6. Fixture, synthetic and live evidence remain distinct.
7. Cleanup leaves no active process, worktree, branch, lease or temporary proof state.
8. Provider, publication, merge, release, secret and rollback authority cannot be widened by a Skill.
9. A Git Town child consumes unmerged parent bytes/contracts; path-disjoint work stays sibling work.
10. A golden proof references its owner implementation instead of copying it.

## Standard procedure

### 1. Bind the refactor contract

Validate the packet against `references/refactor-proof-contract.schema.json`, then run `scripts/check_refactor_proof.py`.

### 2. Freeze and compare treatments

Record treatment path and Git blob identity. Never overwrite a frozen fixture to make a candidate pass.

### 3. Preserve old strengths

Convert every load-bearing old behavior into an assertion, oracle, mutation control, or explicit retained non-claim. A new feature cannot compensate for a lost old guarantee.

### 4. Close executable routes

Trace:

```text
SKILL.md
→ selected references/modules
→ deterministic producer/checker
→ owning tests
→ suite runner
→ CI arrival
```

Kill at least one dead-route or hollow-route mutation.

### 5. Execute the claimed task layer

For L3+, run the matched task and bind exact base/tree, process/worktree observations, result lineage, denominator, local/global oracles and cleanup.

### 6. Register the golden proof

Add a content-bound entry only after its checker can replay path, blob, runner, evidence ceiling, denominator and authority assertions. The registry is an index, not a copy of the proof implementation.

### 7. Hand off higher layers

Link each `NOT_EXERCISED`, `ABSENT`, or `HUMAN_ADMIT_REQUIRED` lane to its owner and issue. Do not close the proof gap through wording.

## Stop conditions

Stop with a blocked/failed classification when:

```text
old or as-landed treatment is missing
historical bytes drift
old strength disappears
entrypoint-to-suite route is hollow
comparison subjects or budgets differ
failed/stale attempt is omitted
local PASS hides global FAIL
predecessor artifact is not consumed
fixture is presented as live
cleanup is incomplete
authority widens
Stack ancestry is artificial
golden proof implementation is duplicated
```

## Required outputs

```text
refactor proof contract
frozen treatment identities
old-strength assertion matrix
route/executable-contract receipts
matched-task report where claimed
golden registry entry where eligible
molecular issue/PR graph
remaining evidence owners
rollback subject
Human Admit boundary
```

<!-- PORTABLE_CORE_END -->

## On-demand modules

Load `modules/agentic-tech-lead-golden-proof.md` only when studying, replaying, or extending the first registered golden proof. It cannot become passive context for unrelated refactors.
