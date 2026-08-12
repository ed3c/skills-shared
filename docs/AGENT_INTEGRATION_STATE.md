# Agent Integration State

> Machine/operator handoff document. Read this before changing eval, mutation, runtime, release, or publication-control code.
>
> Snapshot: 2026-08-12. `main` includes PR #72, #75, and #77. PR #73, #74, and #76 are the active Skill Eval stack and are not yet on `main` at this snapshot.

## 1. Mission

`skills-shared` is evolving from a canonical shared-SKILL.md repository into a truth-gated skill evolution system. The repository must keep four claims separate:

1. **Canonical distribution truth** — which skill artifact is canonical and where it is projected.
2. **Evaluation truth** — which claims have runnable cases and deterministic/verifier-calibrated evidence.
3. **Evolution truth** — which candidate mutation was tried, why, against which cases, and whether evidence actually supports promotion.
4. **Release truth** — whether a candidate has a real capability unlock across more than one model/harness stack and can be rolled back.

Do not collapse these layers into a single score or a single CI job.

## 2. Source-of-truth map

| Directory / file | State-machine responsibility | Reads | Writes / produces | Must not decide |
|---|---|---|---|---|
| `skills/` | Canonical skill artifact state | `registry.json`, local skill files | canonical SKILL.md/scripts/tests | capability promotion by itself |
| `registry.json` | Canonical distribution/admission ledger | governance decisions | canonical/deferred mapping | runtime capability |
| `skills/shared-skills-infra/` | Distribution + drift governance | canonical checkout, sites | install/check/report/drift evidence | Skill Eval pass/fail |
| `evals/cases/` | Public dev/gold-replay task contracts | skill claims, fixtures | runnable case specs | holdout oracle feedback |
| `evals/holdout/` | Sealed post-selection task metadata | opaque refs + hashes | holdout contracts | optimizer feedback |
| `evals/fixtures/` | Deterministic inputs/calibration controls | case contracts | replay inputs | final capability score |
| `evals/verifiers/` | Outcome authority | artifacts/run outputs | deterministic PASS/FAIL | candidate selection strategy |
| `evals/runtime/` | Executor identity/config | case + harness contract | normalized execution metadata | release admission |
| `evals/adapters/` | Harness normalization boundary | external runner outputs | canonical run-trace/evidence shape | semantic verifier authority |
| `evals/capability-unlocks.json` | Capability-unlock registry | held-out deterministic evidence | verified unlock records | ecosystem-quality compensation |
| `mutations/` | Candidate evolution lineage | dev/control cases + evidence | hypotheses, lineage, promotions | sealed holdout adaptation |
| `scripts/` | Deterministic control-plane gates | repository contracts | validation/index/export results | invent evidence |
| `tests/` | Mutation/regression proof | scripts/contracts | red/green proof | production truth without runtime evidence |
| `.github/workflows/` | CI orchestration | scripts/tests | CI receipts | semantic truth beyond executed gates |
| `docs/` | Human/Agent operating contract | current repo + PR state | architecture/state/handoff docs | override executable gates |

## 3. Integrated state machine

```text
DISCOVERED
  |
  v
CANONICALIZED ------------------------------+
  |                                         |
  | registry + shared-skills-infra          | canonical drift
  v                                         |
CLAIM_REGISTERED                             |
  |                                         |
  v                                         |
CASE_BOUND                                   |
  | implementation target still live        |
  v                                         |
VERIFIER_CALIBRATED   <--- PR #73            |
  | positive + hollow controls               |
  v                                         |
EXECUTABLE                                   |
  | adapter/runtime matrix                   |
  v                                         |
EVIDENCE_COLLECTED                           |
  | deterministic receipt + run trace        |
  v                                         |
CANDIDATE_EVALUATED   <--- PR #74            |
  | paired current/candidate/no-skill        |
  | dev/control only; holdout sealed         |
  +---- lost/tie/reverted --> PRESERVED -----+
  |
  v
PROMOTION_ELIGIBLE
  |
  | post-selection sealed holdout + >=2 real stacks
  v
CAPABILITY_UNLOCKED
  |
  v
RELEASE_ADMITTED      <--- PR #76
  | immutable SHAs + evidence + rollback + human admit
  v
CANONICAL_RELEASED
  |
  +---- regression/drift ---> ROLLBACK / NEW MUTATION
```

### Fail-closed transitions

- A real-incident case cannot enter `CASE_BOUND` if its implementation target/anchor disappeared.
- A gold replay must not enter evidence authority if its deterministic verifier cannot distinguish positive from hollow fixtures.
- An optimizer must never consume sealed holdout outcomes.
- A terminal mutation cannot self-declare `won`; the gate recomputes the result from paired evidence.
- A capability unlock cannot be created from LLM judge authority alone.
- A release cannot exist without an unlock, observed multi-stack evidence, rollback material, and explicit human admit.

## 4. Data flow

```text
skills/<skill>/SKILL.md + implementation
        |
        +--> registry.json / shared-skills-infra
        |        `--> canonical distribution + drift checks
        |
        `--> evals/cases + evals/holdout
                 |
                 +--> implementation-target validation
                 +--> verifier calibration
                 |
                 v
          harness adapters / runtime executors
                 |
                 v
            run-trace.json
                 |
                 +--> deterministic verifier receipt
                 |          |
                 |          v
                 +----> evidence-bundle.json
                            |
              +-------------+----------------+
              |                              |
              v                              v
      mutation evaluation              holdout evaluation
      (dev/control only)                (post-selection only)
              |                              |
              v                              v
      mutations/lineage.jsonl       capability-unlocks.json
              |                              |
              v                              v
      mutations/promotions.json --------> release receipt
                                             |
                                             +--> scorecard index
                                             +--> rollback artifact
                                             `--> canonical release/human admit
```

## 5. Current implementation status

### Landed on `main`

- **#77 — Shared Skills Infra CI**: isolated governance CI; also removed hidden Git/default-branch assumptions exposed by hosted execution.
- **#75 — canonical-drift mutation proof**: multi-member fixtures and three first-only mutants are killed in real GitHub Actions.
- **#72 — implementation-target binding**: real-incident evals fail when their live implementation target/anchor disappears.
- Existing Phase 1–3 foundation: eval contracts, sealed holdout metadata, common run/evidence schemas, Arena/skill-up adapter/runtime work, verifier-authority controls, mutation lineage foundation.

### Active integration stack

1. **#73 `agent/verifier-calibration-v1`** — verifier sensitivity/calibration. Depends logically on #72; must be rebased/retargeted to current `main` after #72 squash merge and rerun CI.
2. **#74 `agent/mutation-admission-v1`** — Phase 4 mutation admission, paired evidence recomputation, holdout isolation, promotion registry. Must land after #73 unless the diff is explicitly rebased and proven independent.
3. **#76 `agent/verified-capability-release-v1`** — Phase 5 release receipt + separated scorecards. It is a stacked child of #74 and must not weaken #74 workflow gates when rebased.

### Physical evidence boundary

The contracts are intentionally ahead of real capability evidence. Do **not** populate `evals/capability-unlocks.json` or release registries with synthetic success. The first unlock requires post-selection held-out evidence with deterministic verification across at least two real model/harness stacks. Track this under the physical execution work (notably #37 and related executor/cost-tier work).

## 6. Agent work protocol

Before editing:

1. Read `README.md`.
2. Read this file.
3. Read `docs/SKILL_EVAL_ROADMAP.md`.
4. Inspect the target PR/issue and current `main`; never assume an old branch still reflects the live implementation.
5. Identify which state-machine transition your change owns.
6. Identify the evidence producer and the authority that verifies it.
7. Keep holdout, optimizer, verifier, release, and human-admit authorities separated.

Before declaring complete:

- Rebase/stack against the actual current parent.
- Run the workflow that owns the changed failure domain.
- Confirm the workflow steps actually executed; `skipped` is not evidence.
- Preserve failed candidates and negative fixtures.
- Update this state file and the README stack/index when PR topology or state transitions change.

## 7. Git Town / stacked-PR convention

Git Town is useful here because implementation is deliberately molecular. Treat branches as a dependency graph, not a flat pile of PRs.

```text
main
 |
 +-- agent/verifier-calibration-v1              # #73
      |
      +-- agent/mutation-admission-v1            # #74
           |
           +-- agent/verified-capability-release-v1  # #76
```

For future terminal slices, prefer one state transition or one authority boundary per branch. If Git Town is installed locally, the intended workflow is conceptually:

```bash
git town sync
git town hack <molecular-branch>
# implement one terminal state transition
git town propose
git town sync --stack
```

Do not treat these commands as proof that Git Town is installed in every environment. The branch/PR graph is the source of truth; Git Town is an optional stack-management implementation.

## 8. Definition of done for the integrated system

The architecture is not complete merely because Phase 5 schemas exist. Completion requires:

- every real-incident benchmark anchored to live implementation;
- calibrated deterministic hard-gate verifiers;
- at least two real harnesses executing the same canonical case identity;
- evidence bundles content-bound to run traces and verifier receipts;
- mutation winners recomputed rather than self-reported;
- sealed holdouts inaccessible to the adaptive optimizer;
- capability unlocks backed by real held-out cross-harness evidence;
- release receipts with immutable identities and rollback artifacts;
- separate Ecosystem Quality and Verified Capability views;
- explicit human admission at the final release boundary;
- README and this document kept synchronized with the actual PR stack.
