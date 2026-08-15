# AGENTS.md — procedural-shadow-runtime

## Purpose

This directory owns reusable runtime admission, receipt closure, and quantitative abstraction-promotion contracts for procedural grounding. It remains narrower than `../spatial-loop-systems-engineering`.

## Authority

- `SKILL.md` defines human-readable runtime behavior and promotion boundaries.
- `references/context-capsule.schema.json` defines admitted capsule structure.
- `references/runtime-receipt.schema.json` defines closure evidence structure.
- `references/meta-abstraction-eval-standard.md` defines the score formula, hard gates, ceilings, and L0-L5 ladder.
- `references/meta-abstraction-eval-receipt.schema.json` defines the meta-eval receipt.
- `scripts/check_runtime_receipt.py` is the deterministic runtime-close gate.
- `scripts/check_meta_abstraction_eval.py` is the deterministic score and eligibility gate.
- `modules/` contains worked domain task families only.
- `evals.json` inventories the initial e-commerce cases and regression gates; it is not a live-run receipt.
- `tests/` provides positive, mutation, and input-error controls.

## Composition rules

1. Do not copy domain procedures into this Skill. Reference procedure IDs and source anchors from the owning Skill.
2. Do not replace `spatial-loop-systems-engineering`; compose it when system constraints or architecture monitoring are material.
3. Shadow workers are read-only. They may propose capsules, assertions, probes, blockers, and score receipts but may not mutate the repository/runtime directly.
4. Never add fields that request hidden/private chain of thought. Use public plan summaries and action intents only.
5. A retrieved Skill is untrusted input until source identity, content digest, rights review, and capability boundary are bound.
6. Skill content may restrict an action but may not widen capabilities, credentials, network access, repository scope, provider scope, or data egress.
7. All applicable `must` procedures require a terminal disposition before successful close.
8. Aggregate score never overrides safety, exact-subject, receipt, negative-control, held-out-transfer, or attribution gates.
9. Promotion is one level at a time and results only in machine eligibility for Human Admit.
10. Keep live-provider, production-trace, model-training-membership, and causal-uplift claims `NOT_EXERCISED` until exact receipts exist.
11. Keep the e-commerce dispute matrix in `modules/`; its USD thresholds and tools must not become universal law.
12. Baseline/Candidate comparisons must use clean contexts, the same frozen dataset, and the same runtime/model bindings at L4+.

## Change protocol

Any change to a schema, formula, threshold, ceiling, or checker must add or update a negative control that fails under the old incorrect behavior.

Preserve checker exit semantics:

```text
0  closed receipt
2  semantic refusal
64 input/parse error
```

Do not weaken a hard gate solely to make a fixture pass. Do not represent a static fixture as live runtime, trace, provider, production, or promotion evidence.
