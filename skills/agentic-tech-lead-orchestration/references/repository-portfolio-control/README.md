# Repository Portfolio Control — Prompt and Contract Foundation

Tracking: `#560`  
Current bounded terminal: `PORTFOLIO_PROMPT_AND_CONTRACT_FOUNDATION_READY`

## Directory map

```text
references/REPOSITORY_PORTFOLIO_CONTROL.md
  portable State Machine, G1–G7 and authority law

references/prompts/repository-portfolio-controller-v3.md
  full coordinator system prompt

references/prompts/repository-portfolio-control/*.md
  common envelope, Tech Lead, Shadow and seven Codex role prompts

references/repository-portfolio-control/contracts/*.schema.json
  snapshot, acceptance, graph, dispatch, result, join, CI and prompt-manifest contracts

references/repository-portfolio-control/CODEX_SUBAGENTS_SOURCE.md
  mutable official-source disposition and runtime-drift boundary

references/repository-portfolio-control/codex-agents/*.toml.template
  project-scoped Codex custom-agent templates; not activated in skills-shared

scripts/check_repository_portfolio_prompt_pack.py
  prompt/hash/TOML and required-law gate

scripts/assert_repository_portfolio_snapshot.py
scripts/assert_issue_pr_acceptance.py
scripts/assert_portfolio_multigraph.py
scripts/assert_subagent_join.py
scripts/assert_one_shot_ci_epoch.py
  deterministic contract and false-promotion gates

tests/portfolio-control/
  positive and mutation denominator
```

## Foundation DAG

```text
Issue #560 frozen problem contract
├─ prompt pack + prompt manifest          SIBLING
├─ snapshot + acceptance contracts        SIBLING
├─ G1–G7 multigraph contract/checker      SIBLING
├─ dispatch/result/join contract/checker  SIBLING
├─ one-shot CI contract/checker           SIBLING
└─ Codex custom-agent templates           SIBLING
        ↓
this path-local selftest convergence
        ↓
next atom: compiler/runtime integration
        ↓
next atom: shared-skills-infra thin bootstrap
        ↓
real Codex/CI/consumer evidence
```

The sibling leaves share a frozen interface and disjoint files. None is a Git child of
another. The next compiler atom may become a true child only when it consumes these
exact unmerged bytes.

## Remaining lanes

```text
portfolio compiler and ready-wave generator     NOT_IMPLEMENTED
live Codex subagent dispatch/join                NOT_EXERCISED
local /Users/neon/skills-shared worktrees        NOT_EXERCISED here
one-shot hosted CI epoch                         NOT_EXERCISED
shared-skills-infra bootstrap profile            NOT_IMPLEMENTED
real public/private consumer canary              NOT_EXERCISED
merge, release, production                       HUMAN_ADMIT_REQUIRED
```
