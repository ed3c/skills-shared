# Issue #376 — GitHub Issue DAG execution packet

Base: `85e6723869bdd545666e07b7c5c6a8f491256cb9`
Branch: `ctl/376-github-issue-dag-projection`
Prep: #381 / #383
Convergence: #379

## Read order

Root Agent/document routes → Agentic Tech Lead nearest AGENTS/README/SKILL → `issue-dual-dag` and task/scheduler contracts → GitHub delivery-loop route → issue #376.

## Writable lease

Only issue-owned GitHub DAG adapter, projection/readback schema, ready-wave generator, checker/tests/fixtures under the Agentic Tech Lead Skill. Shared README/AGENTS/traceability/Git Town indexes are read-only; #379 owns convergence.

## State machine

`TASK_DAG_ASSERTED → GITHUB_PROJECTION_COMPILED → ISSUE_DEPENDENCIES_WRITTEN → REMOTE_READBACK → PROJECTION_RECEIPT → READY_WAVE_COMPUTED → SESSION_DISPATCH_ELIGIBLE`.

## Required contract

GitHub blockedBy/blocking is a durable projection, never semantic truth alone. Bind exact repo identity, visibility/default branch, issue identities, frozen input graph digest, mutation intent, readback edge set and receipt. Preserve start-readiness vs completion-readiness in machine truth. Refuse cycles, self edges, false serialization of path-disjoint siblings, missing/extra edges, stale issues, projection drift, duplicate linked PR ownership and UI-state/evidence laundering.

## Shadow controls

Independently recompute the expected graph from frozen contracts and current remote readback, compare the complete denominator, and refuse any unsupported edge/state.

## Zero-context worker prompt

Implement issue #376 on this branch only. Project only already-asserted semantic dependencies. Compute ready waves only after exact readback agrees with the portable graph. Add positive and drift/cycle/false-edge/duplicate-PR/closure-laundering controls. Do not edit convergence docs, merge, release, close issues as proof, or widen repository authority. Return exact subjects, projected/read-back edge sets, ready-wave manifest, test denominator, evidence ceiling, cleanup/rollback and #379 handoff.

## Completion gate

Schema/checker positive PASS; every planted defect refused; fixture evidence remains distinct from live GitHub mutation/readback evidence; affected Skill suites remain green.
