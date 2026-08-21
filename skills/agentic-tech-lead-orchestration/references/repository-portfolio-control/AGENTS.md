# AGENTS.md — Repository Portfolio Control

Read `../REPOSITORY_PORTFOLIO_CONTROL.md`, this directory's `README.md`, all schemas,
the prompt manifest, the exact prompt selected for the role, and Issue #560 before
changing this subtree.

## Writer lease

This foundation atom owns only:

```text
references/REPOSITORY_PORTFOLIO_CONTROL.md
references/prompts/repository-portfolio-controller-v3.md
references/prompts/repository-portfolio-control/**
references/repository-portfolio-control/**
scripts/check_repository_portfolio_prompt_pack.py
scripts/assert_repository_portfolio_snapshot.py
scripts/assert_issue_pr_acceptance.py
scripts/assert_portfolio_multigraph.py
scripts/assert_subagent_join.py
scripts/assert_one_shot_ci_epoch.py
tests/portfolio-control/**
```

Root routes, Skill prose, shared `tests/run-all.sh`, workflows, registry,
shared bootstrap paths, Git Town indexes, and existing runtime-handoff queues are
read-only in this atom.

## Stop laws

Stop and report rather than weaken a gate when:

- `main` or the selected parent moves;
- an open PR writes an owned exact path;
- a schema or prompt ID conflicts with an existing authority;
- a required result is missing from the join denominator;
- a local or hosted lane is unavailable;
- a semantic conflict or permission/merge/release decision appears.

## Completion packet

Return changed paths, prompt and schema IDs/digests, commands/exits, positive and
mutation denominator, exact base/head/tree, residual runtime/bootstrap/convergence
owners, evidence ceiling, rollback, and Human authority.
