# Tests

```bash
bash tests/run-all.sh
```

Three control classes, in the order they run.

**Positive.** Every committed artifact validates against its schema, its semantic
laws, and every subject digest it names. A red positive control stops the suite
before any mutation runs, so a planted defect is never credited to a suite that
was already failing.

**Byte-stability.** Each compiled projection is re-compiled from its input and
byte-compared. A hand-edited dossier, closure matrix or handoff is a red suite
rather than a second source of truth.

**Mutation, hollow and stale-subject.** `selftest.py` plants one defect per
refusal code in a disposable copy of `references/` and requires the checker to
refuse it *by that code*. Requiring the code rather than a non-zero exit is the
whole point: a checker that fails everything for one generic reason looks
identical to a working one when you only read the exit status.

The hollow controls are the ones that catch the failure mode Markdown cannot.
A signal set with every required field present and `TBD` in the evidence slot
satisfies every `minLength` in the schema, which is exactly why the placeholder
scan exists. An `OBSERVED_ARTIFACT` with a null observation is the same failure
wearing the right label.

The stale-subject controls plant three distinct states, because they fail
differently: an upstream artifact that changed after the projection was compiled,
a named subject whose bytes moved, and a named subject that is no longer on the
tree at all.

Two controls exercise the compiler rather than the checker: a hand-edited
projection must fail `--check`, and a signal set with no observable mechanism and
no graded magic moment must be refused rather than compiled into an empty MVP.

## Proving the suite is not hollow

The suite asserts its own defects go red; it does not assert that a *weakened
checker* goes red. That was verified separately by disabling three rules one at
a time in a scratch copy — the attention-as-demand rule, the lane-substitution
rule and the consumer-topology rule — and confirming the matching control
reported `planted defect survived` each time. Re-run that check by hand after
changing a rule's condition; a control whose rule can be deleted without the
suite noticing is decoration.
