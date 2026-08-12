# Traceability index — document routing

## Trace model

```text
source / incident
→ repository decision
→ parent issue
→ molecular issue
→ sibling or child PR
→ eval / negative control
→ immutable subject
→ receipt / current evidence state
→ Human Admit
```

## Current documentation line

| Subject | Repository item | State |
|---|---|---|
| Four-repository routing parent | `ed3c/bettor-arena#35` | open parent contract |
| Shared routing method | `ed3c/skills-shared#84` | this documentation issue |
| Runtime binding docs | `ed3c/runtime-env#29` | independent sibling |
| Agent Shield binding docs | `ed3c/agent-shield-monorepo#77` | independent sibling |
| Bettor integration docs | `ed3c/bettor-arena#36` | independent sibling |
| Final exact merged index / cold-start audit | future bettor convergence leaf | `NOT_IMPLEMENTED` until sibling PRs merge |

PR base/head metadata and Git commits are the source of truth for publication status. This Markdown is a navigation snapshot.

## Method lineage

- `knowledge-continuity` supplies the rule that readers must not depend on hidden background or two-hop evidence chains.
- `github-delivery-loop` supplies issue/PR/receipt and publication-state separation.
- `forgejo-delivery-loop` supplies local authoring, deterministic routing, outbox/recovery, and receipt separation.
- `git-town-stacked-pr-worker` supplies molecular sibling/child/terminal/convergence branch semantics.

## Evidence boundary

Documentation completion does not imply mechanical route-checker execution, GitHub/Forgejo equivalence, live provider canaries, capability unlock, release promotion, or production readiness.
