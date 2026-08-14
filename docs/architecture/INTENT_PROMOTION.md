# Intent Promotion

> Status: lifecycle and receipt mechanics only. Nothing here connects to a
> memory provider, mutates `CONTEXT.md`, approves a business rule, establishes
> merge truth, or performs a production writeback.

Extends the Intent-Bound Constraint control plane
([`evals/schema/intent-bound-constraint.schema.json`](../../evals/schema/intent-bound-constraint.schema.json)).
It does not introduce a second meta-evaluator authority.

## The substitutions this prevents

Each of these looks like evidence of the next state, and is not:

```text
a PR was opened            → so the intent is durable
CI went green              → so the intent is verified
a flag was passed          → so a human approved
prose says the same thing  → so the old record can be replaced
```

The first three infer authority from an event that never carried it. The fourth
replaces history with resemblance. A well-formed receipt can assert any of them,
which is why the gate is separate from the schema.

## Lifecycle

```text
HYPOTHESIS
→ CANDIDATE
→ PROPOSED
→ VERIFIED
→ ADMITTED
→ CANONICAL
→ SUPERSEDED | REVOKED
```

| State | What it takes to enter | What it may write |
|---|---|---|
| `HYPOTHESIS` | nothing | nothing durable |
| `CANDIDATE` | nothing | nothing durable |
| `PROPOSED` | an exact branch or PR subject | nothing durable |
| `VERIFIED` | owning evaluator receipts at the **exact head** | module scope |
| `ADMITTED` | an admitted merge or release subject | project scope |
| `CANONICAL` | human approval bound to that commit | root/global scope |
| `SUPERSEDED` | a named supersession target | nothing |
| `REVOKED` | human approval | nothing |

`HYPOTHESIS` and `CANDIDATE` are the only non-authoritative states, and the
contract may not widen that set — widening it is how a guess reaches durable
memory.

## Laws

1. **Evidence is bound to a commit, not to a pipeline.** An evaluator receipt
   whose `subject_commit_sha` differs from the promoted commit is refused. An
   old receipt does not carry forward, however green it was.
2. **A flag requests approval; it cannot be one.** A caller flag naming
   `override` or `approve` with no human approval receipt is refused.
3. **An agent cannot manufacture the approval that authorises it.** The
   approver kind must be `HUMAN`, and the approval must name the same commit
   being promoted.
4. **Root/global destinations are reachable only from `CANONICAL`**, and must
   be declared `human_owned`.
5. **Writeback is append-only.** Replacement is by lineage: a `SUPERSEDE`
   writeback must name the receipt it replaces. Similarity is not lineage.
6. **A terminal intent projects nothing.** A `SUPERSEDED` or `REVOKED` receipt
   carrying a writeback is refused — presenting a revoked intent as current is
   the exact failure those states exist to prevent.
7. **Rules and evidence move together.** The receipt binds the contract's byte
   digest, so a receipt issued under different rules than the ones being applied
   is refused rather than silently re-interpreted.
8. **Free-form private reasoning is never persisted.**

## Running the gate

```bash
python3 scripts/check_intent_promotions.py contract <contract.json>
python3 scripts/check_intent_promotions.py receipt <receipt.json> --contract <contract.json>
python3 scripts/check_intent_promotions.py selftest
```

`selftest` plants 24 defects — one per law above, plus each control named in the
owning issue — and requires every one to be refused, so a law that stops biting
is reported rather than assumed.

## Evidence boundary

```text
lifecycle and receipt mechanics       IMPLEMENTED
contract/receipt digest binding       IMPLEMENTED
memory provider integration           NOT_EXERCISED
CONTEXT.md mutation                   NOT_EXERCISED
production memory migration           NOT_EXERCISED
business-rule approval                HUMAN_ADMIT_REQUIRED
root/global invariant admission       HUMAN_ADMIT_REQUIRED
```
