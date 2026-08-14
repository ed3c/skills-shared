---
name: controlled-technical-language-harness
description: |
  Check and rewrite technical text against a controlled-language profile, and
  emit a typed receipt that separates what a deterministic checker proved from
  what a model suggested. Use when a document must satisfy a named writing
  standard, a project termbase, or a bounded rewrite loop with evidence.
  Do not use as a general style critic, a translator, a compliance certifier,
  or a substitute for the official standard's own authority.
license: MIT
compatibility: Any Agent Skills-compatible coding agent with repository read access. Optional parsers, models, and providers accelerate lanes but are never evidence authorities.
metadata:
  version: "1.0.0"
  procedure: "controlled-language-check-and-rewrite"
---

# controlled-technical-language-harness

A portable procedural core for controlled technical language. It names
capability slots and evidence laws. It does not require one parser, one model,
one provider, one proprietary dictionary, one consumer path, or a live session.

The contract layer this consumes lives in
[`../../evals/schema/`](../../evals/schema/) and
[`../../scripts/controlled_language/`](../../scripts/controlled_language/).
This Skill does not define a second contract vocabulary.

## State machine

```text
SCOPE
→ BIND EXACT INPUT
→ CLASSIFY DOCUMENT
→ SELECT PROFILE
→ BIND TERMBASE
→ SELECT PRIVACY LANE
→ DISPATCH EVALUATORS
→ BOUNDED REPAIR
→ ASSERT EXACT RECEIPT
→ HANDOFF
```

Each transition has one named failure. A transition that cannot prove its
precondition emits that failure rather than advancing.

| Transition | Named failure |
|---|---|
| BIND EXACT INPUT | `SUBJECT_UNBOUND` — no exact digest for the text under review |
| CLASSIFY DOCUMENT | `DOCUMENT_CLASS_UNKNOWN` |
| SELECT PROFILE | `PROFILE_ABSENT`, `PROFILE_NOT_TRIGGERED` |
| BIND TERMBASE | `TERMBASE_ABSENT`, `TERMBASE_STALE` |
| SELECT PRIVACY LANE | `PRIVACY_LANE_UNDECIDED` |
| DISPATCH EVALUATORS | `EVALUATOR_ABSENT`, `EVALUATOR_ERROR` |
| BOUNDED REPAIR | `REPAIR_BUDGET_EXHAUSTED`, `NO_IMPROVEMENT` |
| ASSERT EXACT RECEIPT | `RECEIPT_SUBJECT_MISMATCH` |

## Evidence laws

1. **Deterministic result outranks model prose.** A rule the checker proved
   broken stays broken however fluently a rewrite explains itself. A
   deterministic failure vetoes an advisory pass.
2. **A profile claims only the source identity it can produce.** Naming an
   official standard edition requires a verified official source with an exact
   locator and digest. Without one, the profile is what it actually is — a
   proposal-derived approximation — and says so.
3. **Absence is not compliance.** No profile, no termbase, no evaluator, and no
   privacy decision each produce their own named state, distinct from a pass.
4. **Technical Names and Technical Verbs are project-owned.** They are admitted
   by a human, never inferred from frequency or from the model's confidence.
5. **Compliance and safety-critical claims are Human-owned.** This Harness
   produces evidence toward such a claim; it never makes one.

## Profile selection

A profile is trigger-selected, never a mandatory core dependency. The core runs
with zero profiles loaded and reports `PROFILE_ABSENT`; it does not silently
fall back to a default standard.

Available profiles live in [`modules/`](modules/). Load exactly the one the
document class and the caller's named standard select.

## Document format

The caller declares the format; it is never sniffed from content, because a
module that decides its own applicability has no failure state. Structured XML
declared over prose, or prose declared over XML, is refused rather than guessed
at — see [`modules/format-structured-xml.md`](modules/format-structured-xml.md)
and [`modules/format-extracted-text.md`](modules/format-extracted-text.md).

Parser output stays a **candidate** until source-node readback succeeds. An
output can be well-formed, read better than the original, and still have dropped
a warning or reordered two steps; `scripts/check_document_preservation.py`
refuses it.

## Privacy lanes

```text
LOCAL_ONLY         no text leaves the process
PRIVATE_ENDPOINT   named admitted provider inside the trust boundary
EXTERNAL_APPROVED  named admitted provider outside it
```

The lane is decided before any evaluator runs, and the decision is recorded.
An undecided lane is `PRIVACY_LANE_UNDECIDED`, not an implicit `LOCAL_ONLY`.

`RESTRICTED` always routes `LOCAL_ONLY` with network disabled. `CONFIDENTIAL`
reaches an external lane only with a human approval bound to the same document
digest. Provider *health* and privacy *admission* are separate states, and an
admitted provider that is unhealthy blocks rather than falling back to a lane the
document was never admitted to — see
[`modules/privacy-routing.md`](modules/privacy-routing.md).

## Bounded repair

```text
violation set
→ at most N rewrite attempts (N declared in the request)
→ re-run the same deterministic evaluators
→ violation count must strictly decrease
→ otherwise STOP and hand the remainder to a human
```

A repair may not delete a control, relax a rule, edit an evaluator so it passes,
or promote a proposal-derived rule into an official one.

## Receipt

Every run ends in a `controlled-language-receipt/v1` bound to the exact subject
digest. It separates deterministic observations, advisory suggestions, and
absent lanes. Validate with:

```bash
python3 scripts/check_controlled_language_contracts.py receipt <receipt.json>
```

## Evaluator lanes

Two lanes, and the difference between them is not how reliable they are.

```text
DETERMINISTIC          the result follows from written rules and the exact
                       input, with no inference
                       scripts/lint_deterministic.py

CALIBRATED_HEURISTIC   the result is a guess, however consistent
                       scripts/check_heuristic_calibration.py
```

A pinned parser is perfectly repeatable and still guesses. Repeatability is not
correctness — a model that is wrong the same way every time is exactly as
wrong — so a pinned implementation does not promote its output into the
deterministic lane.

A heuristic is admitted only with a pinned implementation identity and digest,
the corpus it was measured against, **both** error rates, and a ceiling it may
not exceed. Even fully admitted:

```text
a heuristic cannot produce a final PASS on its own
a heuristic cannot overturn a deterministic failure
an evaluator that errored is not an evaluator that passed
```

## Measuring the assembled Harness

An A/B comparison of this Harness is scored by
[`scripts/score_ab.py`](scripts/score_ab.py), and most of what that script does
is refuse invalid experiments rather than compute metrics. An unfair comparison
produces the same shape of numbers as a fair one and reads better:

```text
a different evaluator per arm       the candidate is graded more kindly
a larger budget for one arm         the candidate had more attempts
the baseline given skill content    both arms are the candidate
failed conditions dropped           the denominator flatters the rate
a semantic PASS over a hard failure a deterministic breach disappears
```

No metric is emitted for a bundle that fails validity. A number computed from an
invalid experiment is worse than no number, because it looks like evidence.

## Evidence boundary

```text
deterministic word budgets           IMPLEMENTED
deterministic forbidden tokens       IMPLEMENTED
exact source-span digests            IMPLEMENTED
source-node preservation             IMPLEMENTED
privacy class to lane routing        IMPLEMENTED
A/B experiment validity gate         IMPLEMENTED
physical model or harness runs       NOT_EXERCISED
real S1000D / DITA schema validation NOT_EXERCISED
PDF extraction itself                NOT_EXERCISED — the caller supplies text
live provider or endpoint            NOT_EXERCISED
typed contracts and receipts         IMPLEMENTED
profile source-identity discipline   IMPLEMENTED
heuristic admission and composition  IMPLEMENTED
mood, voice, noun-cluster detection  NOT_IMPLEMENTED — heuristic lane, uncalibrated
official ASD-STE100 rule set         NOT_EXERCISED — see modules/profile-ste.md
semantic rewrite quality             NOT_IMPLEMENTED as a deterministic check
compliance / certification claim     HUMAN_ADMIT_REQUIRED
safety-critical acceptance           HUMAN_ADMIT_REQUIRED
```
