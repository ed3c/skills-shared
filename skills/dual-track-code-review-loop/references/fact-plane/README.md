# DTCR deterministic fact-plane contract

Owner: Issue #519, atom `D1-C`.

This directory freezes the provider-neutral interface consumed by the later
Tree-sitter, SCIP, SQLite and optional contract-compatibility adapter siblings.
It does **not** implement any provider and it does not claim a complete semantic
model of a repository.

## Read order

1. `../../AGENTS.md`
2. `../../README.md`
3. `../../SKILL.md`
4. this file
5. `exact-source-subject.schema.json`
6. `provider-observation.schema.json`
7. `fact-bundle.schema.json`
8. `fact-plane-receipt.schema.json`
9. `contract-cases.json` and `check_contract.py`
10. exact Issue/PR/head/receipt

## Contract flow

```text
exact repository commit/tree
        ↓
provider observation
  executable/version/config/input digest
  warnings/omissions/coverage ceiling
        ↓
normalized fact bundle
  syntax / symbol / occurrence / relationship / dependency / contract facts
        ↓
bounded blast-radius projection
        ↓
fact-plane receipt
        ↓
violation nomination / review compiler
```

## Hard laws

```text
SYNTAX_MATCH != SEMANTIC_PROOF
PARTIAL_INDEX != COMPLETE_GRAPH
OCCURRENCE_ENCLOSING_RANGE != GUARANTEED_CALL_EDGE
SQLITE_LEDGER != SOURCE_OR_GIT_TRUTH
CONTRACT_CHECK_PASS != DEPLOYMENT_SAFETY
PROVIDER_PASS != TASK_PASS
PROVIDER_AVAILABLE != PROVIDER_VERIFIED
```

Every fact binds an exact repository/commit/tree and carries provenance. File
facts additionally bind a repository-relative path and blob identity. Provider
observations carry their own executable/version/config/input identity and must
report warnings and omissions explicitly.

## Completeness vocabulary

```text
EXACT_FOR_DECLARED_DENOMINATOR
PARTIAL
UNKNOWN
NOT_APPLICABLE
```

`EXACT_FOR_DECLARED_DENOMINATOR` means only that every item in the named
*declared denominator* was processed. It never means universal semantic
coverage. Heuristic provenance may not use that value.

## Deterministic contract verifier

`check_contract.py` owns the cross-field invariants that Draft 2020-12 schemas
cannot compare directly. Its committed denominator is in `contract-cases.json`:

```text
4 schema files
4 positive examples
9 schema refusal controls
9 own-guard knockout checks
4 schema-valid semantic mutations
```

The semantic mutations refuse at least:

```text
EXACT_COVERAGE_COUNT_MISMATCH
PASS_WITH_NONZERO_EXIT
PASS_RECEIPT_WITH_FAILED_CHECK
BLAST_RADIUS_EXCEEDS_BUNDLE_COVERAGE
```

Run from a checkout that already has the pinned JSON Schema validator:

```bash
python3 skills/dual-track-code-review-loop/references/fact-plane/check_contract.py
```

A local green run is not hosted CI arrival and does not release provider
siblings. #537 owns the common DTCR suite/CI arrival; #519 owns D1-C admission.

## Adapter siblings after D1-C freeze

```text
D1-TS    syntax/parser observations
D1-SCIP  compiler/index symbol and relationship observations
D1-SQL   canonical event/edge ledger and bounded recursive traversal
D1-BUF   optional contract compatibility observations
```

They remain siblings unless one consumes exact unmerged bytes produced by
another. Availability of a binary is start readiness only.

## Evidence ceiling

This contract can establish only interface/schema consistency on its exact
subject. Provider execution, graph correctness, blast-radius adequacy, applied
refactoring, independent full-method review, registry admission, merge, release
and production remain `NOT_IMPLEMENTED`, `NOT_EXERCISED`, or
`HUMAN_ADMIT_REQUIRED` in their owning lanes.
