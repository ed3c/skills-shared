# Procedural Shadow Runtime

Reusable side-effect admission, evidence-closure, and abstraction-promotion primitive for Agent Skills.

## Data flow

```text
Task + public candidate plan/action intents
        ↓
Applicable Skill procedures + source anchors
        ↓
Procedure gap = applicable - already satisfied - prior verified evidence
        ↓
Context Capsule admission
        ↓
PRE_SIDE_EFFECT_GATE
        ↓
Builder/tool execution
        ↓
assertions + multimodal evidence
        ↓
Runtime Receipt reconciliation
        ↓
PASS / BLOCKED / FAIL
        ↓
optional Meta-Abstraction Evaluation
        ↓
ELIGIBLE_FOR_HUMAN_ADMIT / HOLD / REJECT
```

## State ownership

| Surface | Owns |
|---|---|
| `SKILL.md` | runtime laws, state machine, composition, promotion boundary |
| `references/context-capsule.schema.json` | source-bound delta capsule contract |
| `references/runtime-receipt.schema.json` | exact-subject evidence/disposition contract |
| `references/meta-abstraction-eval-standard.md` | four-plane score, ceilings, L0-L5 requirements |
| `references/meta-abstraction-eval-receipt.schema.json` | machine-readable meta-eval receipt |
| `modules/ecommerce-dispute-eval-matrix.md` | worked e-commerce task family and edge cases |
| `evals.json` | machine-readable eval inventory and initial regression gates |
| `scripts/check_runtime_receipt.py` | deterministic runtime-close gate |
| `scripts/check_meta_abstraction_eval.py` | deterministic score/promotion eligibility gate |
| `tests/` | positive, mutation, and input-error controls |

## Relationship to Shadow Architecture

`spatial-loop-systems-engineering` discovers hard laws, architecture deltas, failure surfaces, and procedural-grounding drift. This Skill is the smaller runtime primitive that any repo agent can compose once procedures are known.

It does not own Git, browser, device, deployment, or business-domain procedures. Those remain in the corresponding Skills; this layer binds them to side-effect admission, exact-subject receipts, regression evidence, and one-step abstraction eligibility.

## Quantitative promotion model

```text
Meta Score =
  30% Agent Architecture Score
+ 30% Procedural Grounding Score
+ 25% Generalization Score
+ 15% Regression / Feedback Score
```

A high raw score cannot bypass:

- safety and HITL failures;
- unresolved applicable `must` procedures;
- missing exact-subject evidence;
- absent negative controls;
- missing held-out task families;
- incomplete five-condition attribution;
- missing production feedback closure for L5.

The checker reports only machine eligibility. Human Admit remains required.

## Verification

Runtime receipt controls:

```bash
python3 skills/procedural-shadow-runtime/tests/verify.py
```

Meta-abstraction controls:

```bash
python3 skills/procedural-shadow-runtime/tests/verify_meta_eval.py
```

Expected semantics:

```text
positive contract               exit 0
planted semantic mutation       exit 2
missing / malformed input       exit 64
```

## Evidence boundary

```text
static Skill/docs/schema/checker/fixtures          IMPLEMENTED
one-step score and ceiling rules                    IMPLEMENTED
e-commerce edge-case module                         IMPLEMENTED
live Claude/Codex hooks                             NOT_EXERCISED
live external registry retrieval                    NOT_EXERCISED
live multimodal browser/device observation          NOT_EXERCISED
live Langfuse/OpenTelemetry production feedback     NOT_EXERCISED
cross-model causal uplift                           NOT_EXERCISED
actual promotion                                    HUMAN_ADMIT_REQUIRED
```
