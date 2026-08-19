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
  -> ISSUE_DEPENDENCIES_WRITTEN
  -> REMOTE_READBACK
  -> PROJECTION_RECEIPT
  -> READY_WAVE_COMPUTED
  -> SESSION_DISPATCH_ELIGIBLE
```

## Drift policy

After every mutation, read the full `blockedBy` denominator back from GitHub and compare exact sets. Missing and extra edges both fail. UI appearance, issue closure, labels, or a model summary cannot replace exact readback.

## Implementation

`../scripts/github_issue_dag_projection.py` validates cycle/self/duplicate constraints, keeps start/completion semantics separate, computes ready waves, and can use `gh issue view --json blockedBy` plus `gh issue edit --add-blocked-by/--remove-blocked-by` on the explicit `--apply` path. Static mode never mutates GitHub.

`../tests/github_issue_dag_selftest.py` covers positive projection/readback plus cycle, self-edge, false start-edge projection, duplicate-edge, and unknown-node mutations. Live remote mutation/readback is an independent evidence lane and remains `NOT_EXERCISED` until run against an admitted repository subject.
