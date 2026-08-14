# controlled-technical-language-harness

A portable procedural core for checking and rewriting technical text against a
controlled-language profile, and for emitting a receipt that keeps what a
checker proved separate from what a model suggested.

## Document authority

| Question | Route |
|---|---|
| Procedure, state machine, evidence laws | [`SKILL.md`](SKILL.md) |
| Interchange contracts and schemas | [`../../evals/schema/`](../../evals/schema/) |
| Contract foundation and its source proposal | [`../../docs/architecture/CONTROLLED_TECHNICAL_LANGUAGE_HARNESS.md`](../../docs/architecture/CONTROLLED_TECHNICAL_LANGUAGE_HARNESS.md) |
| Profile admission rules | [`references/PROFILE_ADMISSION.md`](references/PROFILE_ADMISSION.md) |
| The Simplified Technical English profile | [`modules/profile-ste.md`](modules/profile-ste.md) |
| Profile admission controls | [`scripts/check_profile_admission.py`](scripts/check_profile_admission.py) |
| Deterministic evaluators | [`scripts/lint_deterministic.py`](scripts/lint_deterministic.py) |
| Calibrated-heuristic admission | [`scripts/check_heuristic_calibration.py`](scripts/check_heuristic_calibration.py) |
| Source-node preservation | [`scripts/check_document_preservation.py`](scripts/check_document_preservation.py) |
| Privacy class to lane routing | [`scripts/check_privacy_routing.py`](scripts/check_privacy_routing.py) |
| Structured XML formats | [`modules/format-structured-xml.md`](modules/format-structured-xml.md) |
| Plain and extracted text | [`modules/format-extracted-text.md`](modules/format-extracted-text.md) |
| Privacy routing | [`modules/privacy-routing.md`](modules/privacy-routing.md) |
| Controls and expected outcomes | [`evals.json`](evals.json), [`tests/`](tests/) |

## What is implemented

```text
profile admission controls        IMPLEMENTED
typed contracts and receipts      IMPLEMENTED (landed with the foundation)
deterministic word budgets        IMPLEMENTED
deterministic forbidden tokens    IMPLEMENTED
heuristic admission boundary      IMPLEMENTED
heuristic implementations         NOT_IMPLEMENTED — mood, voice, noun clusters
official ASD-STE100 rule set      NOT_EXERCISED — the specification is not held here
semantic rewrite quality          NOT_IMPLEMENTED as a deterministic check
compliance / certification        HUMAN_ADMIT_REQUIRED
```

The two evaluator lanes are separated by what kind of claim they make, not by
how reliable they are. A pinned parser is repeatable and still guesses, so it
stays in the heuristic lane — where it cannot conclude a run or overturn a
deterministic failure however good its numbers are.

The shipped profile is proposal-derived and says so. It approximates Simplified
Technical English; it is not ASD-STE100, and the admission controls refuse any
pack that blurs that line. The current official edition is Issue 9 of 15 January
2025, verified with ASD and recorded in the profile module — verifying that an
edition exists is a different thing from holding it, and only the first has
happened.

## Run the controls

```bash
bash skills/controlled-technical-language-harness/tests/run-all.sh
```

`SELFTEST GREEN` means the canonical pack is admitted and 15 planted defects are
each refused. It does not mean any text has been checked against any standard.
