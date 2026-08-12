# Skill Quality & Capability Evaluation Roadmap

This roadmap keeps `skills-shared` focused on reusable skill artifacts, eval contracts, fixtures, baselines, and mutation lineage. Execution engines and promotion authorities remain adapters/consumers rather than being reimplemented here.

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

## Phase 5 — Capability unlocks and release scorecards

Keep two scorecards separate:

1. **Ecosystem Quality** — provenance, installability, security, documentation, compatibility, drift.
2. **Verified Capability** — routing F1, task pass rate, skill lift, generalization gap, recovery, efficiency, safety, capability unlocks.

A capability unlock means the candidate repeatedly solves a held-out real task that both no-skill and the current production skill mostly fail, with deterministic outcome verification across more than one model/harness stack.

Exit criteria:

- generated dashboard index contains both scorecards without collapsing them into one number;
- release receipt pins immutable skill SHA, eval suite SHA, harness/model matrix, evidence bundle, and rollback target;
- capability unlock registry links each claim to its replay evidence.
