# References

Host-neutral contracts. Nothing here names a product, a provider, a repository
or a machine. Every schema is Draft 2020-12 and every example validates against
the schema beside it — `tests/run-all.sh` proves both on current bytes.

| File | Owns |
|---|---|
| [`product-signal.schema.json`](product-signal.schema.json) | intake contract and the producer compatibility binding |
| [`reverse-engineering-dossier.schema.json`](reverse-engineering-dossier.schema.json) | job, pain, workflow, magic moment, classified mechanisms, capability/rights graph, MVP and stop loss |
| [`problem-closure-matrix.schema.json`](problem-closure-matrix.schema.json) | one row per requirement, its oracle, its lane and its closure state |
| [`prompt-packet.schema.json`](prompt-packet.schema.json) | the envelope and the nine stage surfaces, with authority and private-reasoning both pinned false |
| [`reverse-engineering-handoff.schema.json`](reverse-engineering-handoff.schema.json) | bounded implementation packets, real edges, disjoint leases, and remaining items with owners |
| [`evidence-vocabulary.md`](evidence-vocabulary.md) | the four controlled vocabularies and every refusal code |
| [`prompt-catalogue.md`](prompt-catalogue.md) | what each prompt surface exists to refuse |

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
