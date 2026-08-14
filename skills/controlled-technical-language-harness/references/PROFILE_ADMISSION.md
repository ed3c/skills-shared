# Profile admission

Host-neutral rules for admitting a controlled-language profile. They apply to
any standard, not only Simplified Technical English.

## The claim a profile makes

A pack reference is a claim about **which authority the output can be traced
to**. A reader who sees a named standard edition reasonably concludes the rules
came from that standard. The schema in
[`../../../evals/schema/standard-pack-reference.schema.json`](../../../evals/schema/standard-pack-reference.schema.json)
proves a pack is well-formed; it cannot prove the claim is true.

These rules cover that gap.

## Rules

1. **Name only what you hold.** A pack may use an official designation — the
   standard's name, an issue or edition number, the standards body as authority
   — only when `source.classification` is `OFFICIAL_STANDARD` and the source is
   an artifact that was obtained, with an exact locator and digest.
2. **An edition is immutable.** `latest`, `current`, `newest`, `rolling` and
   `HEAD` are refused. A pack whose edition can change meaning without its
   digest changing is not a pin.
3. **An official pack must be reachable.** Its locator resolves over HTTP(S).
   An official claim a reader cannot follow is not checkable.
4. **Committing bytes needs a grant.** `content_mode: VENDORED` requires
   `redistribution_allowed` true and `human_legal_review` `ADMITTED`. A standard
   supplied free of charge on request is not thereby redistributable.
5. **A ruleset digest binds a ruleset that exists.** The digest must match the
   file present, and the ruleset's own provenance must agree with the pack's
   source classification.
6. **Terminology and compliance stay Human-owned.** Technical Name and
   Technical Verb admission are contract-level constants, and a compliance claim
   is always `HUMAN_ADMIT_REQUIRED`.
7. **A profile stays optional.** The core keeps a `PROFILE_ABSENT` state, and
   every profile module states when it must *not* be loaded. A profile that
   cannot be absent has become a core dependency.
8. **A module adds, never relaxes.** A module may tighten a rule. It may not
   relax Human Admit, skip the deterministic lane, let advisory output override
   a deterministic result, or widen the privacy lane.

## Promotion

Promoting an approximation to an official pack produces a **new pack**, with a
new `pack_id`. It is not an edit of the approximation's fields. Editing an
existing pack's edition to name an official standard is exactly what rule 1
refuses, and it is refused whether or not the editor believed the rules matched.

## Enforcement

```bash
python3 scripts/check_profile_admission.py --root <skill-dir>
python3 scripts/check_profile_admission.py --root <skill-dir> --selftest
```

`--selftest` plants one defect per rule above and requires each to be refused,
so a rule that stops biting is reported rather than assumed.
