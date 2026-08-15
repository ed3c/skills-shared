# Procedural Shadow Runtime

Reusable side-effect admission and evidence-closure primitive for Agent Skills.

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
```

## State ownership

| Surface | Owns |
|---|---|
| `SKILL.md` | runtime laws, state machine, composition rules |
| `references/context-capsule.schema.json` | source-bound delta capsule contract |
| `references/runtime-receipt.schema.json` | exact-subject evidence/disposition contract |
| `scripts/check_runtime_receipt.py` | deterministic semantic gate |
| `tests/` | positive, mutation, and input-error controls |

## Relationship to Shadow Architecture

`spatial-loop-systems-engineering` discovers hard laws, architecture deltas, failure surfaces, and procedural-grounding drift. This Skill is the smaller runtime primitive that can be composed by any repo agent once procedures are known.

It does not own Git, browser, device, deployment, or domain procedures. Those remain in the corresponding Skills; this layer binds them to side-effect admission and receipts.

## Verification

```bash
python3 skills/procedural-shadow-runtime/tests/verify.py
```

Expected control semantics:

```text
positive receipt + capsule       exit 0
planted semantic mutation        exit 2
missing / malformed input        exit 64
```

Live Claude/Codex hooks, external registry search, multimodal browser/device observers, and causal cross-model evals remain `NOT_EXERCISED` until separately evidenced.
