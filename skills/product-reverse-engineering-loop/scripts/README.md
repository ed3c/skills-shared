# Scripts

Both scripts are zero-network and standard-library only, except for the pinned
Draft 2020-12 validator. Neither executes a model, reaches a product surface,
writes outside the path it was given, or grants merge, publication, release or
promotion authority.

## `check_prel_contract.py`

Validates one artifact. Two layers run and both always run: the schema layer
decides shape, the semantic layer decides whether evidence was laundered. The
semantic layer is deliberately defensive so it still emits its own refusal code
on an artifact the schema layer already rejected — a mutation flipping
`authority.merge` to true has to be reported as
`PROMPT_GRANTS_RESERVED_AUTHORITY`, because that code is what a Worker was told
to look for, and a bare `const` failure is not.

```bash
python3 scripts/check_prel_contract.py --artifact <artifact.json>
python3 scripts/check_prel_contract.py --artifact <artifact.json> --input <upstream.json>
python3 scripts/check_prel_contract.py --artifact <artifact.json> --resolve-subjects <dir>
python3 scripts/check_prel_contract.py --catalogue references/prompt-catalogue.md
```

`--input` compares `derived_from.digest` against the upstream file's current
bytes. `--resolve-subjects` re-hashes every `exact_subject` and `derived_from`
the artifact names anywhere in its tree, so a subject that moved or vanished is
`STALE_SUBJECT` rather than a promise nobody re-reads. `--catalogue` asserts the
prose catalogue still names every surface the schema declares.

Exits: 0 green, 2 a contract or control is red, 64 the checker could not run —
an unreadable input is never reported as a pass.

Every refusal code is listed in [`../references/evidence-vocabulary.md`](../references/evidence-vocabulary.md)
and planted as a defect by `../tests/selftest.py`.

## `compile_prel.py`

Compiles the three projections. Each output is a pure function of its input bytes
plus this file, serialized canonically, so `--check` byte-compares a committed
projection instead of trusting that somebody regenerated it.

```bash
python3 scripts/compile_prel.py --stage dossier --input <signals.json> --out <dossier.json>
python3 scripts/compile_prel.py --stage closure --input <dossier.json> --out <closure.json>
python3 scripts/compile_prel.py --stage handoff --input <closure.json> --out <handoff.json>
python3 scripts/compile_prel.py --stage <stage> --input <in.json> --out <out.json> --check
```

The compiler adds no product semantics. A slot with no admissible signal comes
out `ABSENT`; a mechanism with no technical-lane oracle comes out
`UNOBSERVABLE_MECHANISM`; a capability edge exists only where a signal declared
`depends_on`; an empty MVP scope is refused rather than emitted.

Two states it cannot produce, each on purpose. It never emits
`CLOSED_BY_ORACLE`, because compiling an oracle is not running one. It never
emits an edge between packets, because nothing in a signal set proves one
implementation consumes another's output — every compiled packet is a sibling,
and a consumer that adds an edge must name the artifact it consumes or be
refused.

Exits: 0 green, 2 the compilation is refused or a `--check` projection is stale,
64 the input is malformed.
