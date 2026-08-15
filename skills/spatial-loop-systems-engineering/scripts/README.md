# Scripts

## `check_system_contract.py`

Deterministically checks the shape, cross-references, evidence-state discipline,
performance-claim closure, teardown symmetry, and implementation-gate
consistency of `spatial-loop-system-contract/v1`.

```bash
python3 check_system_contract.py check path/to/system-contract.json
```

Exit contract:

```text
0   valid contract and internally consistent gate
2   declared contract is hollow or contradictory
64  file, JSON, command, or usage is absent/invalid
```

The script performs zero network access and uses only the Python standard
library. It validates evidence references as strings; it does not attest the
external evidence they name.
