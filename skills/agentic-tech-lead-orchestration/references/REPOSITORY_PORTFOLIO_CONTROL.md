# Repository Portfolio Control

Tracking: `ed3c/skills-shared#560`  
Contract: `agentic-tech-lead/repository-portfolio-control/v1`

This composition reuses `agentic-tech-lead-orchestration`,
`procedural-shadow-runtime`, `github-delivery-loop`,
`git-town-stacked-pr-worker`, `shared-skills-infra`, and the existing Issue Closure
Contract. It does not create a second planner, Shadow, merge authority, closure
authority, or bootstrap authority.

Mandatory coordinator law:

```text
Use subagents. Wait for all agents and consolidate their findings.
```

## State Machine

```text
REQUEST_BOUND
→ RUNTIME_AND_AUTHORITY_ADMITTED
→ REPOSITORY_SET_FROZEN
→ SNAPSHOT_EPOCH_BOUND
→ ACCEPTANCE_CONTRACTS_COMPILED
→ ADVERSARIAL_DRIFT_AUDITED
→ G1_G7_ASSERTED
→ READY_WAVES_COMPUTED
→ READ_ONLY_SUBAGENTS_DISPATCHED
→ ALL_REQUIRED_AGENTS_TERMINAL
→ FINDINGS_CONSOLIDATED
→ BOUNDED_WRITERS_DISPATCHED
→ ALL_WRITERS_TERMINAL
→ LOCAL_GATES_PASS
→ DRAFT_PUBLICATION
→ ONE_SHOT_CI_EPOCH
→ READY_FOR_HUMAN_ADMIT | HOLD | REJECT
→ TRUE_DEPENDENCY_MERGE
→ EXACT_MAIN_READBACK
→ ISSUE_CLOSURE_RECONCILED
```

## Separate graphs

`G1` start dependency, `G2` completion dependency, `G3` Git ancestry,
`G4` path writers, `G5` resources/runtime, `G6` evidence/authority, and `G7`
publication/merge/closure remain separate. Queue order, chronology, Issue links, or
shared vocabulary do not manufacture Git ancestry.

## Evidence and authority

`AVAILABLE` is not `EXERCISED`; Draft/open/mergeable/green prose is not semantic
admission; static/local/hosted/provider/private/Human/production lanes do not
substitute for one another. Failed, stale, cancelled, blocked, timed-out, unavailable,
superseded, rejected, and closed-unmerged attempts remain in the denominator.

Shadow Architect is read-only. One Worker owns one attempt, branch, worktree,
exclusive path lease, and exclusive resource lease. Private bytes may cross a provider
boundary only after explicit repository/provider/egress admission. Merge, release,
visibility, permissions, secrets, billing, semantic conflicts, production, and
rollback remain Human or pre-authorized repository authority.

## Prompt and Codex routes

- `prompts/repository-portfolio-controller-v3.md`
- `prompts/repository-portfolio-role-prompts-v1.md`
- `repository-portfolio-control/codex-agent-templates.md`
- `repository-portfolio-control/prompt-manifest.json`
- `../scripts/check_repository_portfolio_prompt_pack.py`
- `../tests/portfolio-control/run-all.sh`

This foundation proves prompt packaging and mutation sensitivity only. Live Codex
subagents, `/Users/neon/skills-shared` worktrees, portfolio compilation, hosted CI,
thin bootstrap, merge, release, and production remain separate successor/evidence
lanes.
