# AGENTS.md — Skill refactor proof operating contract

Read this file before changing the `skill-refactor-proof-loop` or using it to refactor another Skill.

## Mandatory read order

1. repository root `AGENTS.md`, `README.md`, `CONTEXT.md`, and `ARCHITECTURE.md`;
2. this `AGENTS.md`;
3. this directory's `README.md`;
4. `SKILL.md`;
5. `references/refactor-proof-contract.schema.json`;
6. `references/golden-proof-registry.schema.json`;
7. `references/golden-proof-registry.json`;
8. `references/skill-adoption-ledger.json` when the change touches another Skill's adoption state;
9. `evals/proof-standard-admission.json` for the bound scope this standard was admitted under;
10. only the selected module under `modules/`;
11. `scripts/`, `tests/`, and the exact issue/PR subjects.

Chat history, branch names, issue state, and Markdown claims are not evidence substitutes.

## Writer and authority rules

- One Worker owns one branch, one linked worktree, and one disjoint path lease.
- A Stack child is legal only when it consumes unmerged parent bytes or contracts.
- Historical treatment bytes are immutable evidence. Never edit them to improve a score.
- Preserve old strengths as named assertions; a cleaner structure is not proof of behavioral preservation.
- Keep structural, executable-contract, hermetic real-task, matched live runtime, and delivery evidence separate.
- Failed, stale, blocked, cancelled, and superseded attempts remain in the denominator.
- Fixture or synthetic evidence cannot become live model/provider PASS.
- An admission record decides which method is canonical. It is never evidence, never a run, and never a reason to move a measured state.
- Semantic conflict, provider activation, publication, merge, release, promotion, and rollback remain Human/trusted-operator authorities.

## Required change packet

Before implementation, bind:

```text
owner Skill
old canonical treatment
refactor-as-landed treatment
repaired candidates
protected old strengths
proof layer being attempted
matched task/base/tree/contracts/tests/budget/carrier
allowed/read-only/forbidden paths
denominator and cleanup rules
parent/sibling/convergence graph
remaining evidence owners and issues
rollback subject
Human Admit boundary
```

Missing fields are `ABSENT`; do not infer them.

## Completion report

Report the exact proof layer reached, treatment and registry digests, commands and controls executed, current PR Stack, residue state, and every higher evidence layer that remains `NOT_EXERCISED`, `ABSENT`, or `HUMAN_ADMIT_REQUIRED`.
