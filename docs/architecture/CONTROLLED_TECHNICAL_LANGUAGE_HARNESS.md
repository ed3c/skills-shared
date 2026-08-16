# Controlled Technical Language Harness — Contract Foundation

> Status: CTL 01–06 merged; CTL 07 (consumer binding) open in `ed3c/bettor-arena#83`; CTL 08 (convergence index, `#133`) not started because its prerequisite has not merged. No language checker, model, parser, official dictionary, consumer binding, or compliance claim is activated by this document.
>
> Current implementation state is owned by [`skills/controlled-technical-language-harness/SKILL.md`](../../skills/controlled-technical-language-harness/SKILL.md), not by this file. This document owns architecture, evidence law, and the Stack ledger.

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

[`skills/controlled-technical-language-harness/`](../../skills/controlled-technical-language-harness/README.md) landed with CTL 02 and owns the portable procedure. Domain profiles, parsers, privacy routes, and document formats stay trigger-selected modules under that directory.

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

## What no merged slice proves

Per-mechanism `IMPLEMENTED` / `NOT_IMPLEMENTED` / `NOT_EXERCISED` state is owned by
[`skills/controlled-technical-language-harness/SKILL.md`](../../skills/controlled-technical-language-harness/SKILL.md)
and its `tests/run-all.sh` exits. Copying that list here would give it a second
place to go stale. What this document owns is the set of claims that no green
control in this repository can ever produce:

```text
current official ASD-STE100 vocabulary   ABSENT — the specification is not held here
project TN/TV termbase                   fixture only
consumer repository binding              NOT_IMPLEMENTED here — CTL 07 owns it
certification or official compliance     NOT_CLAIMED
Human semantic approval                  fixture identity only
```

Fixture Human receipts test contract shape. They are not real Human approval. A
green suite proves that planted defects were refused; it does not prove that any
real manual was checked against any real standard.

## Molecular Stack ledger

A branch edge represents consumed unmerged bytes. Path-disjoint leaves remain siblings. A convergence branch is not created until required leaves are admitted and merged.

Merged subjects below are commits on `ed3c/skills-shared` `main` and are immutable. Open rows carry no commit, because an open PR head is not a release identity.

| Slice | Issue | PR | Merge commit | State |
|---|---|---|---|---|
| CTL 01 contract foundation | `#116` | `#117` | `a711316ec6ab50a952e2ec3df64c7feea2d181b1` | Merged |
| CTL 01 hotfix — false-PASS paths | `#124` | `#125` | `65c72f7ab67af49d6237245eb64298cf62c11e14` | Merged |
| CTL 02 Harness core and STE profile | `#118` | `#126` | `061ff5e479e0f4595def11ec08bc4ddff8959708` | Merged |
| CTL 03 deterministic evaluators | `#119` | `#127` | `edfa2922856a457167b56d32a73d679577718492` | Merged |
| CTL 03 hardening — exact profile subjects | `#129` | `#137` | `6764c67e7df9206dbc36f731f38f4c7dd252d51d` | Merged |
| CTL 03 hardening — calibration controls | `#129` | `#139` | `8e13b3ab9a2e34b75384c8fbc87ea5f8a3249f22` | Merged |
| CTL 04 intent-promotion and writeback gate | `#120` | `#130` | `8c040362eaad3fdf8d81a50cb594d15a7de8feb6` | Merged |
| CTL 04B authority substitutions | `#134` | `#138` | `c737e43d2cb6713a3fbbfd1f8d54c3b81b1870a7` | Merged |
| CTL 04C external authority readback | `#141` | `#143` | `a7b278aba8bdf744e901f605ea07b09e3b468e60` | Merged |
| CTL 05 document format and privacy routing | `#121` | `#131` | `e4f22e887bd1dfaea9cf673d75bb0a19a30d0ca6` | Merged |
| CTL 06 integrated A/B canary | `#132` | `#140` | `47cbb259c0157535d6f40b703b487e225a1a9de1` | Merged |
| CTL 06B A/B against external authority bytes | `#144` | `#152` | `b3d47948feb6e2d44d84261354117aecfaa4f5dc` | Merged |
| CTL 07 consumer binding and canaries | `ed3c/bettor-arena#83` | none | n/a | Open — different repository, different owner |
| CTL 08 convergence index | `#133` | none | n/a | Blocked on CTL 07 |

`#142` was an alternative Intent Promotion gate and was closed unmerged; it is not part of any subject above.

CTL 08 cannot be opened yet. Its own contract forbids creating `ctl/08-convergence-index` before every prerequisite merges, and a convergence PR may not repair an implementation leaf, so the unmet condition returns to its owner in `bettor-arena`.

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
