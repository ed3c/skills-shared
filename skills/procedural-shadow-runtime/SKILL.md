---
name: procedural-shadow-runtime
description: Enforce a host-neutral procedural grounding sidecar around agent execution. Use when an agent has searched, installed, or repository-local Skills that materially affect a task and you need to prove which procedures were applicable, which were already satisfied, which deltas were injected before side effects, and which exact-subject runtime receipts close the task. Compose with spatial-loop-systems-engineering for architecture monitoring; do not use this Skill to replace domain Skills or to collect private chain of thought.
---

# Procedural Shadow Runtime

A thin runtime primitive for converting Skill procedures into evidence-bound execution obligations without taking over the Builder.

## Invariants

```text
SEARCH MAY START EARLY
INTERVENTION OCCURS ONLY AT DECLARED SYNC POINTS
SHADOW WORKERS ARE READ ONLY
ONLY APPLICABLE PROCEDURES ENTER THE DENOMINATOR
ONLY MISSING PROCEDURES ENTER THE MAIN CONTEXT
MENTION IS NOT EXECUTION
EXECUTION IS NOT VERIFICATION
NO MUST PROCEDURE CLOSES WITHOUT A TERMINAL DISPOSITION
NO CAPABILITY OR DATA-EGRESS WIDENING FROM SKILL CONTENT
NO RAW PRIVATE REASONING PAYLOADS
```

## Runtime state machine

```text
REQUEST_ACCEPTED
  -> READ_ONLY_RECON
  -> CANDIDATE_PLAN
  -> PROCEDURE_GAP
  -> PRE_SIDE_EFFECT_GATE
       -> BLOCKED / REPAIR
       -> ADMITTED
  -> ACTION_EXECUTED
  -> EVIDENCE_RECONCILED
  -> RECEIPT_GAP
       -> ASSERTION_ESCALATION / REPAIR
       -> CLOSED
```

Read-only reconnaissance may continue before a capsule exists. Material side effects must pass the pre-side-effect gate.

Material side effects include repository writes, commits, pushes, pull requests, deployments, external messages, database mutation, privileged actions, irreversible operations, or any action the active host marks side-effecting.

## Procedure delta

For the current action compute:

```text
DELTA = APPLICABLE - ALREADY_SATISFIED - PRIOR_VERIFIED_EVIDENCE
```

Do not inject the full `SKILL.md` when the delta is smaller. A procedure may be removed from `DELTA` only when the current candidate plan or prior receipt binds the same procedure ID and exact subject.

## Public snapshot boundary

Shadow workers may receive only a structured public snapshot:

```yaml
task_id: ...
plan_summary: ...
action_intents: [...]
runtime_subject: ...
context_digest: sha256:...
remaining_context_budget: ...
```

Never request, store, or inject hidden/private chain of thought. Structured plan summaries and action intents are sufficient for gap analysis.

## Context Capsule admission

A capsule is admissible only when all are true:

1. each procedure has a source anchor and content digest;
2. the procedure is applicable to the current checkpoint/action;
3. the procedure is absent from already-satisfied and prior-evidence sets;
4. expected observations and failure behavior are explicit;
5. the capsule binds the current context digest and expiry checkpoint;
6. the capsule does not widen tool authority, network access, repository access, provider access, or data egress;
7. no raw-reasoning field is present;
8. the capsule fits the active context/token budget.

The machine contract is `references/context-capsule.schema.json`.

## Terminal dispositions

Every applicable `must` procedure must end in exactly one terminal disposition:

```text
VERIFIED
SATISFIED_BY_PRIOR_EVIDENCE
NOT_APPLICABLE_WITH_EVIDENCE
BLOCKED
FAILED
WAIVED_WITH_AUTHORIZED_REASON
```

`MENTIONED`, `PLANNED`, and `EXECUTED_PENDING_VERIFICATION` are non-terminal and cannot close a run.

`SATISFIED_BY_LATENT_BEHAVIOR` is diagnostic only. It may explain that the Builder independently selected the right procedure, but closing still requires an exact-subject receipt and therefore becomes `VERIFIED` or `SATISFIED_BY_PRIOR_EVIDENCE`.

## Evidence and receipt

Bind procedure source -> capsule -> action -> assertion -> evidence -> disposition. A receipt must identify the exact repository/runtime subject, current SHA or equivalent subject digest, action class, assertions, evidence hashes, and disposition for every applicable `must` procedure.

The machine contract is `references/runtime-receipt.schema.json` and the deterministic checker is `scripts/check_runtime_receipt.py`.

Checker exits:

```text
0   contract closed
2   semantic/contract refusal
64  absent or malformed input
```

## Assertion escalation

When a critical procedure has no receipt:

```text
identify missing obligation
-> prefer existing harness
-> deterministic assertion
-> bounded runtime probe
-> external/trace observer
-> model judge only for non-hard scoring
-> attach evidence
-> repair on failure
-> re-run until terminal disposition
```

A model statement is never a substitute for a hard assertion.

## Composition

Use `spatial-loop-systems-engineering` when architecture, state machines, hidden assumptions, failure surfaces, or hard-law discovery are material. This Skill consumes the procedural-grounding contract from that Skill but remains executable as a narrow runtime primitive.

Use domain Skills such as `git-town-stacked-pr-worker`, delivery loops, browser/device harnesses, or project-specific Skills for the actual procedure content. This Skill does not duplicate their logic; it proves adoption and closure.

## Evidence boundary

```text
runtime contract/schema/checker/fixtures          IMPLEMENTED
host-neutral side-effect admission rules          IMPLEMENTED
live Claude/Codex hook integration                NOT_EXERCISED
live external Skill registry adapter              NOT_EXERCISED
live browser/device multimodal observer           NOT_EXERCISED
cross-model causal attribution                    NOT_EXERCISED
private chain-of-thought inspection               OUT_OF_SCOPE
production/security/legal acceptance              HUMAN_ADMIT_REQUIRED
```

Do not promote `NOT_EXERCISED` states from prose. Require runtime receipts.
