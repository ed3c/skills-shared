# References

Host-neutral contracts. Nothing here names a product, a provider, a repository
or a machine. Every schema is Draft 2020-12 and every example validates against
the schema beside it — `tests/run-all.sh` proves both on current bytes.

| File | Owns |
|---|---|
| [`product-signal.schema.json`](product-signal.schema.json) | intake contract and the producer compatibility binding |
| [`reverse-engineering-dossier.schema.json`](reverse-engineering-dossier.schema.json) | job, pain, workflow, magic moment, classified mechanisms, capability/rights graph, MVP and stop loss |
| [`problem-closure-matrix.schema.json`](problem-closure-matrix.schema.json) | one row per requirement, its oracle, its lane and its closure state |
| [`product-closure-audit.schema.json`](product-closure-audit.schema.json) | the read-only Shadow audit: seven ordered levels over six lanes, exact-subject anchors, reopened obligations, the findings denominator, the issue delta and the public snapshot |
| [`prompt-packet.schema.json`](prompt-packet.schema.json) | the envelope and the nine stage surfaces, with authority and private-reasoning both pinned false |
| [`reverse-engineering-handoff.schema.json`](reverse-engineering-handoff.schema.json) | bounded implementation packets, real edges, disjoint leases, and remaining items with owners |
| [`external-projection-registry.schema.json`](external-projection-registry.schema.json) | a projection of Git subjects into an external document: external id, observed revision, export digest, exact Git subjects, backlinks, read-back state — and no implementation, completion, product-truth, merge or release authority |
| [`session-dispatch-request.schema.json`](session-dispatch-request.schema.json) | what would be launched: exact base commit/tree, branch and parent, disjoint lease, separate start and completion dependencies, oracles, negative controls, rollback, stop states, output paths. Pinned to `LAUNCH_REQUESTED` |
| [`session-receipt.schema.json`](session-receipt.schema.json) | what a carrier observed: the five lifecycle states as separate fields, every evidence lane reported including the unavailable ones |
| [`evidence-vocabulary.md`](evidence-vocabulary.md) | the four controlled vocabularies, every refusal code, and the pre-registered refusal classes |
| [`prompt-catalogue.md`](prompt-catalogue.md) | what each prompt surface exists to refuse |

## Contract index: required name → landed name

The names in the originating contract issue and the names on disk are not
identical. The landed names are the ones every consumer already imports by exact
string — `check_prel_contract.py` maps a schema constant to a filename, so
renaming a file to match the issue would break intake rather than document it.
The mapping is recorded here instead.

| Required name | Landed name | Why |
|---|---|---|
| `product-signal-compat.schema.json` | [`product-signal.schema.json`](product-signal.schema.json) | same contract: it carries the `compatibility` block that binds the producer and the consumed fields |
| `evidence-and-closure-vocabulary.md` | [`evidence-vocabulary.md`](evidence-vocabulary.md) | same document: evidence states, signal grades, mechanism classes, closure states and oracle lanes |
| `examples/*.json` | `references/example-*.json` and [`../examples/`](../examples/) | the compiled example chain stays beside the schemas it is byte-compared against; examples for the projection and session contracts live in `examples/` |

## Examples

[`example-product-signal.json`](example-product-signal.json) is the only
hand-authored data artifact. The next three are compiled from it and are not
edited by hand:

```text
example-product-signal.json
  → example-dossier.json          compile_prel.py --stage dossier
    → example-closure-matrix.json compile_prel.py --stage closure
      → example-handoff.json      compile_prel.py --stage handoff
```

`--check` re-compiles and byte-compares each one, so a hand edit is a red suite
rather than a second source of truth.

[`example-closure-audit.json`](example-closure-audit.json) is hand-authored:
an audit is an observation of a subject, not a projection of an upstream
artifact, so there is no compiler stage that could regenerate it. What keeps it
honest instead is that its earned levels are recomputed from its own rung states
and every anchor it names is re-hashed by `--resolve-subjects`.

[`example-prompt-packet.json`](example-prompt-packet.json) is hand-authored and
pins the sha256 of each artifact its surfaces bind to. Those digests are not
decoration: `check_prel_contract.py --resolve-subjects` re-hashes every named
artifact, so a packet pointing at bytes that moved is `STALE_SUBJECT` instead of
a surface quietly describing a subject that no longer exists.

## The compatibility binding

`product-signal.schema.json` carries a `compatibility` block naming the producer
and the exact signal fields consumed. The checker asserts every consumed field is
one this contract actually defines. A producer that renames or drops a field
therefore fails at intake, where the fix is cheap, instead of surfacing three
stages later as a slot that mysteriously graded `ABSENT`.

## The example subject

`PRODUCT-ALPHA` is a placeholder identity, not an anonymised real product. Using
a real one would put a specific vendor's observed behavior into a shared body,
where it would age without anyone owning it.
