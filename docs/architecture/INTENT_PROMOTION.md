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
| `VERIFIED` | owning evaluator receipts at the **exact head** | nothing durable |
| `ADMITTED` | an admitted merge or release subject binding this candidate | module and project scope |
| `CANONICAL` | human approval bound to that commit | root/global scope |
| `SUPERSEDED` | a named supersession target | nothing |
| `REVOKED` | human approval | nothing |

`HYPOTHESIS` and `CANDIDATE` are the only non-authoritative states, and the
contract may not widen that set — widening it is how a guess reaches durable
memory.

**Durable projection begins at `ADMITTED`, for every scope.** `VERIFIED` means
the evidence held at one commit; it does not mean the change survived review and
landed. The contract schema's `minimum_state` enum is `ADMITTED | CANONICAL`, so
authorising a durable write at PR-open or CI-green is unexpressible rather than
merely refused — an earlier version guarded only `ROOT_GLOBAL`, which left
module and project destinations reachable from `VERIFIED`.

## Laws

1. **Evidence is bound to a commit, not to a pipeline.** An evaluator receipt
   whose `subject_commit_sha` or `subject_tree_sha` differs from the promoted
   subject is refused. An old receipt does not carry forward, however green it
   was.
2. **"Owning" is an identity, not a label.** Naming an evaluator and writing
   `status: PASS` is something any caller can do. An admitted run must also
   carry the evaluator's pinned version, its artifact digest, its own receipt
   reference and digest, and an execution origin — none of which can be produced
   without the evaluator and its receipt existing. Duplicate evaluator ids are
   refused, because a repeated run can pad a receipt with the appearance of
   independent coverage.
3. **A merge subject must bind the candidate it admitted.** A non-null
   `merge_subject` proved nothing; a syntactically valid random SHA satisfied it.
   It must now name the same repository, the same candidate head and tree as the
   promoted subject, and a forge readback observed at the merge commit it is
   offered as evidence for. A release artifact is a distinct object from a
   commit, and reusing the commit identity as its digest is refused.
4. **A flag requests approval; it cannot be one.** A caller flag naming
   `override` or `approve` with no human approval receipt is refused.
5. **An agent cannot manufacture the approval that authorises it.** The
   approver kind must be `HUMAN`, the approval must name the same commit being
   promoted, and it must carry `generated_by_agent: false`, a review reference,
   and a trusted readback source. An agent can write `approver_kind: HUMAN`; it
   cannot honestly write `generated_by_agent: false`, which turns the
   substitution from an omission into a stated lie.
6. **Root/global destinations are reachable only from `CANONICAL`**, and must
   be declared `human_owned`.
7. **Writeback is append-only, and lineage needs a ledger.** A `SUPERSEDE`
   writeback must name the receipt it replaces, and that predecessor must exist
   in the append-only ledger, still be current, and match on digest, state,
   subject and intent. Without a ledger, `supersedes` is a claim about a
   predecessor nothing can confirm ever existed — an unverifiable lineage claim
   is not lineage. Similarity is never lineage.
8. **A terminal intent projects nothing, and is not current.** A `SUPERSEDED`
   or `REVOKED` receipt carrying a writeback is refused, and so is one still
   marked `current` in the ledger.
9. **Rules and evidence move together.** The receipt binds the contract's byte
   digest, so a receipt issued under different rules than the ones being applied
   is refused rather than silently re-interpreted.
10. **Free-form private reasoning is never persisted**, at any nesting depth.
    A `chain_of_thought`, `reasoning`, `scratchpad`, `private_notes` or
    `thinking` field anywhere in a contract or receipt is refused.

## External authority readback

The semantic gate above closes every substitution a receipt can make about
itself. One remains that a receipt cannot close alone:

```text
the receipt says an evaluator receipt exists, with this digest
the receipt embeds forge readback fields
the receipt labels an approval Human and names a readback source
→ and the semantic checker believed all of it
```

Those fields are caller-supplied. A caller who can write `receipt_digest` can
write any value into it. `scripts/check_intent_promotion_authority.py` requires
the referenced bytes to be present and to hash to what the receipt claimed, so
the digest stops being a label and starts being a check, and requires each
evidence artifact's contents to agree field-by-field with the receipt that cited
it.

It also **executes** the committed schemas with a pinned Draft 2020-12
validator. They were previously parsed with `json.tool`, which proves they are
JSON — not that anything validates against them. `additionalProperties: false`,
conditional branches and required nested fields were never deciding gates. A
schema nobody runs is the same shape of defect as a test nobody runs, and the
checker exits 70 rather than skipping validation if the validator is absent:
falling back to "skip" would make the strictest gate the one most likely to be
silently off.

```bash
python3 scripts/check_intent_promotion_authority.py \
  --bundle evals/fixtures/intent-promotion/authority/bundle.json
python3 scripts/check_intent_promotion_authority.py --selftest
```

What stays outside: whether the forge really said this, whether the merge really
happened, and whether a human really approved. Those are external authority.
This layer proves the bundle is internally consistent with bytes that exist,
which is a smaller claim, stated as such.

## Running the gate

```bash
python3 scripts/check_intent_promotions.py contract <contract.json>
python3 scripts/check_intent_promotions.py receipt <receipt.json> \
  --contract <contract.json> --ledger <ledger.json>
python3 scripts/check_intent_promotions.py selftest
```

`selftest` plants 50 defects — one per law above, plus each control named in
the owning issues — and requires every one to be refused, so a law that stops
biting is reported rather than assumed.

Exit codes separate two events that look alike: `2` is a promotion that was
evaluated and refused, `64` is an input that could not be evaluated at all.
Collapsing them makes a mistyped path read as a policy failure, which is the
more dangerous direction — it looks like the gate is working.

## Evidence boundary

```text
lifecycle and receipt mechanics       IMPLEMENTED
contract/receipt digest binding       IMPLEMENTED
external evidence byte readback       IMPLEMENTED
Draft 2020-12 deciding validation     IMPLEMENTED
external provider authenticity        NOT_EXERCISED
actual merge or release occurrence    NOT_EXERCISED
memory provider integration           NOT_EXERCISED
CONTEXT.md mutation                   NOT_EXERCISED
production memory migration           NOT_EXERCISED
business-rule approval                HUMAN_ADMIT_REQUIRED
root/global invariant admission       HUMAN_ADMIT_REQUIRED
```
