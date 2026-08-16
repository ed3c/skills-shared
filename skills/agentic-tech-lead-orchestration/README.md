# agentic-tech-lead-orchestration

Portable contract-first orchestration for turning one large coding request into a dependency-aware branch team. `SKILL.md` owns the method; `modules/` contains optional provider/delivery adapters; `references/` contains stable packet schemas and prompt templates; `scripts/` contains deterministic assertions.

## Data flow

```text
Issue / PRD / PDF
→ repository routing
→ locked task contract
→ grepai candidate intent anchors (optional)
→ current-source readback
→ SCIP + SQLite deterministic impact graph (when admitted)
→ Tree-sitter context slicing
→ DAG + Worktree prompt packets
→ Serena or another admitted Worker executor
→ bounded gates and repair
→ tournament selection or Git Town Stack
→ Forgejo/GitHub review boundary
→ Human Admit
```

`code-graph-rag` is intentionally not an active dependency. A consumer may retain old files for migration/audit, but the task contract assertion rejects it as a runtime provider.

## Read order

1. repository instructions and current task packet;
2. `SKILL.md`;
3. `references/task-contract.schema.json`;
4. `references/fanout-prompt.md`;
5. `modules/README.md`, then only required modules;
6. executable assertion and selftest.

## Local verification

```bash
python3 scripts/assert_task_contract.py --contract references/example-stack-contract.json --receipt /tmp/agentic-tech-lead-receipt.json
sh tests/run-all.sh
```

A local PASS validates the packet mechanics only. Live providers, index freshness, Worktrees, Git Town, Forgejo, CI, and model quality remain `NOT_EXERCISED` until separate receipts exist.
