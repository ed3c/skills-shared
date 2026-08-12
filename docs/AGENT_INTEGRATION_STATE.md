# Agent Integration State

> Machine/operator handoff. Read before changing Skill distribution, eval, verifier, mutation, runtime, release, publication control, or cross-repository routing.
>
> Snapshot: 2026-08-12. `main` includes the implementation-target, verifier-calibration, mutation-admission, release-boundary, drift-proof, infrastructure-CI, and private-Actions publication-gate lines. The current open documentation subject is PR #85; exact head remains GitHub metadata.

## 1. Mission

`skills-shared` keeps five claims separate:

1. **Canonical distribution truth** — which Skill artifact is canonical and where it is projected.
2. **Evaluation truth** — which claims have runnable cases and calibrated deterministic evidence.
3. **Evolution truth** — which mutation was attempted, why, and whether paired evidence supports its terminal state.
4. **Capability truth** — whether post-selection held-out evidence generalizes across real model/harness stacks.
5. **Release truth** — whether a verified capability has immutable release identity, separated scorecards, rollback material, and Human Admit.

Do not collapse these layers into one score, one README, or one CI job.

## 2. Four-repository role

```text
skills-shared       Instruction / Method Plane
runtime-env         secret-free Runtime Contract Plane
bettor-arena        Integration / Acceptance Plane
agent-shield        Domain Product / Reference Consumer Plane
```

Contract flow and routing are in [`integration/CROSS_REPO_INTEGRATION.md`](integration/CROSS_REPO_INTEGRATION.md) and [`architecture/DOCUMENT_ROUTING.md`](architecture/DOCUMENT_ROUTING.md).

## 3. Source-of-truth map

| Directory / file | State-machine responsibility | Produces | Must not decide |
|---|---|---|---|
| `registry.json` | shared/repo-owned classification | canonical/deferred rulings | runtime capability |
| `skills/` | canonical Skill artifact/method | SKILL bodies, method scripts/tests | capability promotion by presence |
| `evals/cases/` | public dev/gold-replay contracts | runnable case specs | holdout feedback |
| `evals/holdout/` | sealed post-selection contracts | opaque held-out identities | optimizer adaptation |
| `evals/fixtures/` | deterministic and calibration inputs | replay controls | final capability score |
| `evals/verifiers/` | hard-gate outcome authority | PASS/FAIL receipts | candidate selection strategy |
| `evals/runtime/` | executor/model/harness/environment identity | execution metadata | release admission |
| `evals/adapters/` | external-harness normalization | canonical run/evidence shape | semantic verifier authority |
| `evals/capability-unlocks.json` | held-out multi-stack capability registry | verified unlocks | popularity compensation |
| `evals/releases.json` | release registry | admitted release receipts | synthetic capability |
| `mutations/` | adaptive candidate lineage | hypotheses, paired evidence, terminal status, promotions | holdout adaptation |
| `scripts/` | deterministic gates/transitions | validation/export/index results | invented evidence |
| `tests/` | positive/hollow/mutation proof | red/green controls | production truth without runtime evidence |
| `.github/workflows/` | orchestration | CI check results | semantic truth beyond executed steps |
| `docs/` | Agent/human routing and handoff | navigation and current state | override of machine authority |

## 4. Integrated state machine

```text
DISCOVERED
→ CANONICALIZED
→ CLAIM_REGISTERED
→ CASE_BOUND
→ VERIFIER_CALIBRATED        # mechanism landed via #73
→ EXECUTABLE
→ EVIDENCE_COLLECTED
→ CANDIDATE_EVALUATED        # mechanism landed via #74
    ├── lost/tie/reverted → PRESERVED
    └── won + recomputed paired evidence → PROMOTION_ELIGIBLE
→ post-selection sealed holdout
→ CAPABILITY_UNLOCKED
→ RELEASE_ADMITTED           # hard gate landed via #76
→ CANONICAL_RELEASED
    └── regression/drift → ROLLBACK or new mutation
```

Fail-closed rules:

- stale/missing implementation targets cannot become `CASE_BOUND`;
- insensitive verifiers fail positive/hollow calibration;
- optimizer targets may not include sealed holdouts;
- terminal mutation states are recomputed from paired current/candidate/no-skill evidence;
- LLM-judge authority alone cannot unlock capability;
- release requires a real unlock, observed multi-stack evidence, rollback artifact, and Human Admit.

## 5. Data flow

```text
SKILL.md + implementation
        ├── registry/shared-skills-infra → canonical projection and drift evidence
        └── public cases + sealed holdout
                    ↓
        target validation + verifier calibration
                    ↓
        runtime / harness adapters
                    ↓
        run trace + deterministic verifier receipt
                    ↓
        content-bound evidence bundle
             ┌──────┴──────┐
             ↓             ↓
       mutation lane   sealed holdout lane
             ↓             ↓
       lineage and     capability unlock
       promotions           ↓
             └────────→ release receipt
                           ├── ecosystem-quality scorecard
                           ├── verified-capability scorecard
                           ├── rollback artifact
                           └── Human Admit
```

## 6. Current implementation status

### Implemented on `main`

- real-incident implementation-target/anchor validation (#72);
- verifier sensitivity/calibration (#73);
- paired evidence mutation admission, holdout isolation, and promotion recomputation (#74);
- canonical-drift mutation controls (#75);
- release receipt, multi-stack identity, separated scorecards, rollback contract (#76);
- Shared Skills Infra hosted CI and portability hardening (#77);
- private GitHub Actions publication cadence, exact-HEAD local verification, billing circuit, and consumer workflow trigger policy (issue #43 and landed implementation line).

The old active Stack `#73 → #74 → #76` is complete; all three PRs merged. Do not present it as pending work.

### Current documentation work

```text
parent: bettor-arena#35
siblings:
  skills-shared#85
  runtime-env#30
  agent-shield-monorepo#78
  bettor-arena#37
convergence after merge:
  bettor-arena#38
```

The four PRs are independent siblings; #38 is the only convergence child because it needs all four merged commits/trees and owns the fresh Claude/Codex cold-start audit.

### Capability and release evidence boundary

Current machine registries remain empty:

```text
evals/capability-unlocks.json  unlocks = []
evals/releases.json            releases = []
```

The release mechanism exists, but the first real capability unlock and canonical release remain absent/not exercised. Do not fabricate them from fixtures, deterministic contract tests, ecosystem quality, or source prose.

## 7. Skill anatomy and loading

```text
SKILL.md      procedural workflow/method/laws
references/   reusable generic contracts/templates
modules/      domain instances loaded on demand
scripts/tests/evals/cases deterministic behavior and controls
README.md     navigation and local ownership
```

Load the procedural core first. Load a reference when the method selects it. Load a domain module only when the repository/provider/task trigger matches. Apply consumer bindings last. A domain module cannot silently become global passive context.

## 8. Agent work protocol

Before editing:

1. Read root routes, this file, and the roadmap.
2. Inspect exact current `main` and PR base/head metadata.
3. Identify one state transition and its authority.
4. Select the implementation target and verifier.
5. Keep holdout, optimizer, verifier, release, and Human authorities separate.
6. Define positive and hollow/mutation controls before implementation.

Before declaring complete:

- synchronize/rebase against the actual parent;
- run the owning workflow and confirm steps executed;
- preserve failed candidates and negative controls;
- update README/current state/traceability when topology changes;
- report all remaining `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, or `SKIPPED_BY_POLICY` states.

## 9. Git Town / Stacked PR convention

Git Town is optional branch synchronization, not authority. GitHub PR base/head metadata remains publication truth.

- independent path-disjoint work → siblings;
- unmerged interface/data dependency → true child;
- smallest reviewable transition → terminal leaf;
- exact merged index/coverage/cold-start after siblings → convergence leaf.

After squash merge, reconstruct/rebase descendants onto the new parent tree and rerun the owning gates. Old green status does not transfer.

## 10. Definition of done for the integrated system

The hard-gate architecture is not complete merely because its schemas/scripts exist. Completion requires:

- all real-incident claims bound to live implementation;
- calibrated deterministic verifiers;
- at least two real model/harness stacks executing the same held-out case identity;
- content-bound run traces, verifier receipts, and evidence bundles;
- mutation winners recomputed, not self-reported;
- sealed holdouts inaccessible to adaptive search;
- real capability unlocks backed by held-out cross-harness evidence;
- immutable releases with separated scorecards and rollback artifacts;
- explicit Human Admit;
- document routes and current handoff synchronized with machine/Git truth.
