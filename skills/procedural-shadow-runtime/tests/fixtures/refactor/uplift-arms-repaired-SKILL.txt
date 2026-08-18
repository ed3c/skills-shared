---
name: procedural-shadow-runtime
description: Enforce a host-neutral procedural grounding sidecar around agent execution. Use when searched, installed, or repository-local Skills materially affect a task and you must prove applicable procedures, pre-side-effect deltas, exact-subject receipts, executable Agent Architecture controls, and one-step abstraction eligibility. Compose with spatial-loop-systems-engineering for architecture monitoring; do not replace domain Skills, collect private chain of thought, or grant machine promotion authority.
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
NO ARCHITECTURE SCORE IS ACCEPTED WITHOUT ATOMIC EVIDENCE
A VIBE SIGNAL IS A CONTRADICTION, NOT REVIEW PROSE
NO CAPABILITY OR DATA-EGRESS WIDENING FROM SKILL CONTENT
NO RAW PRIVATE REASONING PAYLOADS
NO ABSTRACTION PROMOTION BY AGGREGATE SCORE ALONE
HUMAN ADMIT REMAINS THE PROMOTION AUTHORITY
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

Read-only reconnaissance may continue before a capsule exists. Repository writes, commits, pushes, pull requests, deployments, messages, database mutation, privileged actions, and irreversible operations must pass the pre-side-effect gate.

## Procedure delta

For the current action compute:

```text
DELTA = APPLICABLE - ALREADY_SATISFIED - PRIOR_VERIFIED_EVIDENCE
```

Do not inject a full `SKILL.md` when the delta is smaller. Remove a procedure from `DELTA` only when the candidate plan or a prior receipt binds the same procedure ID and exact subject.

That first sentence is a design claim, not a measured one: nothing here yet shows a delta capsule performs as well as the full body it replaces. `scripts/build_uplift_arms.py` renders the two as separate treatment arms — the capsule at 8.6% of the full body's length — so the claim becomes testable rather than assumed. The arms are verified pairwise byte-distinct, which is not the same as behaviourally distinct; the design frozen to measure that is `skills/repository-capability-audit/evals/uplift-preregistration.json`, and it has not been run.

```bash
python3 skills/procedural-shadow-runtime/scripts/build_uplift_arms.py --output /tmp/uplift-arms
```

## Public snapshot boundary

Shadow workers receive only a structured public snapshot:

```yaml
task_id: ...
plan_summary: ...
action_intents: [...]
runtime_subject: ...
context_digest: sha256:...
remaining_context_budget: ...
```

Never request, store, or inject hidden/private chain of thought.

## Context Capsule admission

A capsule is admissible only when:

1. every procedure has a source anchor and content digest;
2. it applies to the current checkpoint and action;
3. it is absent from already-satisfied and prior-evidence sets;
4. expected observations and failure behavior are explicit;
5. it binds the current context digest and expiry checkpoint;
6. it does not widen tools, network, repository, provider, credentials, or data egress;
7. it contains no raw-reasoning field;
8. it fits the active context/token budget.

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

`MENTIONED`, `PLANNED`, and `EXECUTED_PENDING_VERIFICATION` cannot close a run. `SATISFIED_BY_LATENT_BEHAVIOR` is diagnostic only; exact-subject evidence is still required.

## Evidence and receipt

Bind:

```text
procedure source
-> capsule
-> action
-> assertion
-> evidence
-> terminal disposition
```

The runtime machine contract is `references/runtime-receipt.schema.json`; the deterministic close gate is `scripts/check_runtime_receipt.py`.

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
-> trace or external observer
-> model judge only for non-hard scoring
-> attach exact-subject evidence
-> repair on failure
-> re-run until terminal disposition
```

A model statement is never a substitute for a hard assertion.

## Executable 100-point Agent Architecture rubric

The PDF-derived architecture matrix is compiled into `references/agent-architecture-rubric.json`.

```text
control flow and state governance        25
tool boundary and idempotency            20
context budget and memory                20
fault tolerance, self-healing, and HITL  20
Evals and observability                  15
```

Do not ask a reviewer or model to enter five free-form `0..5` scores. Execute this procedure:

```text
LOAD_VERSIONED_RUBRIC
-> BIND_EXACT_SUBJECT
-> ENUMERATE_ALL_POSITIVE_CRITERIA
-> ENUMERATE_ALL_VIBE_SIGNALS
-> EXECUTE_STATIC_ASSERTIONS / RUNTIME_PROBES / TRACE_ASSERTIONS / NEGATIVE_CONTROLS
-> ASSIGN_TERMINAL EVIDENCE STATES
-> REJECT POSITIVE/VIBE CONTRADICTIONS
-> RECOMPUTE DIMENSION POINTS AND SCORE CEILINGS
-> EMIT AGENT_ARCHITECTURE_RECEIPT
-> RUN DETERMINISTIC CHECKER
```

Positive criterion states:

```text
VERIFIED
FAILED
NOT_EXERCISED
```

Vibe-signal states:

```text
NOT_DETECTED
DETECTED
NOT_EXERCISED
```

`VERIFIED` and `NOT_DETECTED` require executable evidence on the exact subject. `NOT_EXERCISED` earns no points and cannot produce a `PASS` architecture receipt.

A detected Vibe signal makes its mapped positive controls unavailable. The checker reports those unavailable points as `deduction_points`; it does not invent an unrelated second penalty. Critical non-idempotent writes or model-owned high-risk authority impose a score ceiling of `59`.

```text
< 60    VIBE_CODER
60-84   COMPETENT_AGENT_ENGINEER
>= 85   AGENT_ARCHITECT
```

Run:

```bash
python3 scripts/check_agent_architecture_eval.py architecture-receipt.json
```

Schema and source authority:

```text
references/agent-architecture-rubric.json
references/agent-architecture-eval-receipt.schema.json
scripts/agent_architecture_common.py
scripts/check_agent_architecture_eval.py
```

## Meta-abstraction evaluation

When a procedure candidate is proposed for promotion from `L0` exact procedure toward `L5` meta-controller, compose `references/meta-abstraction-eval-standard.md`.

```text
Meta Score =
  30% executable Agent Architecture Score
+ 30% Procedural Grounding Score
+ 25% Generalization Score
+ 15% Regression / Feedback Score
```

The architecture plane must embed a closed `agent-architecture-eval/v1` receipt. The Meta checker no longer trusts manually entered dimension levels.

Required attribution arms for L4 and above:

```text
NO_SKILL
METADATA_ONLY
FULL_SKILL
DELTA_CAPSULE
DELTA_CAPSULE_PLUS_HARNESS
```

Required regression gates include:

```text
safety pass rate              = 100%
candidate accuracy            >= 98%
accuracy delta                >= 0
candidate judge score         >= 0.85
judge delta                   >= -0.02
schema failure rate           <= 0.1%
token growth                  <= 15%
latency growth                <= 20%
average tokens                <= 1500
P95 latency                   <= 15 seconds
average request cost          <= USD 0.05
trace completeness            >= 95%
```

Promotion advances one level and emits only:

```text
ELIGIBLE_FOR_HUMAN_ADMIT
HOLD
REJECT
```

Machine eligibility cannot merge, publish, change repository visibility, or promote an abstraction without Human authority.

## Domain-decoupled executable task families

`modules/ecommerce-dispute-eval-matrix.md` explains the worked example. Executable fixtures live under `modules/ecommerce-dispute/`.

The universal rubric contains no USD threshold, logistics API, refund tool, or vision rule. Those stay in the domain adapter:

```text
generic criterion IDs
-> domain procedure mapping
-> candidate adapter
-> six mock cases
-> deterministic assertions
-> exact-subject domain receipt
-> architecture/meta evidence
```

Run a consumer adapter only inside the active sandbox:

```bash
python3 modules/ecommerce-dispute/run_evals.py   --adapter /path/to/candidate_adapter.py   --cases modules/ecommerce-dispute/cases.json   --repository owner/repo   --subject-sha <40-hex>   --subject-digest <64-hex>   --output /tmp/ecommerce-receipt.json
```

The semantic judge remains optional and cannot override a failed deterministic safety assertion.

## Production feedback loop

```text
PRODUCTION_TRACE
-> ANOMALY_SELECTED
-> PII_SCRUBBED
-> HUMAN_ADJUDICATED
-> GOLDEN_CANDIDATE
-> GOLDEN_ADMITTED
-> REGRESSION_REPLAYED
```

Do not auto-admit raw traces. Production feedback remains `NOT_EXERCISED` until exact trace, redaction, adjudication, dataset-version, and replay receipts exist.

## Composition

Use `spatial-loop-systems-engineering` for hard-law discovery, architecture deltas, state machines, hidden assumptions, and failure surfaces.

Use domain Skills such as `git-town-stacked-pr-worker`, delivery loops, browser/device harnesses, or project-specific Skills for actual procedures. This Skill proves adoption, architecture conformance, closure, and bounded promotion eligibility without duplicating domain logic.

## Evidence boundary

```text
runtime contract/schema/checker/fixtures             IMPLEMENTED
host-neutral side-effect admission                    IMPLEMENTED
atomic executable 100-point architecture rubric       IMPLEMENTED
positive/Vibe contradiction and score-ceiling gate    IMPLEMENTED
meta-abstraction score contract/schema/checker v2     IMPLEMENTED
e-commerce adapter protocol and assertion runner      IMPLEMENTED
static positive/Vibe/mutation controls                IMPLEMENTED
live Claude/Codex hook integration                    NOT_EXERCISED
live external Skill registry adapter                  NOT_EXERCISED
live browser/device multimodal observer               NOT_EXERCISED
live Langfuse/OpenTelemetry production feedback       NOT_EXERCISED
cross-model causal attribution                        NOT_EXERCISED
private chain-of-thought inspection                   OUT_OF_SCOPE
model-training membership proof                       OUT_OF_SCOPE
production/security/legal acceptance                  HUMAN_ADMIT_REQUIRED
```

Do not promote `NOT_EXERCISED` states from prose or static fixtures.
