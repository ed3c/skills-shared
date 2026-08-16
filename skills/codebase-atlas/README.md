# `codebase-atlas`

Evidence-driven isometric repository atlas generator.

## Purpose

Turn a repository into one stable, self-contained interactive HTML architecture map with repository-grounded counts, directed flows, structure drill-downs, inspector tabs, trace stepping, zoom/pan controls, and deterministic screenshot states.

## Directory contract

```text
skills/codebase-atlas/
├── README.md
├── SKILL.md
├── references/
│   └── atlas-template.html
├── scripts/
│   └── verify_atlas.py
└── evals/
    ├── coverage-report.json
    └── share-safety-report.txt
```

`SKILL.md` owns the generalized procedure and hard gates. `references/` owns the reusable renderer contract. `scripts/` owns deterministic runtime checks. `evals/` contains replayable reference receipts from the admitted implementation; they are evidence fixtures, not consumer runtime truth.

## State machine

```text
REPOSITORY_SCAN
  -> FACT_INVENTORY
  -> DATA_MODEL
  -> FIRST_RENDER
  -> VALIDATE
  -> SCREENSHOT_STATE_MATRIX
  -> VISUAL_REPAIR_LOOP
  -> SHARE_SAFETY
  -> PASS

Any failed deterministic gate -> REPAIR -> VALIDATE
Unknown repository fact -> NOT_MEASURED, never guessed
```

## Data flow

```text
repo files/manifests/tests/runtime receipts
        |
        v
measured subsystem inventory
        |
        v
single AtlasData object
        |
        +--> left rail
        +--> top metadata
        +--> isometric structures
        +--> edges / payload dots
        +--> right inspector
        +--> canonical trace
        |
        v
self-contained HTML
        |
        +--> validator / Playwright states
        +--> coverage report
        +--> share-safety scan
```

## Evidence boundary

A consumer run may claim `PASS` only after executing the exact generated artifact against the deterministic checks. The checked-in reference reports demonstrate that the reusable engine and verification method were exercised, but they do not certify a future consumer repository or generated atlas.

Use the repository-wide evidence vocabulary:

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
```

## Composition

This Skill composes naturally with:

- `repository-capability-audit` for truth-grounded capability claims;
- `truth-verify-loop` / `external-verify` for independent evidence checks;
- `html-for-decisions` when the atlas is one evidence surface inside a larger decision artifact;
- `spatial-loop-systems-engineering` when system invariants and runtime substrate limits must be recovered before drawing;
- delivery Skills only after implementation evidence is complete.

It does not own Git branches, PRs, remote mutation, consumer paths, secrets, or live deployment state.
