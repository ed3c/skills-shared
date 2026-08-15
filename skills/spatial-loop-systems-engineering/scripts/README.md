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

## `check_procedural_grounding.py`

Deterministically checks `procedural-grounding-receipt/v1` source provenance,
procedure atoms, uptake states, proof modes, fork/depth/token/no-progress budgets,
Context Capsule admission, assertion/probe obligations, weighted coverage, and
four-condition attribution arithmetic.

```bash
python3 check_procedural_grounding.py path/to/procedural-grounding-receipt.json
```

Exit contract:

```text
0   receipt is structurally and semantically closed
2   receipt is hollow, contradictory, stale, over-budget, or overclaims evidence
64  file, JSON, or usage is absent/invalid
```

The checker never searches for a Skill, spawns a model context, runs the declared
runtime oracle, or authenticates an external receipt. Those remain environment-
owned execution facts.

The public CLI is split into `procedural_grounding_common.py`,
`procedural_grounding_inputs.py`, `procedural_grounding_runtime.py`, and
`procedural_grounding_metrics.py`. These are internal implementation modules;
consumer automation should invoke only `check_procedural_grounding.py`.
