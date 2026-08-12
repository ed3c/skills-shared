# Skill Quality & Capability Evaluation Roadmap

This roadmap keeps `skills-shared` focused on reusable skill artifacts, eval contracts, fixtures, baselines, and mutation lineage. Execution engines and promotion authorities remain adapters/consumers rather than being reimplemented here.

> **Live state vs target state:** this file defines the target Phase architecture. Agents must read [`AGENT_INTEGRATION_STATE.md`](AGENT_INTEGRATION_STATE.md) for the current landed/open/physical-evidence state before implementing the next step.
>
> Snapshot 2026-08-12: implementation-target binding (#72) is landed; verifier calibration (#73), mutation admission (#74), and verified release (#76) form the active contract stack. Real cross-harness capability-unlock evidence remains a separate physical-execution requirement.

## Phase 1 — Eval contract and truth gate

Goal: make skill quality claims mechanically testable before adding expensive model runs.

Deliverables:

- `skill-eval-contract/v1` schema;
- non-empty claim/case coverage registry;
- fail-closed validator for missing/fabricated coverage;
- deterministic outcome verifier requirement for hard-gate cases;
- first gold replay from a real failure (`skills-shared#25`);
- CI that runs the validator and mutation-style fixtures.

Exit criteria:

- every registered claim maps to at least one existing runnable case;
- every runnable case maps back to registered claims;
- hard-gate cases cannot use LLM self-judgment as their only verifier;
- fixture and verifier paths resolve inside the repository;
- the issue #25 replay has a deterministic offline verifier.

Current hardening adds a benchmark-freshness rule: real-incident evals bind to live implementation targets, and gold-replay verifier calibration is the next authority boundary.

## Phase 2 — Convert one existing skill family end to end

Pilot: `autoresearch-composer`.

Convert existing positive/negative routing cases into `skill-eval/v1`, then add downstream outcome cases so the suite measures whether the selected workflow produces a better usable artifact rather than merely emitting expected tokens.

Required conditions per capability case:

- `no_skill`;
- `current_skill`;
- `candidate_skill`.

Add near-miss, wrong-skill, recovery, and adversarial cases. Keep holdout cases outside the prompt-optimization loop.

Exit criteria:

- routing precision/recall can be computed;
- candidate vs current and candidate vs no-skill deltas can be computed;
- at least one hidden/held-out slice exists;
- failure reasons use a controlled taxonomy.

## Phase 3 — Harness matrix and executor adapters

Add adapters rather than a new runner. Initial targets:

- existing Arena/control-plane consumer;
- Alibaba `skill-up`;
- BenchFlow/SkillsBench-compatible export where useful.

The canonical run identity is:

`task × condition × skill_sha × model × harness × environment × seed`.

Add context, tool, state, and task perturbations. A skill that only succeeds under one model/harness pair is reported as harness-specific rather than generalized.

Exit criteria:

- common `run-trace` and `evidence-bundle` schemas;
- at least two harnesses can execute the same case contract;
- cross-harness variance and generalization gap are reported;
- retries are explicit and zero-retry runs remain available for promotion evidence.

Contract/runtime adapters exist, but **contract support is not the same as physical capability evidence**. Promotion/unlock claims require actual execution on at least two real stacks.

## Phase 4 — Skill/prompt evolution loop

Every candidate mutation carries:

- parent SHA;
- hypothesis;
- mutation class;
- target failures/cases;
- expected metric effect;
- non-target regression budget.

Allowed mutation classes include trigger, routing, knowledge, tool-contract, verification, recovery, context-management, example, and negative-instruction changes.

One main hypothesis per candidate keeps causal attribution and rollback possible.

Exit criteria:

- lineage is machine-readable;
- optimizer cannot read holdout/oracle material;
- every fixed real-world failure becomes a regression case;
- candidate promotion requires positive paired evidence without critical safety regression.

Implementation stack: **PR #74 `agent/mutation-admission-v1`**. It recomputes terminal wins from paired current/candidate/no-skill evidence, separates target and non-target controls, rejects holdout leakage, and preserves failed candidates outside the promotion registry.

## Phase 5 — Capability unlocks and release scorecards

Keep two scorecards separate:

1. **Ecosystem Quality** — provenance, installability, security, documentation, compatibility, drift.
2. **Verified Capability** — routing F1, task pass rate, skill lift, generalization gap, recovery, efficiency, safety, capability unlocks.

A capability unlock means the candidate repeatedly solves a held-out real task that both no-skill and the current production skill mostly fail, with deterministic outcome verification across more than one model/harness stack.

Exit criteria:

- generated dashboard index contains both scorecards without collapsing them into one number;
- release receipt pins immutable skill SHA, eval suite SHA, harness/model matrix, evidence bundle, and rollback target;
- capability unlock registry links each claim to its replay evidence.

Implementation stack: **PR #76 `agent/verified-capability-release-v1`**, stacked on #74. The registry intentionally remains empty until physical evidence satisfies the unlock boundary; synthetic fixtures may validate the contract but may not manufacture an unlock.

## Required landing / evidence sequence

```text
#72 implementation target binding          LANDED
        |
        v
#73 verifier calibration                   ACTIVE
        |
        v
#74 mutation admission                     ACTIVE
        |
        v
#76 release receipt + scorecard boundary   ACTIVE
        |
        v
physical post-selection holdout execution  REQUIRED
        |
        v
first real Capability Unlock               NOT YET CLAIMED
```

When a parent PR is squash-merged, rebuild/rebase the child on the new parent/main and rerun the owning CI. Old green checks on obsolete ancestry are not merge authority.
