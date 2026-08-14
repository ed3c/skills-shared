# Agent Integration State

> Machine/operator handoff. Read before changing Skill distribution, eval, verifier, mutation, runtime, release, publication control, or cross-repository routing.
>
> Snapshot: 2026-08-14. `main` includes the implementation-target, verifier-calibration, mutation-admission, release-boundary, drift-proof, infrastructure-CI, private-Actions publication-gate, and Intent-Bound Constraint lines. The four-repository documentation stack and its convergence owner have all merged. There is no open PR at this snapshot; exact open-head identity, when one exists, remains GitHub metadata.

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

- Intent-Bound Constraint contract, closure evaluator, and four adapter registrations (#98–#102, landed as PRs #104, #105, #106, #111, #107).

The old active Stack `#73 → #74 → #76` is complete; all three PRs merged. Do not present it as pending work.

### Four-repository documentation work — complete

```text
parent: bettor-arena#35            OPEN
siblings:
  skills-shared#85                 MERGED e3b327ad49c088f1962c33167ecd5ac9d28125fb
  runtime-env#30                   MERGED 4a333ccf106ef60bc6942b922b7f5efffb3876f5
  agent-shield-monorepo#78         MERGED 1af04c1ef5cb68eab198987feba008c93d3ec22f
  bettor-arena#37                  MERGED 1f94d3d77992a1396959a15b2ada7836c07bf300
convergence:
  bettor-arena#38                  CLOSED
```

All four siblings and the convergence owner have landed. Only the parent contract issue `bettor-arena#35` is still open; do not present the four siblings as pending.

## 6a. Intent-Bound Constraint stack convergence

Convergence report for #103, after #98–#102 all merged. Per-leaf merged commits and trees are in [`traceability/TRACEABILITY_INDEX.md`](traceability/TRACEABILITY_INDEX.md).

### Owning workflow at each admitted subject

```text
IBC 01  #104  Skill Eval Contract                          SUCCESS
IBC 02  #105  (none)                                       ABSENT — zero runs at head
IBC 03  #106  (none)                                       ABSENT — zero runs at head
IBC 04  #111  Forgejo Delivery Loop Contract               SUCCESS
IBC 05  #107  Git Town Stacked PR Worker / live-canary     SUCCESS
```

The #103 precondition "all owning workflows green at admitted subjects" is **not** satisfied as stated. Two leaves merged with no CI arrival whatsoever. That absence is a distinct state from a pass, and it had consequences that were found by hand rather than by a check:

- #105 shipped `tests/stack-contract/verify.sh` invoking `python3 -m unittest <absolute path>`, which raises `ValueError: Empty module name` on every Python. Its twelve stack-contract mutation controls had never executed once.
- #105 changed `skills/git-town-stacked-pr-worker/evals.json` in four ways and updated none of the matching assertions in `check_publication_boundary.py`, leaving that verifier red on `main`.
- Neither could be reported, because `git-town-stacked-pr-worker.yml` ran only the live canary and never `tests/run-all.sh`.

Both were repaired in #112, on the owning branch rather than inside this convergence subject. A same-shape scan then found four more skills whose suites had no CI arrival at all — `github-delivery-loop`, `gitlab-delivery-loop`, `html-for-decisions`, `knowledge-continuity` — all green but unguarded; #113 gave each an arrival and added `scripts/check_suite_ci_coverage.py` so a new suite cannot reopen the gap.

### Intent and constraint coverage

```text
intent-bound contract schema + closure evaluator     IMPLEMENTED  (#104)
git-town-stacked-pr-worker adapter                   IMPLEMENTED  (#105)
knowledge-continuity adapter                         IMPLEMENTED  (#106)
forgejo-delivery-loop adapter                        IMPLEMENTED  (#111)
github-delivery-loop adapter                         ABSENT
gitlab-delivery-loop adapter                         ABSENT
```

### Runnable evaluator and control coverage

```text
skills/git-town-stacked-pr-worker/tests/run-all.sh   2 verifiers, CI since #112
skills/forgejo-delivery-loop/tests/run-all.sh        3 verifiers, CI since #111
skills/knowledge-continuity/tests/run-all.sh         2 verifiers, CI since #113
skills/github-delivery-loop/tests/run-all.sh         8 verifiers, CI since #113
skills/gitlab-delivery-loop/tests/run-all.sh         5 verifiers, CI since #113
skills/html-for-decisions/tests/run-all.sh           3 verifiers, CI since #113
scripts/check_suite_ci_coverage.py                   gates the above, CI since #113
```

### Live versus offline evidence

```text
offline stack-graph, routing, and contract closure   IMPLEMENTED
live git-town 24.0.0 binary admission                EXERCISED    (#107 CI)
real linked-worktree sync                            EXERCISED    (#107 CI)
semantic conflict fail-closed canary                 EXERCISED    (#107 CI)
remote publication                                   NOT_EXERCISED
live Forgejo session and external mutation           NOT_EXERCISED
consumer repository adoption                         NOT_EXERCISED
```

The Git Town evidence became live only at #107, and only after the pinned release was corrected: the admitted artifact named git-town 22.9.0 and asset `git-town_linux_amd64.deb`, neither of which exists upstream, so the canary had failed its first download on every run and no assertion after it had ever executed. It is now pinned to a verified 24.0.0.

### Remaining explicit states

```text
ABSENT              github-delivery-loop and gitlab-delivery-loop intent registrations
ABSENT              .github-delivery/ci-policy.json for this private repository (#82)
NOT_EXERCISED       remote publication, live Forgejo session, consumer adoption
NOT_EXERCISED       first physical capability unlock and canonical release
NOT_IMPLEMENTED     semantic authority and ambiguity decisions as deterministic checks
HUMAN_ADMIT_REQUIRED  merge, promotion, permission and legal widening, rollback
```

### Cold-start navigation audit — 2026-08-14

```text
relative links in README, AGENTS, CONTEXT, docs/INDEX,
  STATE_MACHINES, TRACEABILITY_INDEX, AGENT_INTEGRATION_STATE   0 broken
skills shipping a README                                        6 of 23
those 6 routed from docs/INDEX.md                               6 of 6
```

`repo-agent-native` shipped a README in #93 without a route in `docs/INDEX.md` and was reachable only by guessing the path; that route now exists. The remaining 17 skills have no nearest-README route to omit. An omitted index entry is invisible by construction — a short index and a complete one read identically — so the audit counts both directions rather than only following the links that are present.

### Rollback subject

`a3592f9129982cb9f30b228077ece0b2ab610f34` was `main` before this line of work began; each leaf is independently revertible at the merged commits recorded in the traceability index. No capability unlock or release receipt was created, so there is no release identity to roll back.

### Human Admit still required

Merge and release promotion remain Human-owned. This report records what landed and what is still absent; it does not admit any capability, release, or consumer adoption.

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
