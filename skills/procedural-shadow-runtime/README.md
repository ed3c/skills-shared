# Procedural Shadow Runtime

Reusable side-effect admission, evidence closure, executable Agent Architecture assessment, and bounded abstraction-promotion primitive for Agent Skills.

## Data flow

```text
Task + public candidate plan/action intents
        ↓
Applicable Skill procedures + source anchors
        ↓
Procedure delta
        ↓
Context Capsule + PRE_SIDE_EFFECT_GATE
        ↓
Builder/tool execution
        ↓
Assertions + exact-subject evidence
        ↓
Runtime Receipt closure
        ↓
Executable Agent Architecture Rubric
        ↓
Meta-Abstraction Evaluation
        ↓
ELIGIBLE_FOR_HUMAN_ADMIT / HOLD / REJECT
```

## State ownership

| Surface | Owns |
|---|---|
| `SKILL.md` | Runtime laws, executable rubric procedure, domain composition, promotion boundary |
| `references/context-capsule.schema.json` | Source-bound delta capsule |
| `references/runtime-receipt.schema.json` | Exact-subject runtime closure |
| `references/agent-architecture-rubric.json` | Five dimensions, positive procedure atoms, Vibe contradictions, weights |
| `references/agent-architecture-eval-receipt.schema.json` | Atomic architecture evidence receipt |
| `references/meta-abstraction-eval-standard.md` | Four-plane score, ceilings, L0–L5 requirements |
| `references/meta-abstraction-eval-receipt.schema.json` | Meta-eval v2 receipt |
| `scripts/check_agent_architecture_eval.py` | 100-point architecture score and Vibe contradiction gate |
| `scripts/check_meta_abstraction_eval.py` | Meta score and one-step eligibility gate |
| `modules/ecommerce-dispute/` | Executable worked domain family and adapter protocol |
| `evals.json` | Eval inventory and routing, not a live provider receipt |
| `tests/` | Positive, Vibe, unsafe-adapter, mutation, and input controls |

## 100-point architecture assessment

The five source dimensions remain:

```text
control flow and state governance        25
tool boundary and idempotency            20
context budget and memory                20
fault tolerance, self-healing, and HITL  20
Evals and observability                  15
```

The checker does not trust five manually entered dimension ratings. It derives points from every source-derived positive control and Vibe signal:

```text
criterion or signal
-> exact subject
-> executable assertion/probe/trace/negative control
-> terminal evidence state
-> contradiction check
-> recomputed score and band
```

A detected Vibe signal invalidates its mapped positive controls. Critical non-idempotent writes and model-owned high-risk authority cap the score at `59`.

## Domain decoupling

The e-commerce dispute example is one executable task family, not universal law.

```text
universal concepts:
  deterministic state machine
  bounded timeout/retry
  context budget
  idempotent writes
  high-risk HITL
  Evals + trace

domain-only constants:
  USD 500
  logistics 5s timeout
  vision evidence
  refund/voucher/reject
  15s / 1500 tokens / USD 0.05
```

A consumer supplies an adapter. The runner executes six mock cases and emits deterministic assertion receipts.

## Verification

```bash
python3 skills/procedural-shadow-runtime/tests/verify.py
python3 skills/procedural-shadow-runtime/tests/verify_agent_architecture_eval.py
python3 skills/procedural-shadow-runtime/tests/verify_ecommerce_eval.py
python3 skills/procedural-shadow-runtime/tests/verify_meta_eval.py
```

Expected semantics:

```text
positive or closed low-band assessment   exit 0
semantic/assertion/mutation refusal       exit 2
missing or malformed input               exit 64
```

## Evidence boundary

```text
rubric/procedure atoms/checkers/fixtures              IMPLEMENTED
local deterministic positive/Vibe/domain controls     IMPLEMENTED
live Claude/Codex hooks                                NOT_EXERCISED
live external registry retrieval                      NOT_EXERCISED
live multimodal browser/device observation            NOT_EXERCISED
live Langfuse/OpenTelemetry production feedback       NOT_EXERCISED
cross-model causal uplift                             NOT_EXERCISED
actual abstraction promotion                          HUMAN_ADMIT_REQUIRED
```
