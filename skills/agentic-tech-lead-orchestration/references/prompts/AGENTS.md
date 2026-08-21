# AGENTS.md — Repository Portfolio Controller prompts

Read this file before changing or consuming `repository-portfolio-controller-v3.md`.

## Mandatory read order

1. repository root `AGENTS.md` and current exact GitHub/local subject;
2. `skills/agentic-tech-lead-orchestration/AGENTS.md`;
3. `../REPOSITORY_PORTFOLIO_CONTROL.md`;
4. `repository-portfolio-controller-v3.md`;
5. `../contracts/repository-portfolio-snapshot.schema.json`;
6. `../contracts/issue-pr-acceptance.schema.json`;
7. `../contracts/portfolio-multigraph.schema.json`;
8. `../contracts/subagent-dispatch.schema.json`, `subagent-result.schema.json`, and `subagent-join-receipt.schema.json`;
9. `../contracts/one-shot-ci-epoch.schema.json`;
10. `../codex-agents/AGENTS.md` and only the selected role templates;
11. `../../scripts/compile_repository_portfolio.py` and the owning assertion scripts;
12. `../../tests/portfolio-control/run-all.sh`;
13. exact Issue, PR, branch, workflow and evidence subjects.

## Non-negotiable coordinator barrier

```text
Use subagents. Wait for all agents and consolidate their findings.
```

This is a machine-checked join requirement. Do not shorten, paraphrase, or remove it from the canonical prompt or role templates.

## Prompt ownership

`repository-portfolio-controller-v3.md` is the one canonical portable controller prompt. Role templates add bounded role-specific instructions; they do not copy or override the controller's authority, graph, evidence, publication, merge, or closure laws.

Do not write consumer repository names, private source locations, credentials, live model sessions, mutable branch heads, current PR state, or runtime receipts into this directory. Consumer bindings pin the exact shared subject and own their local deltas.

## Stop conditions

Stop and return a typed blocker when:

- the snapshot epoch or exact base moved;
- acceptance is missing or contradictory;
- a required agent result is missing;
- path/resource leases overlap;
- model/provider/egress identity is unresolved;
- a lower evidence lane is promoted;
- Ready has already occurred and code movement is requested;
- merge, release, production, visibility, permission, secret or rollback authority is absent.

Do not request or persist private chain of thought.
