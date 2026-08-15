# Scripts

All scripts use the Python standard library for their core contract logic.

| Script | Input | Exit `0` | Exit `2` | Exit `64` |
|---|---|---|---|---|
| `check_runtime_receipt.py` | Runtime receipt JSON | Closed runtime contract | Semantic refusal | Input/parse error |
| `check_agent_architecture_eval.py` | Architecture receipt JSON | Closed assessment, including a valid low band | Rubric/evidence contradiction | Input/parse error |
| `check_meta_abstraction_eval.py` | Meta receipt JSON | Closed promotion assessment | Score/gate refusal | Input/parse error |

The checkers do not call external networks, mutate consumer repositories, or execute candidate adapters. Domain adapter execution is isolated under `modules/` and must run in the host sandbox.
