# Controlled Technical Language Harness — Contract Foundation

> Status: CTL 01–06B merged here. CTL 07A merged in `ed3c/bettor-arena` and closed its issue; CTL 07B bytes landed there while its issues stay open, so the CTL 07 parent `ed3c/bettor-arena#83` is still open. CTL 08 (`#133`) has recorded what is admitted — merged subjects, the selected bundle, the rollback subject, routes and the precondition audit below — and cannot be admitted itself while its prerequisite is open. No language checker, model, parser, official dictionary, consumer binding, or compliance claim is activated by this document.
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

Merged subjects below are immutable commits, and each is recorded with the tree it produced: a commit identifies the change, a tree identifies the bytes a consumer can pin. Rows are on `ed3c/skills-shared` unless the issue column names another repository. Open rows carry no commit, because an open PR head is not a release identity.

| Slice | Issue | PR | Merge commit | Merged tree | State |
|---|---|---|---|---|---|
| CTL 01 contract foundation | `#116` | `#117` | `a711316ec6ab50a952e2ec3df64c7feea2d181b1` | `9067edb0a2dedc8d88188f3f4cad0aa111c000b9` | Merged |
| CTL 01 hotfix — false-PASS paths | `#124` | `#125` | `65c72f7ab67af49d6237245eb64298cf62c11e14` | `f36307edf8596818207a9ddf12ac6de6c41a12ad` | Merged |
| CTL 02 Harness core and STE profile | `#118` | `#126` | `061ff5e479e0f4595def11ec08bc4ddff8959708` | `b6d5631af9a4ae128ae19be9d58192c4b9b4feec` | Merged |
| CTL 03 deterministic evaluators | `#119` | `#127` | `edfa2922856a457167b56d32a73d679577718492` | `299516fd0f175473cb14c14e7915ce31b8571b85` | Merged |
| CTL 03 hardening — exact profile subjects | `#129` | `#137` | `6764c67e7df9206dbc36f731f38f4c7dd252d51d` | `c4123e3b9685412257db4627763fbd1b768567c8` | Merged |
| CTL 03 hardening — calibration controls | `#129` | `#139` | `8e13b3ab9a2e34b75384c8fbc87ea5f8a3249f22` | `9c085842e70f95648916365705be33a4f0989bd7` | Merged |
| CTL 04 intent-promotion and writeback gate | `#120` | `#130` | `8c040362eaad3fdf8d81a50cb594d15a7de8feb6` | `1173b33d6a80a1ee012a6375b1ce857398c24bb8` | Merged |
| CTL 04B authority substitutions | `#134` | `#138` | `c737e43d2cb6713a3fbbfd1f8d54c3b81b1870a7` | `d37f3ce18204b5d9e93b4351a6925fe195aa6df3` | Merged |
| CTL 04C external authority readback | `#141` | `#143` | `a7b278aba8bdf744e901f605ea07b09e3b468e60` | `5fd73a0d671a3a091f34bed0e9c242f6785014ae` | Merged |
| CTL 05 document format and privacy routing | `#121` | `#131` | `e4f22e887bd1dfaea9cf673d75bb0a19a30d0ca6` | `cb80dc6bf6948b07b4a32abea748b422f8778468` | Merged |
| CTL 06 integrated A/B canary | `#132` | `#140` | `47cbb259c0157535d6f40b703b487e225a1a9de1` | `8d9a3a0b5f18eb95a3ec8e6ac74edfbe46a6f197` | Merged |
| CTL 06B A/B against external authority bytes | `#144` | `#152` | `b3d47948feb6e2d44d84261354117aecfaa4f5dc` | `8b7a44fb080d290135223e372d77825589fdfe3a` | Merged |
| CTL 07 consumer binding and canaries | `ed3c/bettor-arena#83` | none | n/a | n/a | Open — different repository, different owner |
| CTL 07A immutable consumer binding | `ed3c/bettor-arena#84` | `ed3c/bettor-arena#85` | `a3bee10b1e8ffc3c85bad518a18d044915a415bb` | `5f5b1291f1e3ef436743c10750ad15d4a73046d6` | Merged there; issue closed |
| CTL 07B sealed projection materializer | `ed3c/bettor-arena#88` | none | `0b0d1a5d571dfdda89d655e1a4fd619ad8d27d55` | `4cfb32d6c5daa796b65f357a47cd0b75816ad299` | Bytes on their `main`; issue open |
| CTL 07B paired carrier canaries | `ed3c/bettor-arena#108` | none | n/a | n/a | Open — the lane CTL 08 waits on |
| CTL 08 convergence index | `#133` | none | n/a | n/a | Recording only; not admitted |

`#142` was an alternative Intent Promotion gate and was closed unmerged; it is not part of any subject above.

The two `bettor-arena` commits are recorded here because they are immutable and this repository is the selected bundle's producer. They are not this repository's evidence: their owning checks, their issue states and their canary lanes belong to `bettor-arena`. The states above were read on 2026-08-18 from a local clone of that repository (`git log`/`git rev-parse`) and from read-only `gh issue` reads; a later read is authoritative over this line.

CTL 07 landing bytes is not CTL 07 being admitted. `#84` closed, `#88` and `#108` did not, and `#108` is the leaf that owns the paired physical carrier canaries — the precondition CTL 08 cannot supply for itself. A convergence PR may not repair an implementation leaf, so that condition stays with its owner in `bettor-arena` and CTL 08 records the gap instead of absorbing it.

## CTL 08 convergence record

`#133` owns this section. Convergence records admitted evidence and creates none,
so every claim below names where it was read from. A line with no source is a
line this repository cannot make.

```text
skills-shared subjects     this tree, `git log --no-walk` and `git rev-parse` over the CTL commits
bettor-arena subjects      READ_FROM_LOCAL_CHECKOUT of a sibling clone of that repository
bettor-arena issue states  read-only `gh issue view` / `gh issue list`, 2026-08-18
consumer binding digests   that clone's `.skill-bindings/controlled-technical-language-harness/binding.json`
digest agreement           `git rev-parse <commit>:<path>` here, compared against that file
proof ceiling              `skills/skill-refactor-proof-loop/references/golden-proof-registry.json`
cold-start navigation      bounded local carrier probes, recorded under "Cold-start route findings"
```

### Selected bundle and rollback subject

The consumer pinned a commit, not a branch: `binding.json` carries
`"mutable_ref": null`, so no reading of `main` can move what it selected.

```text
selected   ed3c/skills-shared@b3d47948feb6e2d44d84261354117aecfaa4f5dc   (CTL 06B)
           commit tree      8b7a44fb080d290135223e372d77825589fdfe3a
           skill tree       2c4582c1c0d1db27c318fbd2a1ed3957f4d2cb46
           SKILL.md blob    5c1932161e9d4164b013f0e2b1f7dc7830021c5d
           evals.json blob  4a8f35732a283550bdce6730504f5b9974513c9e
           pack blob        a3cc85d63c6ebec867bd27f01ba7d94deb399644
           authority comp.  d3939b69 reference / d742f62f scorer / 448ad77f selftest

rollback   ed3c/skills-shared@47cbb259c0157535d6f40b703b487e225a1a9de1   (CTL 06)
           commit tree      8d9a3a0b5f18eb95a3ec8e6ac74edfbe46a6f197
           skill tree       95f32efc63e718cfc5b7663333cee1a35ed18b5a
           SKILL.md blob    5c1932161e9d4164b013f0e2b1f7dc7830021c5d
           evals.json blob  c7e07c9f980f1d9b3b5ce9d42a1f01ee1d2f866f
           authority comp.  ABSENT — the layer did not exist at that commit
```

Every digest above was re-derived in this tree with `git rev-parse` and matched
the consumer's file exactly. Selected and rollback are distinct commits and
distinct skill trees, and their **`SKILL.md` blob is identical**: 06B changed the
evaluator composition around the body, not the body. A reader who compared only
the entrypoint blob would conclude the two bundles were one bundle, which is why
the skill tree and `evals.json` blob are recorded beside it.

The selected skill tree is not the current one. `main` has moved past it — the
`#165`, `#170`, `#354` and `#344` commits each changed that directory — and the
pin still resolves because it names a commit. A consumer that had pinned `main`
would have moved with those commits without deciding to.

`5c193216…` is also the treatment registered as `B2_AB_VALIDITY_REPAIRED` in the
golden proof registry, so the selected entrypoint bytes and the proven bytes are
the same bytes rather than two things that happen to agree.

### Precondition audit

| Precondition (`#133`) | State | Owner of the gap |
|---|---|---|
| exact merge commit/tree for CTL 01–06 | `PASS` | recorded in the ledger above |
| exact bettor-arena consumer merge commit/tree | `PASS` for CTL 07A; `PASS` for the CTL 07B bytes | recorded in the ledger above |
| every owning workflow result bound to its admitted head | `ABSENT` from here | GitHub Actions metadata; the traceability index records the per-leaf check that ran at each PR head |
| immutable selected Skill/profile/ruleset/schema/evaluator/fixture digests | `PASS` | recorded above and re-derived here |
| immutable consumer projection digests for Claude and Codex | `NOT_IMPLEMENTED` | `ed3c/bettor-arena` — its binding still records both projections as `NOT_IMPLEMENTED` |
| A/B with full condition denominator and declared model/harness/environment/seed | `NOT_EXERCISED` as a live result | the mechanism and its validity gate are implemented and exercised on fixtures here; no physical run exists in either repository |
| rollback bundle distinct from the selected candidate | `PASS` | distinct commits and distinct skill trees, above |
| zero active overlapping path leases | `PASS` for this leaf's paths | this change touches route and record documents only |
| fresh Claude and Codex cold-start navigation audit | `PASS` for this repository's routes, n=1 per carrier | recorded below; it is **not** the consumer canary `ed3c/bettor-arena#108` owns |
| all remaining evidence gaps explicitly classified | `PASS` | this table plus "What no merged slice proves" |

Two preconditions are unmet and neither may be repaired here. The consumer
projection digests and the paired physical carrier canaries belong to
`ed3c/bettor-arena#83` and its open leaf `#108`. Until those land, CTL 08 is a
record, not an admission: no release identity, no capability unlock, and no
Human Admit follow from this section.

### Cold-start route findings

The audit was run rather than asserted, and it was run against the only thing
this leaf can audit: this repository's own routes. Machine record:
[`../../skills/controlled-technical-language-harness/evals/receipts/ctl-08-cold-start.receipt.json`](../../skills/controlled-technical-language-harness/evals/receipts/ctl-08-cold-start.receipt.json).

Each carrier was given one question — *following only the documented routes,
which file owns the controlled-language architecture, evidence law and merged
ledger?* — with directory listing and search withheld, so a route had to carry it.

```text
claude  PRE   REACHED   the answer was correct before any route was added
claude  POST  REACHED
codex   POST  REACHED
codex   PRE   NOT_EXERCISED   the carrier was reached after the PRE tree was gone
```

**The PRE run falsified the reason this leaf expected to add a route.** The
prediction was that a fresh reader could not reach this document, because no
route table names it. The reader reached it anyway: `docs/INDEX.md` routes the
traceability index, and that index links here in prose. So the defect is not
reachability. The defect is that the reachability was accidental — it depended on
a reader opening a *traceability* index while looking for *architecture*, and on
a prose sentence nobody had declared to be a route.

That is the gap now closed. `docs/architecture/AGENTS.md` states that a stable
architecture topic is registered in `docs/INDEX.md`; the controlled-language topic
was in neither that index nor that router's own trigger table. Both now name it,
and the root README links it from the sentence that mentions the gates.

The denominator is one run per cell, three cells observed of four planned. One
run is one observation: it does not measure whether either carrier would answer
the same way again, and neither carrier's result says anything about the other.
None of it is the consumer canary — that runs in `ed3c/bettor-arena`, against a
different tree, and `#108` owns it.

### What this record does not establish

An index of admitted evidence is still not evidence. Nothing here establishes
official ASD-STE100 certification, proprietary-manual safety, production privacy
authorization, a physical A/B result, or generalization beyond the exact tested
carriers and documents. Release promotion, capability unlock, compliance
representation, merge and rollback remain Human-owned.

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
