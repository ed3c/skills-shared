# Agent contract — `universal-refactor-controller`

This directory is governed by the repository root `AGENTS.md` plus this nearest contract. Read this file before changing controller composition, adapters, evidence rules, tests, canary records, or navigation.

## Mandatory read order

1. `README.md` — current State Machine, DAG, evidence ceilings and handoff.
2. `SKILL.md` — portable composition law.
3. `references/controller-contract.schema.json` and `references/complexity-delta.schema.json`.
4. `modules/target-adapter-contract.md` and the selected adapter manifest.
5. `scripts/assert_controller_gate.py` and `tests/` when changing executable behavior.
6. `evals/canaries/` when changing canary/golden evidence.
7. Exact issue/PR/workflow metadata before acting on mutable delivery state.

## Role separation

### Tech Lead

Owns:

```text
exact target and treatment binding
capability / old-strength freeze
root-cause graph
candidate and rejected-alternative set
task/capability DAG
path leases
convergence ownership
global objective
Complexity Delta assertion
residue/regression closure
Local Handoff packet
```

Tech Lead is a writer only inside its admitted lease. It cannot manufacture another owner's receipt.

### Shadow Architect monitor

Shadow is independent and read-only. It must inspect the same immutable subject and attack the global objective, evidence ceiling, ownership model, replacement burden and complexity relocation risk.

Shadow may emit:

```text
ELIGIBLE_FOR_IMPLEMENTATION
HOLD
REJECT
HUMAN_ADMIT_REQUIRED
```

Shadow must not edit the candidate under review, reuse Tech Lead's conclusion as independent evidence, or promote a lower evidence lane.

### Owner Skills

One authority remains canonical for each plane:

```text
repository-entropy-reclamation    entropy/safe-cut proof
skill-refactor-proof-loop         treatment and old-strength proof
agentic-tech-lead-orchestration   DAG/lease/convergence mechanics
procedural-shadow-runtime         independent review mechanics
git-town-stacked-pr-worker        molecular delivery mechanics
universal-refactor-controller     composition + Complexity Delta only
```

Do not copy an owner mechanism locally because it is convenient.

## Writer leases

Parallel work is legal only when paths and produced artifacts are disjoint. Typical leases:

```text
contract/schema        SKILL.md + references/**
checker/evals          scripts/** + tests/**
adapters               adapters/** + modules/**
canary evidence        evals/canaries/**
convergence/docs       README.md + AGENTS.md + shared registry/CI/index routes
```

A child branch exists only when it consumes unmerged parent bytes or proof artifacts. Path-disjoint work is a sibling. One convergence owner updates shared indexes after prerequisite receipts exist.

## State transition law

Do not advance the controller unless the preceding state has exact evidence. In particular:

- file/tool presence is not applicability proof;
- a candidate is not admitted until entropy/consumer/boundary evidence exists;
- a treatment is not preserved until required capabilities and old strengths have exact evidence;
- local deterministic PASS is not live-runtime PASS;
- remote CI PASS is not production safety;
- open PR success is not merged/golden truth;
- documentation cannot promote mechanism state;
- skipped workflows remain `SKIPPED_BY_POLICY`.

## Complexity law

Do not optimize LOC. Require at least one strict reduction in a frozen non-LOC dimension and no hidden regression in protected dimensions. New sources of truth, ownership edges, synchronization paths, policy authorities, dependencies or replacement burden must remain explicit.

If a cut deletes code but moves the same obligation behind another wrapper, adapter, caller, generated layer, config surface or service, classify it `COMPLEXITY_RELOCATED`.

## Target adapter law

Adapters may enumerate observable surfaces, add constraints, narrow effects and narrow authority. They may not:

```text
decide safe simplification
admit an entropy cut
remove a core Complexity Delta dimension
hide dynamic/persisted/generated/compatibility consumers
promote evidence
make installation/file presence applicability proof
widen filesystem/network/secret/merge/release/promotion authority
copy mutable consumer state into the portable core
```

Ambiguity is `HOLD`.

## Canary and Golden Refactor law

Canary records are evidence indexes, not copied implementations. An entry may become golden only when its treatment and verification subjects are replayable and immutable at the required delivery state. While the candidate is an open PR, use `HOLD_UNMERGED`; do not embed its mutable head SHA as durable truth.

Two successful target classes prove bounded transfer only. Do not write `universal`, `production-safe`, or `works on any repo` as a verified result from the current corpus.

## Verification obligation

For mechanism changes, run the nearest UCR suite. For convergence changes, additionally require repository CI surfaces whose inputs changed:

```text
skills/universal-refactor-controller/tests/run-all.sh
Skill Suites
Shared Skills Infra
Skill Eval Contract / document-route guard when indexes or routes change
```

A failing adjacent gate is a real blocker until causal analysis proves it unrelated. If the failure is caused by this line, repair it in an isolated leaf or this convergence owner as appropriate; do not hide it.

## Human-owned operations

Agents must stop at:

```text
semantic conflict admission
intentional capability change without prior authority
force push
merge
release
promotion
governance permission widening
production rollback
```

An explicit Human request may authorize preparation and classification changes, but merge/release still require their own admission.

## Local Handoff packet

When the required verifier belongs to another physical/runtime/Human lane, record:

```text
exact subject or immutable locator
missing evidence lane
command or observation required
acceptance oracle
expected receipt location
current blocker
owner of the next action
rollback/cleanup condition
```

Do not substitute `NOT_EXERCISED` with prose saying the work is expected to pass.

## Completion report

Every implementation session ends by stating:

```text
what changed
issue / PR graph
exact evidence actually observed
Shadow verdict and evidence ceiling
failures discovered and whether they are causal
remaining blockers
next legal frontier
Human-owned operations still pending
```
