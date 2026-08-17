# Executable assertions

The portable pre-dispatch contract is a two-stage gate. Both stages are zero-network and neither invokes a model/provider.

1. `check_task_contract_schema.py` validates packet shape with the repository's Draft 2020-12 `references/task-contract.schema.json`. The owning CI installs the pinned `jsonschema` validator. A missing/invalid validator or schema is mechanism error `70`; it is never skipped or converted to PASS.
2. `assert_task_contract.py` is the Python-standard-library semantic/hard-law gate. It validates immutable subjects, safe paths and leases, branch/DAG topology, provider-role separation, exact-subject/readback rules, evidence ceilings, budgets, automation boundaries, Git Town admission, semantic-conflict refusal, Human merge authority, and the prohibition on active `code-graph-rag` dependencies. It mutates only the requested receipt.

```bash
python3 scripts/check_task_contract_schema.py --contract <contract.json>
python3 scripts/assert_task_contract.py --contract <contract.json> --receipt <receipt.json>
```

Both commands must return `0` before Worker admission. Exit codes are `0` pass, `2` evaluated gate failure, `64` invalid/absent input, and `70` mechanism/validator failure. Shape PASS and semantic PASS are distinct receipts/states; neither proves a provider, Worker, Worktree, delivery lane, merge, or promotion ran.
