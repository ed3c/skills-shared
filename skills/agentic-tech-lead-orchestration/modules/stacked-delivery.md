# Stacked delivery adapter

## Trigger

Use when a dependency-ordered change should be delivered as atomic Git Town branches and forge review requests.

## Non-trigger

Do not create an artificial Stack for independent siblings, bypass an active queue/path lease, activate unadmitted Git Town/forge tooling, or automate merge.

## Purpose

Map DAG serial edges to parent/child branches, keep independent work as siblings, and create reviewable forge requests through the repository's admitted adapter.

## Assumptions

Base and parent commits, branch class, path lease, admitted Git Town closed command set, forge identity, no-push/publication policy, and Human boundaries are declared.

## State machine

```text
validated DAG → branch topology → isolated worktrees → local commits
→ parent-targeted PRs → bounded restack → gates → Human review
```

Failure states: `BASE_MOVED`, `PARENT_EDGE_INVALID`, `DUPLICATE_WRITER`, `GIT_TOWN_NOT_ADMITTED`, `FORGE_IDENTITY_ABSENT`, `RESTACK_CONFLICT`, `UNSAFE_FORCE_PUSH`, `PUBLICATION_NOT_ADMITTED`.

## Inputs

DAG, exact base, branch names/classes, allowed paths, commit messages, validation commands, and publication policy.

## Outputs and effects

Local branches/commits and, only when admitted, forge PR metadata. Merge, ship, close, force-push policy, and rollback remain external authority.

## Evidence class and freshness

A local Stack receipt proves local ancestry only. Remote PR/check/merge claims require current forge readback.

## Fallback

Use standard Git branches and manually recorded parent edges; do not simulate Git Town execution in prose.

## Core laws that remain authoritative

`../SKILL.md` owns DAG edge semantics, exact subjects, semantic-conflict proof, and Human Admit.

## Consumer-owned values

Git Town config/version/checksum, remotes, forge URL/CLI/API, credentials, branch protections, PR identities, checks, and live receipts remain consumer-owned.
