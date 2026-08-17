# Executable refactor assertions

`check_refactor_contract.py` is the owning zero-network gate for the portable refactor contract and optional golden proof.

## Inputs

```text
references/refactor-contract.schema.json
references/example-refactor-contract.json
references/golden-proof.schema.json
references/tech-lead-golden-proof.json
repository files named by law/module routes
```

## Validation DAG

```text
contract JSON
→ Draft 2020-12 shape
→ treatment/baseline immutability
→ exclusive ownership map
→ exact PCR-LAW set
→ law → assertion → test reachability
→ module trigger/predecessor/fallback checks
→ matched A/B and evidence ceiling
→ authority and trace roots

optional golden proof
→ Draft 2020-12 shape
→ treatment identity reconciliation
→ old-strength and B0-regression retention
→ structural score consistency
→ matched synthetic real-task closure
→ live-evidence non-promotion
→ exact issue/PR/head/CI trace
```

## Command

```bash
python3 scripts/check_refactor_contract.py \
  --contract references/example-refactor-contract.json \
  --proof references/tech-lead-golden-proof.json \
  --receipt /tmp/procedural-core-refactor-receipt.json
```

## Exit contract

```text
0   contract and supplied proof passed the named deterministic gates
2   input was evaluable and a refactor/proof law was violated
64  required input was absent or invalid JSON/usage
70  Draft 2020-12 validator/schema/assertion mechanism was unavailable or invalid
```

A green receipt has evidence class `DETERMINISTIC_FIXTURE`. It does not claim live model/provider execution, Git Town/forge delivery, merge, release or production promotion.
