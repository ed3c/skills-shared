# GitHub Issue DAG projection

GitHub Issue Dependencies are a durable collaboration projection, not the semantic source of truth for the Tech Lead scheduler.

## Dual-edge rule

The portable DAG keeps two readiness meanings:

- `start`: the predecessor has produced enough readable output for downstream work to begin;
- `completion`: the predecessor must be admitted before downstream completion is valid.

GitHub exposes one `blockedBy/blocking` relation. This adapter therefore permits `project_to_github=true` only on `completion` edges. Projecting a start-readiness edge would falsely serialize work and is rejected.

## State machine

```text
TASK_DAG_ASSERTED
  -> GITHUB_PROJECTION_COMPILED
  -> REMOTE_PREFLIGHT_BOUND
  -> ISSUE_DEPENDENCIES_WRITTEN
  -> REMOTE_READBACK
  -> PROJECTION_RECEIPT
  -> READY_WAVE_COMPUTED
  -> SESSION_DISPATCH_ELIGIBLE
```

## Remote preflight

Before any live mutation, the graph binds and re-reads:

- exact `owner/name` repository identity;
- repository visibility and default branch;
- every issue identity and expected `OPEN` / `CLOSED` state;
- linked pull requests for every issue.

The adapter refuses stale issue state, repository identity/visibility/default-branch drift, and more than one open linked PR for the same issue. This prevents a second implementation PR from silently acquiring ownership of the same issue.

## Drift policy

After every mutation, read the full `blockedBy` denominator back from GitHub and compare exact sets. Missing and extra edges both fail. The repository/issue/link preflight is repeated after mutation and must match the pre-mutation observation. UI appearance, issue closure, labels, or a model summary cannot replace exact readback.

## Implementation

`../scripts/github_issue_dag_projection.py` validates cycle/self/duplicate constraints, keeps start/completion semantics separate, computes ready waves, and can use `gh repo view`, `gh issue view`, and `gh issue edit --add-blocked-by` on the explicit `--apply` path. Static mode never mutates GitHub.

`../tests/github_issue_dag_selftest.py` covers static projection/readback plus cycle, self-edge, false start-edge projection, duplicate-edge, unknown-node, repository metadata drift, stale issue state, duplicate linked-PR ownership, and unmanaged remote-edge mutations. Live remote mutation/readback is an independent evidence lane and remains `NOT_EXERCISED` until run against an admitted repository subject.
