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
independent same-subject live Shadow execution         NOT_EXERCISED
live Codex SDK / Herdr / GitHub dependency effects     NOT_EXERCISED unless exact receipts exist
real source/provider closure                           EVIDENCE_DEPENDENT
live external registry retrieval                       NOT_EXERCISED
live multimodal browser/device observation             NOT_EXERCISED
live Langfuse/OpenTelemetry production feedback        NOT_EXERCISED
cross-model causal uplift                              NOT_EXERCISED
actual sibling admission / abstraction promotion / merge / release  HUMAN_ADMIT_REQUIRED
```

## Wave 3 live-evidence Shadow monitor — #464–#468

Canonical trace: [`../../docs/traceability/WAVE3_LIVE_EVIDENCE.md`](../../docs/traceability/WAVE3_LIVE_EVIDENCE.md).

Wave 3 adds carriers that contain words such as `live`, `EXERCISED`, or `PASS`. Shadow must treat those as **data vocabulary**, not evidence promotion. The current review graph is:

```text
#455 static/deterministic parent
├─ #464/#469 Codex live acceptance carrier       TRUE_CHILD / SIBLING
├─ #465/#470 GitHub DAG reversible canary        TRUE_CHILD / SIBLING
├─ #466/#471 Herdr lifecycle carrier             TRUE_CHILD / SIBLING
└─ #467/#472 source-claim compiler               TRUE_CHILD / SIBLING
        ↓ exact consumed leaf bytes
#468/#473 convergence
        ↓
Shadow same-subject review
```

Shadow must independently verify at least:

```text
#464
  worker result really binds sdk_execution=EXERCISED
  exact task/attempt/repo/base/tree and changed-file denominator agree
  lease readback is PASS
  controller source/diff/test readback and command digests are present
  output is still SHADOW_PENDING, not final acceptance
  no prompt/model prose/reasoning/auth/token/credential durability

#465
  both canary issues are explicitly owned and OPEN
  original blockedBy denominator matches the plan
  exactly one owned edge is added and exact-read back
  cleanup removes only that edge and restores the original denominator
  any unexpected drift or cleanup error is rejection, never partial PASS

#466
  all samples bind one task/attempt/repo/Git/worktree/target identity
  pane/workspace/PID-start/native-session identity does not drift
  timestamps do not regress
  nonterminal samples have a live process
  terminal state is clean with zero residue and no later sample exists
  UNAVAILABLE_FALLBACK is not live evidence

#467
  complete problem/source denominator is preserved
  GitHub issue identity is exact; external docs are immutable sha256 identities
  exact locator + claim digest + manifest digest are present
  output validates through the existing #378 closure checker
  no verification/receipt/merge evidence is invented
```

#468 close gate additionally requires:

```text
four exact leaf heads are consumed by the multi-parent integration
leaf relation is TRUE_CHILD of #455 and SIBLING among #464–#467
shared run-all executes Wave 2 + Wave 3 tests without conditional skip
10 schemas are Draft-2020-12 valid
source example compiles into the existing closure model
Wave-3 Local Handoff Queue validates and stays bound to immutable integration subject
README/AGENTS/Shadow/Git Town/traceability routes agree
hosted Skill Suites + Shared Skills Infra + Skill Eval Contract + Git Town gates are exact-head green
```

The only permissible static Wave-3 Shadow conclusion before real runtime receipts is a scoped infrastructure verdict such as `STATIC_LIVE_EVIDENCE_INFRASTRUCTURE_READY_FOR_RUNTIME_HANDOFF`. It must simultaneously retain:

```text
live Codex SDK/controller acceptance       NOT_EXERCISED
live GitHub add/readback/remove canary      NOT_EXERCISED
live Herdr lifecycle                       NOT_EXERCISED
article/PDF/PRD truth                      SOURCE_PROPOSAL / EVIDENCE_DEPENDENT
real source/provider closure               EVIDENCE_DEPENDENT
Human Admit / merge / release              HUMAN_ADMIT_REQUIRED / NOT_PERFORMED
```

A deterministic fixture containing `sdk_execution=EXERCISED`, a canary function returning `PASS`, or a lifecycle fixture returning `DONE_CANDIDATE` cannot raise those lanes. Only exact external/runtime receipts plus the required independent readback can do so.
