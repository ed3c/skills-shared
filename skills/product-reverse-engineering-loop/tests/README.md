# Tests

```bash
bash tests/run-all.sh
```

Three control classes, in the order they run.

**Positive.** Every committed artifact validates against its schema, its semantic
laws, and every subject digest it names. A red positive control stops the suite
before any mutation runs, so a planted defect is never credited to a suite that
was already failing.

*The set of artifacts is derived, not listed.* `selftest.py` reads every `*.json`
under `references/`, `examples/` and `tests/fixtures/`, treats any file carrying a
top-level `schema` string as an artifact, and reconciles that set against the
schema registry inside `scripts/check_prel_contract.py` in **both** directions: a
registered schema with no committed artifact is red, and an artifact whose schema
the checker does not register is red. The previous version of this suite
enumerated six filenames, which is how the three schemas and two compilers that
landed with #370/#371 reached CI through nothing at all while the suite stayed
green. Adding an artifact now changes the printed denominators without editing a
list; adding a schema without an artifact turns the suite red.

**Byte-stability.** Each compiled projection is re-compiled from its input and
byte-compared: the dossier, closure matrix and handoff from `references/`, and the
session-dispatch request and external-projection registry from the drafts in
`tests/fixtures/`. A hand-edited projection is a red suite rather than a second
source of truth.

**Mutation, hollow and stale-subject.** `selftest.py` plants one defect per
refusal code in a disposable copy of the relevant artifact root and requires the
checker to refuse it *by that code, at that exit status*. Requiring the code
rather than a non-zero exit is the whole point: a checker that fails everything
for one generic reason looks identical to a working one when you only read the
exit status. The compiler controls additionally assert the true exit code — 2 is
a refusal, 64 is a tool that could not run, and a suite that accepts either
cannot tell a refused mutation from a crashed checker.

The hollow controls are the ones that catch the failure mode Markdown cannot.
A signal set with every required field present and `TBD` in the evidence slot
satisfies every `minLength` in the schema, which is exactly why the placeholder
scan exists. An `OBSERVED_ARTIFACT` with a null observation is the same failure
wearing the right label.

The stale-subject controls plant three distinct states, because they fail
differently: an upstream artifact that changed after the projection was compiled,
a named subject whose bytes moved, and a named subject that is no longer on the
tree at all.

Controls that exercise a compiler rather than the checker: a hand-edited
projection must fail `--check`; a signal set with no observable mechanism and no
graded magic moment must be refused rather than compiled into an empty MVP; a
draft claiming one subject both `CONFIRMED` and `CONTRADICTED` must exit 2 as
`K09_CONTRADICTION_DROPPED` rather than quietly keeping one verdict; and a draft
missing a required field must exit 64 rather than being reported as a refusal.

**Pin controls.** Two controls run an *adversarial* draft — one asserting
`RUNNING` with a pid and every authority true, one asserting `MACHINE_AUTHORITY`
— and assert that the compiled bytes are pinned anyway: `LAUNCH_REQUESTED`, a
null `running_session`, all-false authority, and the `HUMAN_PROJECTION` ceiling.
A refusal proves the compiler rejects a lie; a pin proves it never reads it.

## Known limitation, recorded rather than asserted away

`check_session_dispatch` compares lease paths with a bare `startswith` and no
separator boundary, so two disjoint sibling directories — `skills/example` and
`skills/example-two` — are reported as `C06_OVERLAPPING_WRITER_LEASE`. The
control `session_dispatch_lease_prefix_known_limitation` asserts the behavior
that exists rather than the behavior that is wanted: the checker lives in the
read-only `scripts/` lease, and a control asserting the ideal would be red on
arrival and tell nobody anything. The defect is fail-closed — it over-refuses,
never under-refuses — so it is noise rather than a hole, and this control is the
record that the noise is measured rather than undiscovered. Delete the control in
the same change that adds the boundary check.

## Proving the suite is not hollow

The suite asserts its own defects go red; it does not assert that a *weakened
checker* goes red. That is verified separately, on a throwaway copy of the Skill,
by deleting a rule and confirming the matching control reports `planted defect
survived`. Verified this way: the attention-as-demand rule, the lane-substitution
rule, the consumer-topology rule, and the `C09` lifecycle-ordering rule. The
tree-derived discovery was falsified the same way — deleting one committed
artifact reports `registered schema ... has no committed artifact`, and adding a
file with an unregistered schema reports it by name. Re-run that check by hand
after changing a rule's condition; a control whose rule can be deleted without
the suite noticing is decoration.
