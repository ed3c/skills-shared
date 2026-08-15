# Multi-Agent Runtime Contract Tests

`verify.sh` runs `verify.py` against the positive fixture in `fixtures/` and then
plants topology, path/resource lease, DAG, budget, Shadow, result, evidence, and
merge-boundary defects. Each planted defect must turn the deterministic checker
red with a stable error class.

The suite also proves that:

- an absent budget profile can admit only a one-Worker `SINGLE_BUILDER` fallback;
- absent input exits `64`, distinct from semantic contradiction exit `2`;
- schema-invalid state vocabulary is refused rather than normalized silently.
