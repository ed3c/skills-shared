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
| Executable admission controls | [`scripts/check_profile_admission.py`](scripts/check_profile_admission.py) |
| Controls and expected outcomes | [`evals.json`](evals.json), [`tests/`](tests/) |

## What is implemented

```text
profile admission controls        IMPLEMENTED
typed contracts and receipts      IMPLEMENTED (landed with the foundation)
deterministic rule evaluation     NOT_IMPLEMENTED — owned by CTL 03
official ASD-STE100 rule set      NOT_EXERCISED — the specification is not held here
semantic rewrite quality          NOT_IMPLEMENTED as a deterministic check
compliance / certification        HUMAN_ADMIT_REQUIRED
```

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
