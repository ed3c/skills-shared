# Executable assertions

`assert_task_contract.py` is a Python-standard-library hard gate. It performs no network calls, invokes no model/provider, and mutates only the requested receipt.

It validates schema/required fields, immutable subjects, path leases, branch topology, provider-role separation, evidence ceilings, budgets, automation boundaries, and the prohibition on active `code-graph-rag` dependencies.

```bash
python3 scripts/assert_task_contract.py --contract <contract.json> --receipt <receipt.json>
```

Exit codes: `0` pass, `2` evaluated assertion failure, `64` invalid/absent input, `70` internal mechanism error.
