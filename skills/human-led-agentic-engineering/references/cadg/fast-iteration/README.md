# Shadow CADG Fast Iteration Contract

This directory adds an operating profile over `cadg-packet/v1`; it does not define a second packet format and does not create an eighth execution graph.

## Hard boundary

```text
Portfolio execution plane
  G1–G7 -> ready waves -> Workers -> Stack PR -> CI -> closure

                           | append-only observations
                           v

Shadow CADG observability plane
  CTX -> ASM -> DEC -> DELTA -> EV
```

`CADG is not G8.` Event order MUST NOT manufacture start/completion dependencies, Git ancestry, path/resource leases, queue order, merge order, publication order, or closure edges.

## Modes

- `OFF`: policy explicitly declines capture; no implied evidence.
- `OBSERVE`: portable default recommendation. Incomplete causal chains are retained and reversible work continues.
- `WARN`: emit bounded findings without blocking while the named transition is reversible.
- `GATE`: block only the named transition when one of the four blocker IDs applies; unrelated ready waves remain eligible.

## Capture tiers

```text
T0_ROUTINE              no CADG object or typed NOT_APPLICABLE
T1_DELTA_EV             DELTA + EV only
T2_INCREMENTAL_CAUSAL   incremental CTX + ASM + DEC + DELTA; EV may arrive later
T3_COMPLETE_GATE        complete exact-subject packet at a named irreversible/high-risk boundary
```

A Worker MUST NOT fabricate missing CTX/ASM/DEC fields retrospectively. `UNKNOWN`, partial causal chains, and `INSUFFICIENT_EVIDENCE` are valid.

## Only four synchronous blockers

```text
CADG-FI-001 STALE_OR_WRONG_SUBJECT
CADG-FI-002 DUPLICATE_CANONICAL_STATE_WRITER
CADG-FI-003 AUTHORITY_OR_IRREVERSIBLE_EFFECT_WIDENING
CADG-FI-004 BLOCKING_ASSUMPTION_AT_IRREVERSIBLE_BOUNDARY
```

A blocker attaches to one `transition_boundary`. It never blocks unrelated ready waves. Existing private-reasoning/secret refusal remains an artifact-safety failure, not a scheduler dependency.

## Late evidence and compaction

Late `EV` may disposition an earlier `ASM` by stable ID. Compaction MAY produce a current summary but MUST retain failed, stale, cancelled, superseded, contradictory and falsified paths in the denominator.

## Cost observations

Cost fields are evidence, not universal SLAs. Report observed/derived/estimated/unknown provenance for:

```text
critical_path_seconds_added
tool_calls_added
ci_jobs_added
metadata_bytes
warnings
blocks
false_blocks
real_corrections
causal_questions_answerable
unverifiable_or_retrospective_declarations
```

Portable recommendation at this interface stage is `OBSERVE` as a hypothesis only. #592 replay decides whether that recommendation survives evidence.