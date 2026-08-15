# Exact Evidence and Heuristic Calibration Boundary

This reference composes the primitive CTL evaluators admitted by PR #127. It does not replace them.

## Why this layer exists

The primitive deterministic linter proves tokenization, word-budget, and source-span mechanisms. The primitive heuristic gate proves that a caller-supplied calibration summary has an admitted shape.

Neither primitive proves that a result used the exact selected profile, ruleset, termbase, source, candidate, gold corpus, or prediction artifact. This layer closes that composition gap.

## Deterministic exact-evidence lane

`scripts/check_exact_evidence.py deterministic` requires exact SHA-256 identities for:

```text
case
profile pack
ruleset
policy
termbase entries
source bytes
candidate bytes
candidate spans
```

The evaluator also checks:

- the policy names the selected pack and ruleset bytes;
- only declared deterministic rule kinds enter the lane;
- document class selects a positive word budget;
- candidate segments cover all non-whitespace bytes without overlap;
- every TN/TV use resolves to an admitted term, exact surface, and allowed part of speech;
- S1000D/DITA-like XML remains well formed;
- explicitly protected XML nodes preserve identity, tag, text, and relative order.

Exit `0` proves only the declared deterministic bundle. Exit `2` is an evaluated document failure. Exit `64` is invalid or absent input. Exit `70` is an evaluator failure.

## Corpus-recomputed heuristic lane

`scripts/check_exact_evidence.py calibration` does not trust caller-supplied aggregate rates. It recomputes false-positive and false-negative rates from exact gold and prediction artifacts.

Each prediction artifact binds:

```text
gold corpus digest
evaluator identity and version
implementation digest
model identity and digest
execution mode
per-case labels
```

The admitted execution modes are:

```text
FIXTURE_LABEL_REPLAY
  proves the calibration mechanism only
  classifier_state = NOT_IMPLEMENTED

RECORDED_CLASSIFIER_OUTPUT
  records an exercised classifier output
  still remains CALIBRATED_HEURISTIC
```

A model identity containing `latest`, `current`, `head`, `rolling`, or `newest` is rejected.

## Authority law

```text
DETERMINISTIC failure
  vetoes final PASS

CALIBRATED_HEURISTIC PASS
  remains ADVISORY_ONLY
  cannot override deterministic evidence
  cannot create a compliance claim

SEMANTIC acceptance
  requires its own evaluator and receipt

HUMAN acceptance
  remains required for terminology admission,
  safety-critical meaning, and official compliance representation
```

## Current evidence boundary

```text
primitive tokenization and word-budget mechanisms  IMPLEMENTED
aggregate heuristic admission shape                IMPLEMENTED
exact profile/termbase/XML composition              IMPLEMENTED in this slice
corpus-recomputed calibration                       IMPLEMENTED in this slice
real heuristic classifier                           NOT_IMPLEMENTED
semantic meaning-preservation evaluator              NOT_IMPLEMENTED
official ASD-STE100 pack and vocabulary              NOT_EXERCISED
certification or official compliance                 HUMAN_ADMIT_REQUIRED
```

Fixture replay is not model evidence. A green Skill suite is not certification. A source proposal is not an official standard pack.
