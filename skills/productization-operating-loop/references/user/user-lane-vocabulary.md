# USER-lane vocabulary (POL, issue #424)

This is the short vocabulary note for `user-lane.schema.json`, in the same
four-part form as [`../core/controlled-vocabulary.md`](../core/controlled-vocabulary.md):
meaning, producer, consumer, never-becomes. It adds terms; it does not
re-specify the twelve lanes, the ten rungs, or `lane_state` — those stay owned
by the C0 core and are only referenced here by their exact `$defs` names.

```text
SCENARIO
  means         one named user, in one named situation, attempting one named
                piece of work
  produced by   scenario construction against a persona and a trigger event
  consumed by   the USER lane roll-up, the differentiation wedge
  never becomes a persona archetype library. A scenario is singular; a set of
                scenarios is a set of these records, not one record with a
                wider "personas" field.

PERSONA (buyer / user)
  means         two separately named roles: whoever approves or pays, and
                whoever does the work in the scenario
  produced by   scenario construction
  consumed by   procurement_path, commercial friction
  never becomes the same role by default. `relationship: SAME_PERSON` is a
                claim this schema requires evidence for, exactly like any
                other claim in this lane — it is not the resting state.

ADOPTION_STATUS
  means         whether the scenario's user actually took up the tool, versus
                said they would
  produced by   observing a second real session, or a stated intent
  consumed by   the retention/return read-back
  never becomes OBSERVED_ADOPTION on a REPORTED or CLAIMED signal. Saying "I'd
                use this" is EXPRESSED_INTEREST; only an OBSERVED_ARTIFACT of a
                real return session reaches OBSERVED_ADOPTION.

SWITCHING_COST / WILLINGNESS_TO_SWITCH
  means         what it costs to leave the incumbent tool, and whether anybody
                has actually left it
  produced by   scenario construction (cost) and observation (willingness)
  consumed by   the differentiation wedge
  never becomes CONFIRMED_SWITCH on a pain complaint about the incumbent tool.
                A `USER_INTERVIEW` reporting frustration is evidence of pain,
                not evidence that anybody moved.

TIME_TO_FIRST_VALUE
  means         elapsed time from the trigger event to the first value the
                scenario's user actually received
  produced by   a recorded session, or an estimate
  consumed by   the friction ladder, the MVP stop-loss
  never becomes MEASURED from a vendor demo or marketing script. A `SOURCE_STATEMENT`
                caps this field at ESTIMATED.

FRICTION FIELDS (setup / account-or-API-key / permission-and-trust /
data-migration / learning-cost burden)
  means         five separately reported costs an adopting user pays before
                or during first value
  produced by   scenario construction, upgraded by observation
  consumed by   the adoption friction ladder read by the differentiation wedge
  never becomes LOW by default. `permission_trust_burden` in particular
                refuses a LOW state built only on `INFERENCE` — "it's probably
                fine" is not evidence that a login or grant step was actually
                cleared.

FALSIFIER
  means         the stated way this scenario's hypothesis would be shown
                wrong, plus one concrete counterexample
  produced by   whoever writes the scenario, before any observation is made
  consumed by   whoever later checks the scenario against real behaviour
  never becomes optional. Every scenario record carries one; a hypothesis with
                no stated way to fail is not being tested by writing it down.

EVIDENCE KIND (`OBSERVED_ARTIFACT` / `USER_INTERVIEW` / `THIRD_PARTY_REPORT` /
`SOURCE_STATEMENT` / `INFERENCE`)
  means         the same five closed signal kinds product-reverse-engineering-loop
                already defines in `evidence-vocabulary.md`
  produced by   whichever act actually produced the signal — a driven session,
                a user's own account, someone else's account, a vendor's own
                claim, or a reading of other signals
  consumed by   every field in this schema through its `evidence` sub-object
  never becomes a second, incompatible evidence vocabulary. This lane reuses
                the PREL kinds by name rather than inventing new grades, so a
                claim carried between the two Skills does not need translating
                or re-arguing.
```
