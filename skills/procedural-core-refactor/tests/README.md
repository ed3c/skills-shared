# Procedural core refactor test controls

`run-all.sh` executes the positive refactor contract and Tech Lead golden-proof bundle, writes a deterministic receipt, then runs planted negative controls.

## Positive path

```text
schema syntax
→ contract + proof shape
→ semantic ownership/law/module/A-B/evidence/authority/trace checks
→ deterministic receipt
```

## Planted defects

`selftest.py` requires red results for:

- mutable baseline or historical treatment;
- dead law assertion/test route;
- domain atom moved into portable core;
- selected module without trigger or predecessor;
- unmatched real-task arms;
- fixture/static evidence promoted to live PASS;
- automation or merge authority widening;
- hidden B0 regression;
- B2 missing a tested causal dimension;
- local PASS with failed global objective;
- cleanup residue;
- CI PASS without an exact run;
- proof head absent from traceability.

The suite is zero-network. It does not invoke providers, Workers, Git Town, Forgejo, GitHub publication, merge or production promotion.
