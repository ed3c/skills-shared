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
READY_FOR_HUMAN_ADMIT / HOLD / REJECT
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
| `evals.json` | Repository eval-plane declaration: each runnable claim bound to the checker and test that exercise it |
| `evals/meta-evals.json` | Meta-eval inventory/routing, not a live provider receipt |
| `tests/run-all.sh` | Entry point the repository runner and CI matrix discover |
| `tests/` | Positive, Vibe, unsafe-adapter, mutation, and input controls |

## Independent Shadow State Machine

```text
EXACT_SUBJECT_BOUND
→ REQUIREMENT_APPLICABILITY_CLASSIFIED
→ SOURCE_AND_CONTRACT_CONTRADICTIONS_CHECKED
→ PRE_SIDE_EFFECT_GATE_ASSERTED
→ BUILDER_EXECUTION_OBSERVED
→ ASSERTION_AND_RECEIPT_READBACK
→ LOCAL_TASK_VS_GLOBAL_OBJECTIVE_CHECKED
→ EVIDENCE_CEILING_ASSERTED
→ DENOMINATOR_CLEANUP_ROLLBACK_CHECKED
→ READY_FOR_HUMAN_ADMIT / HOLD / REJECT
```

The Shadow receives the Tech Lead's public plan, action intents, exact subject, contracts and observable evidence. The Shadow does not reuse the Tech Lead's conclusion as independent evidence.

Shadow ownership:

```text
applicability and missing-requirement review
source/document/contract/runtime contradiction detection
global objective versus local task result
false-promotion and evidence-ceiling review
missing owner/issue/eval/receipt discovery
failed/stale/cancelled/superseded/closed-unmerged denominator review
cleanup and rollback review
```

Forbidden Shadow authority:

```text
second canonical state writer
silent edit of the Builder branch
unreviewed semantic-conflict repair
fixture/deterministic PASS → live PASS
model agreement → Human Admit
convergence ancestry → sibling admission
workflow green → release
private chain-of-thought persistence
```

The Tech Lead owns decomposition, leases, Worker admission and convergence. Shadow owns independent findings. A Human or repository controller owns semantic admission, sibling admission, merge, promotion, release and rollback.

## Codex control-plane monitor — #375–#379

When `agentic-tech-lead-orchestration` selects the Codex SDK / GitHub Issue DAG / Herdr / problem-closure lanes, Shadow evaluates the same immutable integration subject through an independent readback path. It does not call itself a second executor.

```text
#375 Codex SDK candidate
  → exact task/attempt/worktree/commit/tree/thread identity
  → post-turn writable-lease readback
  → runtime result remains below implementation acceptance

#376 GitHub Issue DAG candidate
  → portable semantic dual DAG
  → repository/default-branch/visibility + issue-state preflight
  → projected completion edges + exact blockedBy readback
  → refuse extra unmanaged blockers, drift, or start-edge serialization

#377 Herdr candidate v3
  → exact Git/worktree/pane/workspace/PID/native-session identity
  → PID start-time + bounded freshness + process liveness
  → DONE_CANDIDATE requires CLEAN cleanup and zero residue
  → DONE_CANDIDATE remains advisory

#378 problem-closure candidate v3
  → frozen source/problem denominator + claim digest
  → exact repo/commit/tree + portable session/worktree identity
  → CURRENT/HISTORICAL/SUPERSEDED implementation mapping
  → exact-subject verification + matching receipt lanes
  → deterministic supersession/residual/closure recomputation
```

#379 is the single convergence writer. Shadow must read the exact multi-parent convergence candidate and verify:

```text
every selected sibling candidate head is actually an ancestor/consumed subject
selected candidates are not mislabeled admitted/merged
shared run-all executes every required control-plane selftest with no conditional skip
current denominator is Codex 4/14, GitHub DAG 6/17, Herdr 4/18, closure 6/22
README / AGENTS / module / script / test / traceability / Git Town routes match current selected bytes
Git Town index records SIBLING rather than fake TRUE_CHILD edges
open/live/evidence-dependent lanes remain in the denominator
rejected/superseded/closed-unmerged candidate lineage is not erased
no merge/release/Human Admit is inferred from hosted CI
```

A Shadow verdict on a deterministic convergence candidate may be `READY_FOR_HUMAN_ADMIT` only for the named static/deterministic integration scope. It must separately report:

```text
#451/#452/#456/#457 sibling admission      HUMAN_ADMIT_REQUIRED
live Codex SDK execution                   NOT_EXERCISED until runtime receipt
live GitHub dependency mutation/readback   NOT_EXERCISED until remote receipt
live Herdr observation                     NOT_EXERCISED until runtime receipt
real source/provider closure               EVIDENCE_DEPENDENT
#455 merge/release                         HUMAN_ADMIT_REQUIRED
```

A live lane becoming green later does not rewrite the historical static verdict; it creates a new exact-subject receipt and a new closure computation.

## Wave-3 live-evidence monitor — #464–#468

Wave 3 consumes #455 as an unmerged true parent and makes the previously residual live lanes executable without declaring them executed.

```text
#455
├─ #464 / PR #469  Codex live acceptance carrier        TRUE_CHILD
├─ #465 / PR #470  GitHub reversible dependency canary TRUE_CHILD
├─ #466 / PR #471  Herdr lifecycle carrier             TRUE_CHILD
└─ #467 / PR #472  immutable source-claim compiler     TRUE_CHILD
          ↓ exact selected bytes
#468 / PR #473     CONVERGENCE
```

Shadow independently checks the #473 exact subject for:

```text
#469 worker-result + controller-readback identity and digest match
#470 canary ownership label + one-edge mutation + original-denominator cleanup
#471 stable lifecycle identity + monotonic timestamps + liveness + clean terminal
#472 immutable source identity/location + complete denominator + compatibility with problem-closure checker
#473 multi-parent selected-byte ancestry
10 total control-plane schemas and all 8 control-plane selftests executed unconditionally
Wave-3 Local Handoff Queue passes the existing semantic queue assertion
no live receipt is synthesized from a static fixture or hosted CI
```

Runtime evidence ceilings are non-substitutable:

```text
Codex carrier deterministic PASS            != signed-in Codex execution
GitHub canary deterministic PASS            != remote dependency mutation
Herdr lifecycle deterministic PASS          != live Herdr process observation
source compiler deterministic PASS          != source truth/applicability/verification
queue PASS                                  != runtime commands executed
#473 hosted PASS                            != Human Admit / merge / release
```

If any live receipt later appears, Shadow must bind it to the exact task/repo/commit/tree/session or fixture issue subjects named by that receipt and recompute closure. Historical #473 CI cannot be reused after the runtime subject changes.

## Relationship to task and Stack DAGs

The Shadow is normally an `EXTERNAL_EVIDENCE` lane. It owns no implementation paths and does not become a Git child merely because its receipt is required.

```text
Tech Lead implementation siblings / true children
        ↓ deterministic and local results
independent Shadow EXTERNAL_EVIDENCE
        ↓ same exact subject, separate evaluation path
one convergence owner
        ↓ Human Admit where required
```

Use `TRUE_CHILD` only when the Shadow implementation itself consumes unmerged parent bytes. Use `PROCESS_DEPENDENCY` when later admission waits for the Shadow receipt without changing branch ancestry. A multi-parent convergence commit may consume several SIBLING candidate heads while leaving those heads siblings of each other; ancestry alone is not admission.

Full closure vocabulary and current control-plane trace:

- [`../../docs/traceability/TECH_LEAD_SHADOW_CLOSURE.md`](../../docs/traceability/TECH_LEAD_SHADOW_CLOSURE.md)
- [`../../docs/traceability/CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md`](../../docs/traceability/CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md)
- [`../../docs/traceability/WAVE3_LIVE_EVIDENCE.md`](../../docs/traceability/WAVE3_LIVE_EVIDENCE.md)

## 100-point architecture assessment

The five source dimensions remain:

```text
control flow and state governance        25
tool boundary and idempotency            20
context budget and memory                20
fault tolerance, self-healing, and HITL  20
Evals and observability                  15
```

The checker derives points from source-derived positive controls and Vibe signals. A detected Vibe signal invalidates its mapped positive controls. Critical non-idempotent writes and model-owned high-risk authority cap the score at `59`.

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
Codex control-plane deterministic convergence         owned by #379 exact candidate subject
Wave-3 live-evidence deterministic convergence        owned by #468 exact candidate subject
independent same-subject live Shadow execution         NOT_EXERCISED
live Codex SDK / Herdr / GitHub dependency effects     NOT_EXERCISED unless exact receipts exist
real source/provider closure                           EVIDENCE_DEPENDENT
live external registry retrieval                       NOT_EXERCISED
live multimodal browser/device observation             NOT_EXERCISED
live Langfuse/OpenTelemetry production feedback        NOT_EXERCISED
cross-model causal uplift                              NOT_EXERCISED
actual sibling admission / abstraction promotion / merge / release  HUMAN_ADMIT_REQUIRED
```
