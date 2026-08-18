# Local/cloud offload: the portable method

One local agent and one always-on remote agent working the same piece of work is
two execution lanes and two evidence lanes with exactly one place where they are
allowed to meet: a frozen handoff. This document is the method that decides what
must be true before that handoff exists, who may close every state after it, and
which of those laws is executable in this repository today.

Machine authority: [`method-contract.v1.schema.json`](method-contract.v1.schema.json),
[`handoff-requirements.v1.schema.json`](handoff-requirements.v1.schema.json) and
[`../../tests/dual-agent-offload-contract/verify.py`](../../tests/dual-agent-offload-contract/verify.py).
This file states the laws in the reviewer's vocabulary and explains why those
shapes exist. It is not a second verifier: where prose and checker disagree, the
checker wins and the prose is the defect.

Inherited law: `CORE-LAW-009` (start-readiness and completion-readiness are two
edge classes) and `CORE-LAW-010` (closure lanes do not substitute) in
[`../../SKILL.md`](../../SKILL.md). This method applies them to a remote lane; it
does not restate or weaken them.

Source state: the architecture generalized here is a `SOURCE_PROPOSAL`. Nothing
in this directory has been executed against a transport, a scheduler, a provider,
an artifact store or an external effect.

## Two planes, one owner per interface

| Plane | Repository | Owns |
|---|---|---|
| Instruction / Method Plane | this repository | the vocabulary, this state machine, the authority map, the evidence and idempotency laws, the *logical* runtime contract IDs, and the exact-subject handoff packet |
| Runtime Contract Plane | `runtime-env` | the exact secret-free wire shapes of the five runtime contracts, their transport, their scheduler and their receipts |

Five logical contracts are declared here and defined there:

```text
runtime-env/dual-agent/offload-job/v1
runtime-env/dual-agent/capability-grant/v1
runtime-env/dual-agent/effect-intent/v1
runtime-env/dual-agent/artifact-manifest/v1
runtime-env/dual-agent/execution-receipt/v1
```

The boundary is a single sentence and it is the reason this method exists: **the
same `$id` or wire shape must never exist in both repositories.** A method
contract may *require* a runtime contract ID and pin its digest. It may not
define its fields, and it may not claim the runtime contract is implemented or
live. Two repositories defining one interface does not risk drift; it guarantees
it, because each side's tests stay green while the shapes separate.

`verify.py` enforces this in two independent places, which is deliberate — a
document-level check alone would stay green while a new wire schema file
appeared beside it:

- every declared contract must name `RUNTIME_CONTRACT_PLANE` as its owner (`M01`);
- no JSON file in this directory may claim one of those five names as its own
  `$id` or `schema_version` (`M01`, enforced by globbing the directory);
- a contract declared `IMPLEMENTED` must carry a real content digest (`M16`).

Until `runtime-env` publishes a shape and a digest, every runtime contract here
stays `NOT_IMPLEMENTED` and any handoff bound to them has verdict
`BLOCKED_BY_RUNTIME_CONTRACT`. That verdict is the correct output, not a failure.

## The offload state machine

```text
LOCAL_INTENT_BOUND
→ DATA_CLASSIFIED
→ AUTHORITY_AND_EFFECTS_DECLARED
→ REQUIRED_RUNTIME_CONTRACTS_DECLARED
→ OFFLOAD_HANDOFF_FROZEN          ← the frozen portable contract ends here
→ RUNTIME_BINDING_RESOLVED
→ DELIVERY_ATTEMPTED
→ REMOTE_EXECUTION_OBSERVED
→ RESULT_AND_ARTIFACTS_VERIFIED
→ LOCAL_RECONCILIATION
→ HUMAN_ADMIT | COMPLETE | RETRY | COMPENSATE | CANCEL
```

| State | Closed by | Closed when | State here today |
|---|---|---|---|
| `LOCAL_INTENT_BOUND` | local agent | exact repository/data subject, objective, deadline, budget and retry quota are frozen against an immutable subject | portable |
| `DATA_CLASSIFIED` | local agent | every input carries `PUBLIC`, `INTERNAL`, `CONFIDENTIAL` or `LOCAL_ONLY` | portable |
| `AUTHORITY_AND_EFFECTS_DECLARED` | local agent | side-effect class, approval requirement, Human-owned operations, idempotency and effect-ledger requirements, and the network/filesystem/secret-handle allowlist are declared | portable |
| `REQUIRED_RUNTIME_CONTRACTS_DECLARED` | local agent | the five contract IDs are named with their owner plane and implementation state | portable |
| `OFFLOAD_HANDOFF_FROZEN` | local agent | one exact subject is bound to one frozen method contract, with start and completion dependencies in separate sets | portable |
| `RUNTIME_BINDING_RESOLVED` | runtime plane | runtime, profile, policy, tool, image and Skill identities resolve to immutable digests | `NOT_IMPLEMENTED` |
| `DELIVERY_ATTEMPTED` | transport | the job was handed to a transport — nothing more | `NOT_IMPLEMENTED` |
| `REMOTE_EXECUTION_OBSERVED` | remote lane | an execution receipt names this exact subject and attempt | `NOT_IMPLEMENTED` |
| `RESULT_AND_ARTIFACTS_VERIFIED` | local lane | the artifact manifest verifies against the returned bytes, independently of what the remote lane reported | `NOT_IMPLEMENTED` |
| `LOCAL_RECONCILIATION` | canonical reducer | the verified result is reconciled against local state that may have moved while the work was remote | `NOT_IMPLEMENTED` |
| terminals | see below | see below | `NOT_IMPLEMENTED` |

### Why the frozen contract stops at state five

`method-contract.v1.schema.json` freezes exactly the first five states, and
`verify.py` refuses any contract whose state list is anything else. This is not
an oversight to be corrected by a later leaf.

This plane can observe documents. It cannot observe a transport, a scheduler, a
sandbox or an external effect, because it has none. A state whose only possible
witness is a runtime this repository does not have would enter the frozen
contract as a state nobody can ever close — and an uncloseable state does not
stay honest. It gets closed by the cheapest thing at hand, which is a document
saying it happened. The five later states and their terminals are therefore
*named* here, so that a consumer inherits the same words, and are
`NOT_IMPLEMENTED` in the portable core until the plane that can witness them
closes them in its own lane.

### The terminals are five, not two

```text
HUMAN_ADMIT   a Human-owned operation is the only thing left
COMPLETE      verified, reconciled, and no compensation outstanding
RETRY         the attempt is repeatable under the same idempotency key
COMPENSATE    an observable effect landed and must be undone
CANCEL        the work was withdrawn before or during execution
```

Collapsing them is how a timeout becomes a disconnect, a cancellation becomes a
success, and an effect that landed with an unknown outcome becomes a retry that
applies it twice. Eleven failure distinctions must stay separately terminal —
`DISCONNECT`, `DUPLICATE`, `TIMEOUT`, `CANCELLATION`, `STALE_RESULT`,
`POLICY_REFUSAL`, `CAPABILITY_REFUSAL`, `PARTIAL_ARTIFACT`, `CLEANUP_FAILURE`,
`UNKNOWN_EXTERNAL_EFFECT`, `COMPENSATION_FAILURE` — and two of them sharing one
terminal state is refused by `M09`.

`UNKNOWN_EXTERNAL_EFFECT` is the one worth naming twice. "The remote lane may or
may not have written" is a distinct state from both success and failure, and it
is the state a compensation path exists for. A method that cannot express it
will report it as whichever neighbour is cheaper.

## Authority vocabulary

Six roles. A capability belongs to exactly one of them.

| Role | May | May never |
|---|---|---|
| `STRATEGY` | `PROPOSE` | execute, gate, commit, admit |
| `WORKER` | `EXECUTE`, `OBSERVE` | commit task state, evaluate a Gate, admit anything |
| `GATE` | `EVALUATE_GATE` | execute the thing it judges, commit state, admit |
| `CANONICAL_REDUCER` | `COMMIT_TASK_STATE` | execute, gate, admit |
| `EFFECT_LEDGER` | `COMMIT_EFFECT_LEDGER` | execute, gate, admit |
| `HUMAN_OR_TRUSTED_POLICY` | every `ADMIT_*` | be inferred from any receipt |

Three laws follow, all executable under `M11`:

1. **A Worker executes and observes.** The moment a Worker can also record that
   the task succeeded, its own report becomes the evidence for its own result.
   Canonical task state, Gate verdicts, merge, promotion, release and rollback
   each have exactly one owner and it is never the thing being judged.
2. **Every sole-holder capability has exactly one holder.** Two roles holding
   `COMMIT_TASK_STATE` is not redundancy; it is two answers with no tiebreak.
3. **Admission is Human or trusted policy, always.** `ADMIT_SEMANTIC_CONFLICT`,
   `ADMIT_IRREVERSIBLE`, `ADMIT_MERGE`, `ADMIT_PROMOTION`, `ADMIT_RELEASE` and
   `ADMIT_ROLLBACK` cannot be delegated to the lane that wants them.

**Shared projections are advisory.** A shared document, a vector index or a
memory store is a hint about the world, never the transaction. Two agents
reading the same document have not agreed on anything; they have read the same
document. `M14` refuses a projection that claims `WORKFLOW_AUTHORITY` or
`TRANSACTION_AUTHORITY`.

## Idempotency and the effect ledger

**Delivery is at-least-once.** Every transport that survives a partition
redelivers, and a method that assumes exactly-once has assumed away the only
interesting case. Two consequences:

- **A transport acknowledgement is an acknowledgement.** It is not workflow,
  task, Gate, effect, artifact, user or release success. `M04` refuses a packet
  whose `TASK` lane reads `PASS`, and `M03` refuses one whose `TASK` lane cites
  the `TRANSPORT` lane as its evidence.
- **An observable write needs three things, not one.** An idempotency key, an
  effect ledger, and a declared compensation path — `NOT_REQUIRED` only for a
  read. `M05` refuses a `REVERSIBLE_WRITE` or `IRREVERSIBLE_WRITE` packet that
  drops either requirement.

An effect ledger is whatever can answer three questions after a crash, and it is
a requirement rather than a design:

```text
has this exact effect intent already been applied?
what exactly did it apply, on which subject?
can it be undone, and by whom?
```

The idempotency key is what makes question one answerable, so it must be derived
from the effect intent and not from the attempt. A key that changes on retry
makes every redelivery a new effect.

`IRREVERSIBLE_WRITE` additionally requires Human admission before the attempt,
because a compensation path that does not exist cannot be declared. The correct
value there is `HUMAN_OWNED`, not `DECLARED`.

## Evidence laws

**Eleven lanes, each closed by its own observation:** `LOCAL`, `CLOUD`,
`TRANSPORT`, `WORKFLOW`, `TASK`, `GATE`, `EFFECT`, `ARTIFACT`, `USER_OUTCOME`,
`HUMAN_ADMIT`, `RELEASE`. Every laundering path in practice is a receipt from a
cheap lane pasted into an expensive one, so lane equality is compared literally
(`M03`).

**Interface and browser are different evidence classes.** An admitted typed API
is preferred whenever one exists. Browser automation remains a legitimate
fallback and produces `BROWSER_OBSERVATION`, which is a weaker claim about a
weaker channel: a rendered page is a projection of state, not the state. `M10`
refuses a packet whose capability class and evidence class disagree.

**A proposal is a document.** The source architecture, a fixture, and a design
note cannot carry runtime `PASS` (`M13`). A local fixture cannot establish a
cloud result and a cloud receipt cannot establish a local execution; that is
`CORE-LAW-010` applied to this method.

**Start-readiness never closes a completion edge.** The handoff keeps
`start_dependencies` and `completion_dependencies` in separate arrays for the
reason `CORE-LAW-009` gives: every child of a stack is start-ready the moment its
parent exists, so one collapsed edge class reports the whole stack as finishable.
A completion dependency proved by `START_READINESS` is refused by `M12`.

**Identity is immutable or it is not identity.** A branch name, a tag, a
floating tool version or a mutable image reference is a pointer that can be
repointed after the evidence was recorded. `M02` refuses a mutable subject.

**Provider names are adapter choices.** Naming a queue, a sandbox, a model or a
vendor in the portable core makes an adapter decision into an architecture
invariant, and the next consumer inherits a constraint nobody chose (`M08`).
Equally, consumer state — issue numbers, commit SHAs, branch references — belongs
to the consumer's packet, not to the portable core (`M15`).

## Data classification and egress

Classification happens at state two, *before* authority and effects are declared
at state three, and the order is load-bearing: the classification decides which
lanes may even be offered. Deciding the execution lane first and classifying
afterwards means the classification arrives as a justification.

- `LOCAL_ONLY` material never leaves the local lane. `M06` refuses a
  `LOCAL_ONLY` packet with egress allowed.
- Secret values, browser and device sessions, credential literals and
  machine-local host paths never enter a remote packet or a portable receipt —
  not a handle, not an example, not a comment. `M07` scans every string in both
  documents for them.

A capability grant carries a *handle* that the runtime plane resolves. The
portable method never sees the value, which is why it can be published.

## Law → executable control

Sixteen pre-registered controls are registered in [`../../cases.json`](../../cases.json)
and executed by `verify.py`. Each mutates a document that remains schema-valid,
and the checker asserts that schema-validity before accepting the kill —
otherwise a parser complaint would stand in for the law, and the law could be
deleted without anything turning red.

| Control | Refused promotion | The law in one line |
|---|---|---|
| `M01` | `DUPLICATE_RUNTIME_SCHEMA_AUTHORITY` | one interface has one owning plane |
| `M02` | `MUTABLE_SUBJECT` | a repointable name is not an identity |
| `M03` | `LANE_SUBSTITUTION` | a lane is closed by its own observation |
| `M04` | `ACK_PROMOTED_TO_TASK_PASS` | delivery is not execution |
| `M05` | `WRITE_WITHOUT_IDEMPOTENCY_OR_EFFECT_LEDGER` | at-least-once makes a bare write a double write |
| `M06` | `LOCAL_ONLY_REMOTE_EGRESS` | classification decides the lane |
| `M07` | `SECRET_OR_SESSION_VALUE` | packets and receipts are publishable |
| `M08` | `PROVIDER_NAME_AS_ARCHITECTURE_INVARIANT` | providers are adapters |
| `M09` | `TERMINAL_STATE_COLLAPSE` | failure distinctions stay distinguishable |
| `M10` | `BROWSER_AS_API_EVIDENCE` | the channel is part of the claim |
| `M11` | `WORKER_SELF_PROMOTION` | the judged does not judge |
| `M12` | `START_DEPENDENCY_USED_AS_COMPLETION_PROOF` | two edge classes, never one |
| `M13` | `SOURCE_OR_FIXTURE_AS_LIVE_PASS` | a proposal is a document |
| `M14` | `SHARED_MEMORY_AS_TRANSACTION_AUTHORITY` | projections advise, transactions decide |
| `M15` | `CONSUMER_STATE_LEAKED_INTO_PORTABLE_CORE` | the portable core is consumer-free |
| `M16` | `RUNTIME_CONTRACT_DECLARED_IMPLEMENTED_WITHOUT_DIGEST` | implemented means digested |

Run them:

```sh
bash skills/agentic-tech-lead-orchestration/tests/dual-agent-offload-contract/verify.sh
```

### What is law here but not executable here

Reconnect, stale-result handling, cancellation propagation, compensation
execution, cleanup verification and artifact re-verification are stated in this
method and have no control in this repository, because there is nothing here to
run them against. They are `NOT_IMPLEMENTED`, not `SKIPPED_BY_POLICY`. Their
executable form belongs to the plane that owns the runtime, and a portable green
here says nothing about them.

## Evidence ceiling

This method and its deterministic contract are the whole of what this directory
can establish. Runtime wire schemas, local transport, cloud execution, provider
isolation, physical reconnect, external effects, artifact durability, user
outcome, production and commercial closure remain consumer-owned evidence in
their own lanes.

License choice, provider admission, credentials, data-egress permission,
irreversible effects, merge, release and production activation remain Human or
trusted-authority operations.

## Not built yet

| Leaf | Scope | State |
|---|---|---|
| method contract and handoff requirements | the two schemas, four positive fixtures, sixteen controls | landed |
| deterministic method validator | a normalized rule set a consumer can run over *its own* method contract, rather than over the fixtures here | `NOT_IMPLEMENTED` |
| positive, hollow and mutation matrix | a hollow-implementation control — a validator that returns green with its rules deleted — and a coverage matrix over the sixteen refusals | `NOT_IMPLEMENTED` |
| trigger-selected module and shared indexes | module activation, `AGENTS.md` and repository-index routes, consumer index rows | `NOT_IMPLEMENTED` |

The first row is the only one with executable bytes. The three below it are
named so a reader knows the list is short on purpose, which is the one thing a
short index cannot say for itself.
