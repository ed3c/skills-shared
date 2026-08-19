# References

This directory owns the host-neutral contract surfaces for `repository-entropy-reclamation`.

| File | Authority |
|---|---|
| `entropy-audit.schema.json` | Draft 2020-12 shape for an exact-subject entropy audit/apply receipt |
| `example-audit.json` | positive example used by the deterministic gate and tests |
| `UPSTREAM_LINEAGE.md` | immutable upstream source pins, concept mapping, exclusions, and licensing boundary |

The semantic authority is `../scripts/assert_entropy_audit.py`. A schema-valid document can still violate consumer, protected-boundary, Shadow, conceptual-reduction, verdict, or evidence-lane laws.
