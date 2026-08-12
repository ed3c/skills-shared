# Git Town Stacked-PR Worker completion report

## Subject

```text
repository: <REPO_FULL_NAME>
repository identity: <REPO_IDENTITY>
issue/task: <ISSUE_OR_TASK_ID>
task packet SHA-256: <SHA256>
branch: <HEAD_BRANCH>
commit: <HEAD_SHA>
tree: <TREE_SHA>
rollback subject: <IMMUTABLE_ROLLBACK_REF>
```

## Tool admission

```text
Git Town version: <EXACT_VERSION>
source/release identity: <IMMUTABLE_RELEASE>
executable checksum/provenance: <STATE_AND_REF>
direct license: <STATE_AND_REF>
SBOM/transitive review: <STATE_AND_REF>
notices review: <STATE_AND_REF>
legal approval: <STATE_AND_REF>
```

Do not write “zero legal risk.” Name each state separately.

## Stack graph

### Before

```text
<STACK_GRAPH_BEFORE>
```

### After

```text
<STACK_GRAPH_AFTER>
```

Changed parent relationships:

```text
<CHANGED_PARENT_EDGES_OR_NONE>
```

## Execution

| Lane | Command/entrypoint | Exit | State | Receipt |
|---|---|---:|---|---|
| preflight | `<ENTRYPOINT>` | `<N>` | `<STATE>` | `<REF>` |
| dry-run | `<ENTRYPOINT>` | `<N>` | `<STATE>` | `<REF>` |
| local no-push sync | `<ENTRYPOINT>` | `<N>` | `<STATE>` | `<REF>` |
| guarded publish | `<ENTRYPOINT_OR_NOT_RUN>` | `<N_OR_NA>` | `<STATE>` | `<REF>` |
| post-sync ancestry | `<ENTRYPOINT>` | `<N>` | `<STATE>` | `<REF>` |
| cleanup/residue | `<ENTRYPOINT>` | `<N>` | `<STATE>` | `<REF>` |

## Ref movement

```text
local refs changed: <REFS_OR_NONE>
remote refs changed: <REFS_OR_NONE>
protected/perennial refs changed: <MUST_BE_NONE_OR_REVIEWED_EXCEPTION>
push performed: <YES_OR_NO>
```

## Path lease

```text
allowed paths: <PATHS>
excluded paths: <PATHS>
actual changed paths: <PATHS>
path conflicts: <NONE_OR_DETAILS>
sibling worktree/branch contact: <NONE_OR_DETAILS>
```

## Eval results

| Eval ID | Positive result | Negative/mutation result | Evidence state | Receipt/artifact |
|---|---|---|---|---|
| `<ID>` | `<RESULT>` | `<RESULT>` | `<STATE>` | `<REF>` |

A positive result without its required control must not be reported as settled.

## Blocked state or named exclusions

```text
Worker outcome: <SYNCED|NO_CHANGE|BLOCKED_TASK_PACKET|BLOCKED_DIRTY|BLOCKED_CONFLICT|BLOCKED_PROMPT|BLOCKED_TIMEOUT|BLOCKED_BRANCH_LEASE|BLOCKED_ANCESTRY|BLOCKED_POLICY|FAILED_TOOL|FAILED_EVAL|ROLLBACK_REFUSED_DRIFT>
blocked worktree preserved: <YES_OR_NO_OR_NA>
named exclusions: <LIST>
```

## Cleanup and residue

```text
lease released: <STATE>
child processes terminated: <STATE>
temporary files removed: <STATE>
worktree disposition: <PRESERVED|REMOVED|REVIEW_REQUIRED>
residue: <NONE_OR_LIST>
```

Task success and cleanup success are separate lanes.

## Remaining gaps

```text
ABSENT: <LIST_OR_NONE>
NOT_IMPLEMENTED: <LIST_OR_NONE>
NOT_EXERCISED: <LIST_OR_NONE>
SKIPPED_BY_POLICY: <LIST_OR_NONE>
```

## Human Admit and merge order

```text
human action required: <YES>
semantic conflict owner: <OWNER_OR_NONE>
review order: <ORDER>
merge order: <ORDER>
operations still human-owned: <LIST>
```

Do not claim Stacked-PR completion until every applicable field is populated and the owning evidence exists.