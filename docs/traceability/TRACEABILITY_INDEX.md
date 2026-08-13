# Traceability index — document routing

## Trace model

```text
source / incident
→ repository decision
→ parent issue
→ molecular issue
→ sibling or true-child PR
→ eval / negative control
→ immutable subject
→ receipt / current evidence state
→ Human Admit
```

## Four-repository documentation stack

| Plane | Issue | PR publication subject | Stack class | State |
|---|---|---|---|---|
| Parent integration contract | `ed3c/bettor-arena#35` | n/a | parent | open |
| Instruction / Method | `ed3c/skills-shared#84` | `ed3c/skills-shared#85` | independent sibling | Draft |
| Runtime Contract | `ed3c/runtime-env#29` | `ed3c/runtime-env#30` | independent sibling | Draft |
| Domain Product / Consumer | `ed3c/agent-shield-monorepo#77` | `ed3c/agent-shield-monorepo#78` | independent terminal sibling | Draft |
| Integration / Acceptance | `ed3c/bettor-arena#36` | `ed3c/bettor-arena#37` | independent sibling | Draft |
| Exact merged index and cold-start audit | `ed3c/bettor-arena#38` | future | convergence leaf | blocked by four PRs |

The exact candidate head of an open PR is read from GitHub PR metadata rather than embedded in the same branch: self-embedding a commit SHA would make the document stale in the commit that updates it. The convergence leaf will record immutable **merged** commit/tree identities after all four inputs exist.

The four implementation branches are siblings because each edits only its repository's documentation and consumes merged inputs. Creating a serial stack would add false dependencies. Issue `bettor-arena#38` is the only convergence owner and must not create a branch until all four siblings merge.

## Method lineage

- `knowledge-continuity` supplies the rule that every hop leaves an in-place summary and evidence is not hidden behind unexplained redirects.
- `github-delivery-loop` supplies issue/PR/receipt and publication-state separation.
- `forgejo-delivery-loop` supplies local authoring, deterministic routing/outbox/recovery, and receipt separation.
- `git-town-stacked-pr-worker` supplies sibling/true-child/terminal/convergence branch semantics and Human boundaries.

## Evidence boundary

PR presence and exact GitHub head metadata prove publication identity only. Documentation completion does not imply route-checker execution, fresh Claude/Codex cold-start, GitHub/Forgejo equivalence, live provider canaries, capability unlock, release promotion, or production readiness.
