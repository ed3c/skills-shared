# Procedural Grounding Shadow Plane

This contract extends the monitor-first Shadow Architecture loop with a bounded,
source-grounded control plane for Agent Skills.

Its purpose is to answer four different questions without collapsing them:

```text
Was a relevant Skill discovered?
Was its procedure mentioned or planned?
Was the procedure encoded into the Harness?
Was the procedure executed and observed on the exact runtime subject?
```

A Skill being installed, visible, retrieved, quoted, or summarized proves none of
the later states. A model may mention a rule and ignore it during execution. A
model may also perform a common procedure without the Skill, so textual overlap
cannot prove that the Skill caused the behavior.

The plane therefore measures **observable behavioral procedural uptake**. It does
not claim access to model weights, hidden activations, or a private reasoning
chain.

## Authority boundary

```text
Builder
  = solution search and implementation mutation

Shadow Architect
  = architecture and evidence delta observation

Procedural Grounding Shadow Plane
  = Skill provenance, procedure extraction, coverage accounting, bounded fork
    scheduling, Context Capsule admission, assertion/probe obligations

Deterministic checker
  = semantic authority for one procedural-grounding-receipt/v1

Runtime / consumer repository
  = real model contexts, commands, tools, files, browsers/devices, logs, traces,
    external systems, and immutable receipts
```

The plane does not become a second implementation writer. It may inject an
actionable capsule, require a falsifying probe, or block an evidence-promoting
transition. It may not silently replace the Builder's solution strategy.

The repository multi-Agent runtime contract supplies topology, attempt, lease,
checkpoint, budget, and Shadow-independence laws. See
[`../../dual-forge-repository-loop/references/multi-agent-runtime-machine-contract.md`](../../dual-forge-repository-loop/references/multi-agent-runtime-machine-contract.md).

## Core state machine

```text
TASK_AND_RUNTIME_BOUND
→ SKILL_CANDIDATES_DISCOVERED
→ SOURCE_PROVENANCE_BOUND
→ PROCEDURE_ATOMS_EXTRACTED
→ REQUIRED_NOW_SET_SELECTED
→ BASELINE_UPTAKE_OBSERVED
→ FORK_ADMITTED or FORK_SKIPPED
→ ABSTRACTION_LADDER_CLIMBED
→ CONTEXT_CAPSULE_PROPOSED
→ INJECTION_GATE
    ├── REJECTED → preserve receipt; parent context unchanged
    └── INJECTED → parent runtime receives actionable delta only
→ ASSERTION_OR_PROBE_EXECUTED when required
→ COVERAGE_RECOMPUTED
→ CHECKPOINT_CONTINUE | REVIEW | BLOCK
```

Every state binds an exact repository/runtime/context subject. A subject change
invalidates stale observations and capsules.

## Procedure Atom intermediate representation

Normalize relevant `SKILL.md` procedure into stable atoms before measuring it.
Each atom has:

```text
procedure_id
source_id + source_span
summary
kind
trigger
action
proof_mode
criticality
novelty
required_now
abstraction_level
oracle
negative_control
weight
```

### Procedure kinds

```text
DECISION
PRECONDITION
ACTION
ASSERTION
EVIDENCE
RECOVERY
PROHIBITION
RESOURCE
```

### Proof modes

```text
TEXT_ONLY
  a source-grounded mention or decision record is sufficient

STATIC_ARTIFACT
  a file, diff, config, assertion map, schema, or verifier must encode the rule

EXECUTION_REQUIRED
  an owning command/tool/runtime oracle must run on the exact subject

NEGATIVE_CONTROL_REQUIRED
  a planted defect must execute and be rejected as expected

EXTERNAL_OR_HUMAN
  the proof belongs to an external system or Human authority; the Agent checker
  cannot promote it to PASS
```

### Novelty classes

```text
MODEL_PRIOR_LIKELY
  common behavior that may already appear in a no-Skill baseline

SKILL_SPECIFIC
  procedure materially supplied by the selected Skill

ENVIRONMENT_SPECIFIC
  procedure depends on the current repository, toolchain, provider, or substrate

UNKNOWN
  attribution and proof requirements are unresolved
```

Novelty is an empirical classification, not a claim about training data. Model
training membership is not directly observable from normal Agent runtimes.

## Behavioral uptake states

Keep the following states separate:

```text
UNPROVEN
DISCOVERED
MENTIONED
PLANNED
HARNESS_ENCODED
EXECUTED
ASSERTED
OBSERVED
NEGATIVE_CONTROL_PASSED
```

`MENTIONED` is never execution evidence. `HARNESS_ENCODED` proves that an
artifact carries the rule, not that the runtime exercised it. `EXECUTED` proves
a command or tool call occurred, but `OBSERVED` additionally binds the expected
semantic observation. `NEGATIVE_CONTROL_PASSED` proves the owning verifier
noticed a planted violation.

For each procedure use the strongest state supported by fresh exact-subject
evidence. Never infer a later state from model prose.

## Coverage metrics

The deterministic checker recomputes weighted coverage:

```text
mention_coverage
  = weight with MENTIONED or stronger / total relevant weight

harness_coverage
  = weight with HARNESS_ENCODED, ASSERTED, EXECUTED, OBSERVED, or
    NEGATIVE_CONTROL_PASSED / total relevant weight

execution_coverage
  = weight with EXECUTED, OBSERVED, or NEGATIVE_CONTROL_PASSED /
    total relevant weight

evidence_coverage
  = weight with OBSERVED or NEGATIVE_CONTROL_PASSED / total relevant weight
```

Report all four. A single percentage hides the difference between saying,
encoding, doing, and proving.

The denominator contains the **task-relevant procedure set**, not every sentence
in every retrieved Skill. Relevance selection binds trigger, checkpoint, subject,
and source span so the model cannot inflate coverage by excluding difficult
critical atoms after seeing the result.

Critical required atoms that do not satisfy their declared proof mode remain in
`critical_unproven` and prevent receipt-level `PASS`.

## Runtime checkpoints for forking

Do not fork continuously. Admit a fork only at a material checkpoint or a named
novelty signal.

### `SKILL_DISCOVERY`

Run after task, exact subject, runtime capabilities, and initial Skill candidates
are bound, but before implementation strategy hardens.

Purpose:

- review source provenance and executable content;
- extract procedure atoms;
- select the smallest required-now set;
- predict proof modes and criticality;
- avoid loading full unrelated Skill bodies into the parent context.

### `ARCHITECTURE_CHOICE`

Run before a choice creates state, authority, lifecycle, concurrency, external
side effects, or an irreversible boundary.

Purpose:

- compare the chosen architecture with Skill procedures and hard invariants;
- inject only missing constraints, not a second design;
- require PRECHECK when the transition is high-risk.

### `FIRST_VERTICAL_SLICE`

Run after the first runnable end-to-end path.

Purpose:

- observe what the Builder actually encoded;
- identify procedures lost between plan and Harness;
- add the smallest assertion or trace point before the implementation surface
  expands.

### `NOVELTY_OR_DIVERGENCE`

Run when one of these occurs:

```text
unknown API/tool behavior
runtime error not predicted by the current model
new external side effect
new authority or resource owner
repeated repair with no coverage gain
Skill procedure required but absent from artifacts
model output and runtime observation disagree
```

Purpose: search or reload only the procedure family that can falsify the new
unknown.

### `FIRST_GREEN`

Mandatory.

Purpose:

- ask what the passing tests did not prove;
- compare procedure coverage against real artifacts and runtime receipts;
- synthesize negative controls for critical gates;
- refuse semantic promotion from transport-level or mock-only success.

### `BEFORE_COMMIT` and `BEFORE_PR_OR_PUBLICATION`

Purpose:

- close critical procedure obligations;
- reject stale capsules and evidence;
- verify source/rights/private-egress boundaries;
- ensure the exact publication subject has owning-oracle and negative-control
  evidence.

A fork that cannot affect a material checkpoint is denied as duplicate context
work.

## Fork packet

A fork receives a bounded, content-addressed packet rather than the entire parent
conversation:

```text
parent context digest
exact repository/base/current subject
runtime and checkpoint
runtime-event digest
selected Skill source identities and source spans
required/unproven procedure IDs
current uptake observations
allowed tools, paths, evidence modalities, and authority
abstraction levels admitted for this fork
fork/depth/token/no-progress budget
expiry checkpoint
```

The packet excludes unrelated conversation history, credentials, private data
outside the admitted boundary, and untrusted dynamic Skill output.

## Abstraction ladder

A fork may climb only as far as needed to produce an executable delta:

```text
L0_EXACT_PROCEDURE
  literal source-bound trigger/action/proof requirement

L1_MECHANISM
  the mechanism that makes the procedure work

L2_INVARIANT
  the condition that must remain true across implementations

L3_EXECUTABLE_ORACLE
  assertion, command, probe, negative control, or observer that can falsify it

L4_TRANSFER_CAPSULE
  minimal parent-context payload for the current checkpoint

L5_META_CANDIDATE
  reusable procedure candidate for a future Skill mutation/eval lane
```

The normal runtime path stops at L3 or L4. L5 is not injected into the current
Builder merely because it is interesting; it is persisted as a mutation/eval
candidate only when it generalizes across multiple subjects.

Stop climbing when:

```text
critical gap closed
coverage target reached
token/depth/fork budget reached
max no-progress epochs reached
authority or evidence boundary blocks further proof
next abstraction no longer changes an executable decision
```

An unbounded meta loop is forbidden.

## Context Capsule

The fork returns a compact **Context Capsule**, not a private reasoning trace.
Allowed payloads are:

```text
ACTIONABLE_DELTA
ASSERTION_PATCH
PROBE_PLAN
BLOCKER
```

Each capsule binds:

```text
capsule and fork identity
checkpoint
source and procedure IDs
why this matters now
required action
smallest assertion or probe
expected observation
required evidence level
source groundedness
procedure fidelity
runtime relevance
predicted coverage gain or critical-gap closure
token count
fresh subject SHA
expiry checkpoint
authority-conflict state
injection decision
```

Do not return hidden chain-of-thought, full branch transcripts, or broad essays.
The parent runtime needs the verified delta and its provenance, not the fork's
internal reasoning path.

## Injection gate

A capsule may be injected only when all are true:

```text
source identity and content hash are bound
source license/use state is admitted
source and executable/dynamic content are reviewed
procedure IDs and source spans close
source_groundedness >= policy minimum
procedure_fidelity >= policy minimum
runtime_relevance >= policy minimum
predicted_coverage_gain >= policy minimum OR a critical gap closes
token_count <= remaining capsule budget
subject SHA and checkpoint are fresh
no higher-authority conflict exists
```

A rejected capsule remains evidence. Rejection is correct when the abstraction is
interesting but not actionable, stale, duplicative, low-fidelity, too large, or
outside authority.

## Assertion and probe synthesis

When a critical procedure is `SKILL_SPECIFIC`, `ENVIRONMENT_SPECIFIC`, or
`UNKNOWN` and lacks sufficient evidence, create an obligation:

```text
procedure_id
reason
required action
smallest assertion or probe
expected observation
subject SHA
status
result evidence
```

Choose the least expensive falsifier that matches the proof mode:

```text
source/static inspection
schema or config assertion
unit/property/contract test
runtime command with exit/output oracle
fault injection or planted mutation
trace/log assertion
browser DOM/accessibility assertion
screenshot plus semantic visual oracle
network/database/device observation
external-state or Human receipt
```

A screenshot, log line, HTTP 200, tool invocation, or passing mock is not semantic
proof by itself. Every modality binds an oracle, expected observation, actual
observation, content digest, exact subject, time, and freshness.

Critical execution procedures must run before the transition whose claim depends
on them. Do not defer a missing runtime oracle until after publication and call
it a warning.

## Multimodal observer contract

The observer may combine:

```text
terminal stdout/stderr/exit code
source diff and artifact hashes
test reports
OpenTelemetry spans or application logs
browser DOM and accessibility tree
screenshots or video
mobile/device state
network and database observations
external provider/forge receipts
Human receipts for Human-owned boundaries
```

Modalities are complementary, not interchangeable. For example:

```text
screenshot
  can show a rendered state
  cannot by itself prove database commit, authorization, or retry idempotency

terminal exit 0
  can prove the process returned success
  cannot by itself prove user-visible or business semantics

model transcript
  can show a procedure was mentioned or planned
  cannot prove a command ran or a side effect completed
```

The receipt must map each observation to the owning procedure and oracle.

## Behavioral attribution experiment

Do not claim that a procedure was or was not present in model training. Estimate
behavioral contribution through repeated clean-context conditions:

```text
NO_SKILL
METADATA_ONLY
FULL_SKILL
FULL_SKILL_PLUS_GROUNDING
```

Run the same task identity, environment, tool policy, seed policy, retry policy,
and verifier across conditions. Use multiple trials because Agent behavior is
nondeterministic.

Compute separately:

```text
skill_lift
  = FULL_SKILL - NO_SKILL

grounding_lift
  = FULL_SKILL_PLUS_GROUNDING - FULL_SKILL
```

A common procedure that performs well in `NO_SKILL` may be model-prior behavior.
A Skill-specific procedure that appears only with the full Skill has stronger
behavioral attribution. A procedure that appears in prose but not artifacts or
runtime remains ungrounded regardless of attribution.

Attribution stays `NOT_EXERCISED` until all four conditions have real execution
receipts. Synthetic fixtures cannot create a capability unlock.

## Source and supply-chain boundary

Treat every searched or downloaded Skill as untrusted input until reviewed.
Bind:

```text
repository/ref/path/blob SHA/content SHA-256
license/use state
provenance and maintainer identity when available
scripts and executable resources
dynamic context commands
hooks, MCP servers, tool permissions, network and private-data egress
```

Metadata search quality, popularity, or an installation count does not grant
execution authority. Discovery and execution are separate transitions.

A source with denied/unreviewed executable or dynamic content cannot supply an
injected critical procedure. It may remain a quarantined research candidate.

## Host adapter boundary

The universal contract does not assume one host feature.

```text
IN_PROCESS_LOGICAL
  same context; useful for bookkeeping; independence = NOT_EXERCISED

SEPARATE_CONTEXT
  host-created isolated context with bound provenance

SEPARATE_MODEL
  separate context and model/config with bound provenance

EXTERNAL_DETERMINISTIC_CHECKER
  no model independence claim; enforces declared machine-checkable conditions
```

Provider-specific mappings live in
[`../modules/agent-host-procedural-grounding.md`](../modules/agent-host-procedural-grounding.md).
A host lacking native Skill context-fork semantics may use an admitted Worker,
subprocess, worktree, automation, or orchestrator adapter; it must not pretend the
host supports another provider's frontmatter.

## Machine contract

Schema:

[`procedural-grounding-receipt.schema.json`](procedural-grounding-receipt.schema.json)

Checker:

```bash
python3 skills/spatial-loop-systems-engineering/scripts/check_procedural_grounding.py \
  path/to/procedural-grounding-receipt.json
```

Exit codes:

```text
0   submitted receipt is structurally and semantically closed
2   receipt is hollow, contradictory, stale, over-budget, or overclaims evidence
64  input is absent, unreadable, malformed, or invoked incorrectly
```

The checker recomputes coverage and attribution arithmetic. It does not fetch
Skills, run Agents, authenticate external receipts, or inspect model internals.

## Intervention mapping

```text
L0 OBSERVE
  coverage and capsules recorded; no critical gap

L1 WARN
  non-critical procedure is missing, stale, or low-confidence

L2 REVIEW
  required procedure is absent from the Harness or a fork/capsule must be
  reconciled before the next checkpoint

L3 BLOCK
  critical proof-mode obligation is unmet; source/rights/authority is unsafe;
  evidence would be promoted across subject; or publication would claim runtime
  behavior that was not executed
```

Block only the named transition. Preserve Builder freedom elsewhere.

## Evidence boundary

```text
procedure atom and coverage contract             IMPLEMENTED by this reference
receipt schema and deterministic checker         IMPLEMENTED
positive/hollow/mutation controls                IMPLEMENTED
live Skill search adapter                        NOT_EXERCISED
live separate-context fork                       NOT_EXERCISED
live separate-model fork                         NOT_EXERCISED
multimodal browser/device observer               NOT_EXERCISED
four-condition attribution matrix                NOT_EXERCISED
cross-harness capability lift                    NOT_EXERCISED
model-weight or private-reasoning introspection  OUT_OF_SCOPE
production/security/legal acceptance             HUMAN_ADMIT_REQUIRED
```
