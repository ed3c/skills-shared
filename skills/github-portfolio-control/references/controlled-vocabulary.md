# Controlled vocabulary

The closed word lists the four schemas in [`schemas/`](schemas/) and the checker
[`../scripts/compile_portfolio_control.py`](../scripts/compile_portfolio_control.py)
agree on. Nothing here is a procedure. A term that is not in one of these lists
is not a term this contract plane can carry, and a schema that widens one of
these lists without widening it here has forked the vocabulary.

## The 24 ordered portfolio states

The plane advances through these and only these. The order is load-bearing: the
checker compares a claimed state against the position of the evidence that
supports it, so a plane cannot sit past a state whose predecessor is unmet.

```text
 1  REQUEST_BOUND
 2  RUNTIME_AND_AUTHORITY_ADMITTED
 3  REPOSITORY_SET_FROZEN
 4  GITHUB_SNAPSHOT_EPOCH_BOUND
 5  ISSUE_PR_DENOMINATOR_COMPLETE
 6  ACCEPTANCE_CONTRACTS_COMPILED
 7  ADVERSARIAL_DRIFT_AUDITED
 8  MULTI_GRAPH_MODEL_ASSERTED
 9  READY_WAVES_COMPUTED
10  SUBAGENTS_DISPATCHED
11  ALL_REQUIRED_AGENTS_TERMINAL
12  RESULTS_SCHEMA_VALIDATED
13  FINDINGS_CONSOLIDATED
14  LOCAL_WORKTREES_EXECUTED
15  EXACT_HEAD_LOCAL_GATES_PASS
16  DRAFT_PUBLICATION
17  ONE_SHOT_CI_EPOCH
18  CI_JOBS_STEPS_ARTIFACTS_READ_BACK
19  PR_ACCEPTANCE_RECONCILED
20  READY_FOR_HUMAN_ADMIT
21  MERGE_IN_TRUE_DEPENDENCY_ORDER
22  EXACT_MAIN_READBACK
23  ISSUE_CLOSURE_RECONCILED
24  PORTFOLIO_EPOCH_CLOSED
```

Movement returns the affected node and its descendants to the earliest invalid
state. It does not restart unrelated safe work, and it is recorded as a typed
delta rather than as a rewritten epoch.

## The 17 drift kinds

Every typed delta carries exactly one of these. A delta with a free-text kind is
a note, and a note does not invalidate an epoch.

```text
INTENT_DRIFT              SCOPE_DRIFT               ACCEPTANCE_DRIFT
BASE_MAIN_DRIFT           DEPENDENCY_DRIFT          GIT_ANCESTRY_DRIFT
PATH_WRITER_DRIFT         RESOURCE_LEASE_DRIFT      IMPLEMENTATION_DRIFT
EVIDENCE_DRIFT            RUNTIME_DRIFT             MODEL_IDENTITY_DRIFT
PROVENANCE_DRIFT          CI_EPOCH_DRIFT            ISSUE_PR_STATE_DRIFT
SECURITY_VISIBILITY_DRIFT POST_MERGE_CLOSURE_DRIFT
```

## Durable and mutable subjects

A **durable subject** is content-addressed: the bytes cannot change under the
name. A **mutable readback** is a name or a provider verdict that describes
whatever it points at when somebody next reads it.

```text
durable      MAIN_COMMIT  MAIN_TREE  PR_HEAD_COMMIT  PR_BASE_COMMIT
             BLOB_DIGEST  AGENT_RESULT_DIGEST  WORKFLOW_RUN_TESTED_HEAD

mutable      BRANCH_NAME  PR_MERGEABILITY  PR_STATE  MODEL_PROSE
             ISSUE_TITLE  QUEUE_ORDER
```

A mutable readback may be recorded. It may not be marked durable, and no control
decision may name one as its evidence subject.

## The 7 subagent roles

```text
portfolio-explorer          read-only provider/repository inventory
acceptance-adversary        read-only Issue/PR acceptance and drift audit
dependency-auditor          read-only G1-G7 graph recomputation
runtime-admission-auditor   read-only tool/provider/egress admission
implementation-worker       one isolated worktree, one exclusive path lease
consolidation-verifier      read-only all-results denominator and contradiction check
release-auditor             read-only exact-head CI/merge/main/closure readback
```

## The 8 agent terminal states

```text
terminal      COMPLETED  FAILED  CANCELLED  BLOCKED  STALE  UNAVAILABLE
non-terminal  DISPATCHED  RUNNING
```

Cancelled, blocked, stale, failed and unavailable agents stay in the
denominator. They are outcomes, not absences.

## The 3 routing aliases

```text
FABLE_5    portfolio orchestrator / DAG planner; no implementation write by default
OPUS_5     adversarial architect / independent verifier; read-only
SONNET_5   bounded implementation Worker; one exclusive lease
```

An alias is a policy label. Before dispatch it resolves to provider, carrier,
exact model and version, config/effort, data boundary and availability. An
unresolved alias is `ALIAS_ONLY` with an absent exact model; it is never
reported as an exercised identity.

## The 4 evidence ceilings

One per contract, so the weakest lane a reader touches always states its own
ceiling rather than inheriting the document's.

```text
REPOSITORY_BYTES_AND_LOCAL_GIT_ONLY   what a local checkout and git can settle
DETERMINISTIC_COMPOSITION             arranging admitted records proves the arrangement
HOSTED_EXECUTION_ONLY                 a workflow ran on a named head, and nothing more
JOIN_DENOMINATOR_ONLY                 every requested agent is accounted for, and nothing more
```

Hosted execution success is not semantic acceptance, merge authority, release
authority or production readiness.

## The 9 checker refusal codes

The schemas refuse what one document can contradict on its own. These nine are
what only a bundle can contradict — each needs two documents visible at once —
so the checker owns them and exits 2 naming one.

```text
K01_MIXED_SNAPSHOT_EPOCH            two members bound to different subjects
K02_JOIN_INCOMPLETE_ADVANCE         a state past the join barrier with a non-terminal agent
K03_SUPERSEDED_EPOCH_NOT_SUPERSEDED a superseded epoch whose subject equals the current one
K04_AUTHORITY_ROUTE_ABSENT          a composed authority routed at a path not on the tree
K05_COORDINATOR_INSTRUCTION_ALTERED the instruction differs from the pinned bytes
K06_CI_EPOCH_NOT_EXACT_HEAD         a hosted receipt whose tested head is not the candidate head
K07_REQUIRED_ROLE_MISSING           a required role absent from the requested denominator
K08_SHAPE_EXAMPLE_USED_AS_RECEIPT   a reserved 900-block identifier inside a real bundle
K09_OVERLAPPING_EXCLUSIVE_LEASE     two exclusive writers over paths that are not disjoint
```

Identifiers in the `900`-`999` block are reserved for shape-only instances that
live inside a schema's `examples`. They never describe an observed run, and the
checker refuses a bundle that carries one.

## Authority

Every artifact in this plane pins `merge`, `release`, `promotion`,
`provider_execution` and `production` to `false`. Human Admit owns all five. An
artifact that could set one of them true would be an artifact that grants
authority by describing it.
