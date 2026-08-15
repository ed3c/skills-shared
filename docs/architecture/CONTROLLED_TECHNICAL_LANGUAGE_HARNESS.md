# Controlled Technical Language Harness — Contract Foundation

> Status: Phase 1 contract foundation. No language checker, model, parser, official dictionary, consumer binding, or compliance claim is activated by this document.

## Source proposal

This architecture responds to the user-supplied source proposal:

```text
file: STE100 檢查與改寫 LLM 應用.pdf
Google Drive file id: 1vqFNBQmCwh9xgziZxlO0oYk6fZQg9rQ_
sha256: d919a887f9bc8acda76ad6350276059e4c4f71a739f048a47626c686d7175578
size: 3036053 bytes
classification: SOURCE_PROPOSAL
```

The proposal describes structured output, deterministic checks, terminology injection, semantic rewriting, bounded feedback, and Human review. Those ideas are inputs. They are not repository truth, an official standard pack, executable evidence, or certification.

## Goal

Create a portable contract layer that can later support controlled technical language profiles without coupling the repository to one standard, parser, model, provider, or consumer.

```text
exact source subject
→ request contract
→ standard-pack reference
→ project termbase references
→ typed evaluator lanes
→ typed violations
→ bounded repair receipts
→ completion decision
```

The foundation extends the existing `intent-bound-constraint/v1` control plane. It does not create another meta-evaluator authority.

## Directory ownership

```text
evals/schema/
  public interchange shapes

evals/fixtures/controlled-language/
  safe positive fixtures and Intent-Bound registration

scripts/check_controlled_language_contracts.py
  dependency-free cross-file semantic closure

tests/test_controlled_language_contracts.py
  positive, hollow, and mutation controls

docs/architecture/CONTROLLED_TECHNICAL_LANGUAGE_HARNESS.md
  architecture, state machine, evidence boundary, and next Stack
```

A future `skills/controlled-technical-language-harness/` directory will own the portable procedure only after these contracts are admitted. Domain profiles, parsers, privacy routes, and document formats will remain trigger-selected modules.

## Contract set

| Contract | Responsibility |
|---|---|
| `controlled-language-request/v1` | exact input subject, document class, operation, profile, termbase, privacy, requested evidence, bounded repair |
| `controlled-language-standard-pack-reference/v1` | source authority, edition, digest, license/redistribution policy, ruleset identity, terminology and compliance boundaries |
| `controlled-language-termbase-entry/v1` | append-only TN/TV candidate and admission history with exact source and Human receipt |
| `controlled-language-violation/v1` | constraint and intent IDs, evidence class, exact source span, severity, status, Human waiver |
| `controlled-language-receipt/v1` | exact request/profile/termbase identities, separated evaluator runs, violation counts, repair history, Human state, final claim/status |

The fixture Intent-Bound contract protects:

```text
MI-CTL-TRUTH
MI-CTL-EVIDENCE
MI-CTL-PRIVACY
MI-CTL-HUMAN
```

## Evidence classes

```text
DETERMINISTIC
  schema, exact digest, token count, lexical membership, XML validity,
  source span, stable command exit

CALIBRATED_HEURISTIC
  POS, passive voice, noun cluster, pronoun ambiguity, action count;
  requires an explicit calibration reference

SEMANTIC
  meaning preservation, warning order, omitted preconditions,
  introduced assumptions; never overrides deterministic failure

HUMAN
  terminology admission, safety-critical acceptance, proprietary-pack
  admission, external confidential processing, official compliance claim
```

`PASS` is not an average. A requested lane that is `FAIL`, `BLOCKED`, `NOT_EXERCISED`, or `SKIPPED_BY_POLICY` prevents final `PASS`.

## State machine

```text
REQUEST_ABSENT
→ REQUEST_BOUND
→ PROFILE_BOUND
→ TERMBASE_BOUND
→ PRIVACY_ADMITTED
→ EVALUATING
    ├── DETERMINISTIC_FAIL → BLOCKED or bounded REPAIR
    ├── HEURISTIC_RESULT   → candidate evidence
    ├── SEMANTIC_RESULT    → candidate evidence
    └── HUMAN_REQUIRED     → HUMAN_ADMIT_REQUIRED
→ ASSERTING_EXACT_RECEIPT
→ PASS | FAIL | BLOCKED | HUMAN_ADMIT_REQUIRED
```

Repair uses the repository-wide diagnostic-reflection receipt. It records only auditable observations, selected allowlisted repair, expected metric delta, actual metric delta, and stop decision. It does not request or store private chain-of-thought.

## Hard laws in Phase 1

1. Bind request, profile, termbase, and receipt to exact bytes with SHA-256.
2. Require `DETERMINISTIC` evidence for every request.
3. Keep all four evidence classes separate.
4. Let deterministic failure veto semantic or Human advisory success.
5. Treat `NOT_EXERCISED` and `SKIPPED_BY_POLICY` as non-PASS states.
6. Keep `RESTRICTED` text in `LOCAL_ONLY` execution with network disabled.
7. Require Human approval before an external lane processes confidential text.
8. Require Human receipts before TN/TV state becomes `ADMITTED`.
9. Require `NO_APPROVED_GENERAL_VERB` before a Technical Verb is admitted.
10. Require Human review before Warning or Caution text receives final `PASS`.
11. Require a distinct Human receipt before `OFFICIAL_COMPLIANCE` can be represented.
12. Stop repair after measured no improvement or retry exhaustion.
13. Keep standard-pack bytes reference-only when redistribution is not admitted.
14. Do not persist private reasoning fields.

## What Phase 1 does not prove

```text
real ASD-STE100 profile                  NOT_IMPLEMENTED
current official vocabulary             ABSENT
project TN/TV termbase                   fixture only
spaCy or another parser                  NOT_IMPLEMENTED
heuristic calibration                    NOT_EXERCISED
LLM rewrite                              NOT_IMPLEMENTED
meaning-preservation evaluation          NOT_EXERCISED
S1000D / DITA parsing                    NOT_IMPLEMENTED
confidential document route              NOT_EXERCISED
consumer repository binding              NOT_IMPLEMENTED
certification or official compliance     NOT_CLAIMED
Human semantic approval                  fixture identity only
```

Fixture Human receipts test contract shape. They are not real Human approval.

## Planned molecular Stack

```text
main
└── ctl/01-contract-foundation       this slice
    ├── ctl/02-ste-profile           profile metadata and Human boundaries; no dictionary vendoring
    ├── ctl/03-deterministic-linter  exact, dependency-owned checks and calibration interface
    ├── ctl/04-intent-promotion      ADMITTED/CANONICAL writeback contract
    └── ctl/05-document-privacy      S1000D/DITA and privacy-routing modules

required leaves admitted and merged
└── ctl/06-integrated-ab-canary
    └── ctl/07-consumer-binding
        └── ctl/08-convergence-index
```

A branch edge represents consumed unmerged bytes. Path-disjoint leaves remain siblings. A convergence branch is not created until required leaves are admitted and merged.

## Next-slice admission requirements

A future Skill or profile slice must consume these contracts and add:

- one exact profile identity and rollback identity;
- trigger and non-trigger cases;
- positive, hollow, mutation, and calibration controls;
- evaluator ownership and stable exits;
- privacy route and source-readback behavior;
- no official vocabulary bytes unless redistribution and legal admission are proven;
- no provider or model as a mandatory portable-core dependency;
- explicit remaining `ABSENT`, `NOT_IMPLEMENTED`, and `NOT_EXERCISED` states;
- Human Admit for safety, terminology, official representation, merge, release, and rollback.
