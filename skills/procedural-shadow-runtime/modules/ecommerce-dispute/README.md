# E-Commerce Dispute Executable Eval Family

This directory is a **domain adapter**, not the universal Agent Architecture method and not a production dispute service.

## Contract

A consumer adapter must expose:

```python
def run_case(case: dict) -> dict:
    ...
```

The result must contain the paths referenced by `cases.json`, including final state, tool-call counts, and a bounded trace. The deterministic runner imports the adapter inside the host-provided sandbox and evaluates the six canonical cases.

```bash
python3 modules/ecommerce-dispute/run_evals.py \
  --adapter /path/to/candidate_adapter.py \
  --cases modules/ecommerce-dispute/cases.json \
  --repository owner/repo \
  --subject-sha <40-hex> \
  --subject-digest <64-hex> \
  --output /tmp/ecommerce-receipt.json
```

Exit contract:

```text
0   all deterministic assertions and budgets pass
2   candidate execution or assertion failure
64  absent/malformed input or adapter contract
```

## Domain boundary

The following are local to this task family:

- USD 500 deterministic HITL boundary;
- 5-second logistics timeout;
- refund/voucher/rejection tools;
- vision damage evidence;
- 15-second, 1,500-token, and USD 0.05 budgets.

The universal rubric knows only concepts such as deterministic high-risk gates, idempotent writes, bounded timeouts, context budgeting, and executable Evals. It does not inherit these e-commerce constants.

## Files

| File | Authority |
|---|---|
| `cases.json` | Six canonical cases, mock inputs, deterministic assertions, budgets |
| `run_evals.py` | Adapter loader, assertion engine, exact-subject receipt emitter |
| `reference_adapter.py` | Deterministic executable fixture; not a production Agent |

The semantic judge is intentionally `NOT_EXERCISED` in this deterministic family. A consumer may add semantic scoring, but it cannot override failed safety assertions.
