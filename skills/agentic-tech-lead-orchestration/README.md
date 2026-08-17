# agentic-tech-lead-orchestration

Portable contract-first orchestration for turning one large coding request into a dependency-aware branch team and, when the current session reaches a real host/runtime boundary, a zero-context Local Handoff Execution Queue. `SKILL.md` owns the method; `modules/` contains optional provider/delivery adapters; `references/` contains stable packet schemas and prompt templates; `scripts/` contains deterministic assertions.

## Data flow

```text
Issue / PRD / PDF
→ repository routing
→ locked task contract
→ optional retrieval/context lanes
→ current-source readback
→ DAG + Worktree prompt packets
→ admitted Worker execution
→ bounded gates and repair
→ candidate selection / Stack convergence
→ global objective assertion
→ delivery handoff
→ [if local/runtime-only evidence remains]
   Local Handoff Execution Queue
   entry → runtime lane → receipt → exit → next item
→ Human / local-runtime authority
```

A handoff queue is not a TODO list. It is an executable continuation contract with exactly one `ACTIVE` item, immutable subject identity, concrete command/runtime bounds, durable receipt requirements, fail-closed exit conditions, and explicit next-item routing. Consumer issue IDs, repository commands, provider names, local paths, and credentials never belong in the portable core.

`code-graph-rag` is intentionally not an active dependency. A consumer may retain old files for migration/audit, but the task contract assertion rejects it as a runtime provider.

## Read order

1. repository instructions and current task packet;
2. `SKILL.md`;
3. `references/task-contract.schema.json`;
4. `references/local-handoff-queue.schema.json` when a host/runtime boundary exists;
5. `references/fanout-prompt.md`;
6. `modules/README.md`, then only required modules;
7. executable assertions and selftests.

## Local verification

```bash
python3 scripts/assert_task_contract.py --contract references/example-stack-contract.json --receipt /tmp/agentic-tech-lead-receipt.json
python3 scripts/assert_local_handoff_queue.py --queue references/example-local-handoff-queue.json
python3 scripts/assert_local_handoff_queue.py --queue references/example-local-handoff-queue.json --selftest
sh tests/run-all.sh
```

A local PASS validates packet mechanics only. Live providers, index freshness, Worktrees, Git Town, Forgejo, CI, signed-in carriers, devices, and model quality remain `NOT_EXERCISED` until separate exact-subject receipts exist.
