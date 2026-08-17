# Executable assertions

`assert_task_contract.py` is a Python-standard-library hard gate. It performs no network calls, invokes no model/provider, and mutates only the requested receipt.

It validates schema/required fields, immutable subjects, path leases, branch topology, provider-role separation, evidence ceilings, budgets, automation boundaries, and the prohibition on active `code-graph-rag` dependencies.

```bash
python3 scripts/assert_task_contract.py --contract <contract.json> --receipt <receipt.json>
```

`assert_local_handoff_queue.py` is the zero-network hard gate for consumer handoff continuation. It validates exact subject binding, exactly one ACTIVE item, predecessor/next ordering, concrete argv/cwd/timeout lanes, durable receipt contracts, evidence-state ceilings, rollback identity, and forbidden automation authority. Its selftest plants stale-subject, dual-active, early-successor, placeholder-command, authority-widening, receipt-laundering, and queue-skip defects.

```bash
python3 scripts/assert_local_handoff_queue.py --queue <queue.json>
python3 scripts/assert_local_handoff_queue.py --queue <queue.json> --selftest
```

Exit codes for portable assertions: `0` pass, `2` evaluated assertion failure, `64` invalid/absent input. Assertions do not execute consumer commands, providers, issue mutations, merges, promotions, or queue advancement.
