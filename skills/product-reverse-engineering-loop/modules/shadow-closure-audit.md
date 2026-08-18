# Shadow product closure audit

A read-only monitor that decides whether a product problem is actually closed,
across the six evidence lanes, against the exact bytes that claim it is. It
composes the read-only Shadow contract in
[`../../procedural-shadow-runtime/SKILL.md`](../../procedural-shadow-runtime/SKILL.md)
— Shadow workers are read only, intervention happens at declared sync points,
and no private reasoning is ever collected — and applies it to one question the
runtime primitive does not ask: *is the product problem closed, or is a cheaper
lane standing in for the one that would settle it?*

This module produces findings. It never writes an implementation, never opens or
edits an issue, and never decides a merge, a release, a right, a customer truth
or a commercial outcome.

## Trigger

Load when a concrete product, repository or source claims a problem is handled
and somebody must decide what that claim has actually earned: a status line in a
README, a closed issue, a green suite offered as evidence of a live workflow, a
first green that arrived while proof obligations were still open, or a review
that must be handed to an independent reviewer with no prior context.

## Non-trigger

Do not load to grade signals, classify mechanisms, derive the closure matrix or
compile packets — those are core transitions and the matrix in
[`../references/problem-closure-matrix.schema.json`](../references/problem-closure-matrix.schema.json)
already owns them. Do not load to *fix* anything: the moment the same worker
edits the subject, the audit stops being independent and its findings stop being
checkable by anyone else.

## Assumptions

The subject can be read without changing it, every claim it makes is carried by
bytes that can be hashed, and the levels below a claim can be inspected. When
that is untrue — the surface is unreachable, the evidence is somebody's memory,
or the subject moves while it is being read — the honest output is an audit with
fewer rungs marked `PASS`, not an audit with softer wording.

## The ladder

Seven earned levels over six lanes, plus two terminals. The `IMPLEMENTATION`
lane carries two rungs because code existing and code being verified are
different obligations produced by different evidence:

| Level | Lane | Closed only by |
|---|---|---|
| `SOURCE_ANCHORED` | `SOURCE` | a source document or an issue record |
| `MECHANISM_BOUND` | `MECHANISM` | an observation of the mechanism with a refutation condition |
| `IMPLEMENTED` | `IMPLEMENTATION` | the code subject itself |
| `TECH_VERIFIED` | `IMPLEMENTATION` | a deterministic suite or a CI run over that exact subject |
| `LIVE_WORKFLOW_VERIFIED` | `RUNTIME` | a live workflow run |
| `USER_VALIDATED` | `USER` | a user report |
| `PAID_VALIDATED` | `COMMERCIAL` | a completed payment, or a Human admission of one |
| `BLOCKED` | — | nothing was earned and nothing failed |
| `FAILED` | — | some rung is `FAIL` |

The highest earned level is the longest unbroken `PASS` prefix, and
`scripts/check_prel_contract.py` recomputes it rather than reading it. A level
stated above what the rungs underneath support is `LEVEL_LADDER_SKIP`, and it is
reported with both the declared and the computed value so the gap is legible
without re-deriving it.

## Procedure

1. **Bind the subject.** Record what is being audited, at which revision, and
   which surfaces were compared. Every later anchor carries its own artifact and
   sha256, so a reader can re-hash the file instead of trusting the sentence
   about it.
2. **Read the declaration.** For each material problem, capture what the subject
   says about itself and the exact bytes that say it — a README line, a status
   table, an issue state. `claimed_level` is that declaration translated into the
   ladder, not the auditor's opinion of it.
3. **Fill the rungs from evidence kinds.** Each rung records its state and its
   anchors. The kind decides what it may close: a `CI_RUN` closes
   `TECH_VERIFIED` and nothing above it, a `MODEL_JUDGMENT` closes nothing at
   all. This is the whole of "no level may be inferred from a cheaper lane", and
   it is a table lookup rather than a judgement.
4. **Separate absence from a skipped obligation.** `ABSENT` means no evidence of
   that kind exists. `NOT_EXERCISED`, `NOT_IMPLEMENTED` and `SKIPPED_BY_POLICY`
   mean an oracle exists and nobody ran it — those must be reopened by name in
   `reopened_obligations`, because a first green elsewhere otherwise inherits
   them as closed.
5. **Report the contradiction out loud.** A subject declaring more than it earned
   requires a `DECLARED_STATUS_AHEAD_OF_EVIDENCE` finding. Without it the audit
   absorbed the claim, which is indistinguishable from agreeing with it.
6. **Reconcile the denominator.** Findings raised, findings reported and findings
   withdrawn with a reason must add up. Dissent leaves an audit only by being
   written down; a finding that silently disappears takes the disagreement with
   it.
7. **Emit the delta as proposals.** `issue_delta` items carry
   `write_authority: NO_WRITE_AUTHORITY`. They describe the repair somebody else
   may choose to make.
8. **Validate before handing anything over.**

   ```bash
   python3 scripts/check_prel_contract.py --artifact <audit.json> --resolve-subjects <subject-root>
   ```

   `--resolve-subjects` re-hashes every anchor against the tree it names, so an
   audit describing bytes that moved is `STALE_SUBJECT` instead of a confident
   report about a file that no longer exists.

## Independent review handoff

The audit *is* the handoff packet. It declares `reviewer.identity`,
`mode: READ_ONLY_FINDINGS_ONLY`, `requires_prior_conversation: false` and
`requests_private_reasoning: false`, and `public_snapshot` states that a
completed review is neither a merge nor a release. A reviewer who has read
nothing else can consume it: every finding names its subject, its digest and
what was observed there. A packet that points at context outside itself is
refused by name, because that context is exactly what an independent reviewer
does not have.

## Controls this module exists to fail

| Control | How it is refused |
|---|---|
| Shadow edits the implementation it audits | `SHADOW_WRITE_AUTHORITY` |
| a Builder drops an inconvenient finding | `DISSENT_OMITTED_FROM_DENOMINATOR` |
| a source statement treated as observed internals | kind table: `SOURCE_DOCUMENT` closes only `SOURCE_ANCHORED` |
| a model judge overrides a deterministic result | `MODEL_JUDGE_OVERRIDE` |
| a stale receipt reused for the current subject | `STALE_SUBJECT` |
| a local or CI receipt offered as a live, user or paid outcome | `EVIDENCE_LANE_PROMOTION` |
| a skipped proof obligation inherited by the first green | `FIRST_GREEN_OBLIGATION_SKIPPED` |
| a status line ahead of its evidence | `CONTRADICTORY_CLOSURE_STATUS` |
| review completion presented as merge or release | `MERGE_OR_RELEASE_AUTHORITY_ASSUMED` |
| private reasoning published, or required, to read the packet | `PRIVATE_REASONING_IN_PUBLIC_SNAPSHOT`, `SNAPSHOT_REQUIRES_PRIOR_CONVERSATION` |

Each row is a planted control in `tests/selftest.py`; a control that stopped
firing is a red suite rather than a paragraph nobody re-read.

## Evidence ceiling

```text
the audit's own contracts and controls        PASS by the suite in tests/
that a problem is closed in the world         only ever as high as its rungs
that the audit found every material problem   NOT_EXERCISED — selection is a judgement
user, paid and market truth                   owned by whoever can produce that lane
merge, release, rights, customer truth        HUMAN_ADMIT_REQUIRED
```

An audit proves what the anchors it names say at the revision it names. One
canary against one repository proves that repository at that revision and
nothing about any other.

## Fallback

When a lane cannot be reached, record the rung as `ABSENT` with its owner and
continue — a thin audit is usable and a padded one is not. When a subject moves
mid-audit, stop and re-bind rather than repairing digests: an audit half-bound
to old bytes is worse than no audit, because it reads as current. When the
material problems cannot be enumerated without the subject's own summary of
them, say so in the ceiling instead of inheriting that summary as the scope.

## Forbidden overrides

This module may not override `CORE-LAW-001` through `CORE-LAW-008` in
[`../SKILL.md`](../SKILL.md). It may not raise a rung by argument, admit a right,
close a lane with an anchor from another kind, drop a finding without a recorded
reason, write to the subject it audits, request or publish private reasoning,
widen filesystem, network, secret or merge authority, or promote itself from
findings to decisions because the findings look conclusive.
