# AGENTS.md — current runtime handoff and closure audit

Read this file before changing the current issue/PR closure classification, modifying a Local Handoff Execution Queue, claiming that a live lane is closed, or updating the current Molecular terminal index.

## Mandatory read order

1. repository root `AGENTS.md`, `README.md`, `CONTEXT.md`, and `ARCHITECTURE.md`;
2. `../AGENTS.md`, `../WAVE3_ADMISSION.md`, and `../CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md`;
3. this directory's `README.md`;
4. `../../../skills/agentic-tech-lead-orchestration/runtime-handoff/AGENTS.md` and `README.md`;
5. the exact queue named by the owning issue;
6. `../../../skills/git-town-stacked-pr-worker/molecular-indexes/codex-v2/README.md`;
7. current GitHub issue, PR, branch, workflow-run, review-thread, commit, and tree metadata.

Do not use chat history, an old PR body, a branch name, issue state, model agreement, generated Markdown, or a previous green workflow as current authority.

## Current immutable implementation subject

The queues in this directory are projections over the admitted implementation subject:

```text
repository       ed3c/skills-shared
implementation  249abc47847f8295b1c75c9d4c84457c5126fd89
tree            a24b9b7ace6f4022967d41262ecdc704d5c11646
rollback        d5993267e03b217dcdab9702dab0400ab03df860
```

A later documentation merge does not rewrite this subject. Any implementation change to a queued lane makes the old queue stale and requires a newly compiled queue bound to the newly admitted commit and tree.

## Authority order

```text
exact Git object and current provider metadata
→ executable schema/checker/test result
→ content-bound runtime/provider receipt
→ independent Shadow readback on the same subject
→ Human repository admission
→ documentation projection
```

A lower layer cannot override a higher one.

## Closure law

```text
SOURCE_PROPOSAL
→ METHOD_IMPLEMENTED
→ DETERMINISTIC_EVIDENCE_VERIFIED
→ LIVE_OR_PHYSICAL_EVIDENCE_VERIFIED
→ INDEPENDENT_SHADOW_PASS
→ HUMAN_ADMITTED
→ RELEASED
```

A completed issue may truthfully close a narrower method or canary lane while related live, durability, source-truth, release, or production lanes remain open in successor issues. State the exact ceiling. #467 is the canonical example: its source compiler method is completed, while #512 owns real Issue/Article/PDF/PRD evidence execution.

## PR terminal classification

Use only these meanings:

- `MERGED`: GitHub reports `merged=true`, and the exact checked head/tree and merge subject are known.
- `CLOSED_UNMERGED / CONSUMED`: exact bytes were admitted through another convergence or landing subject; never describe the source PR as individually merged.
- `CLOSED_UNMERGED / SUPERSEDED`: current shared-writer bytes advanced elsewhere; merging the old PR would restore stale state.
- `DRAFT / HOLD`: a prerequisite, current-main refresh, exact-head gate, live receipt, or provenance repair remains missing.
- `REJECTED`: a named falsifier, provenance gate, or Shadow finding failed.

Before closing an unmerged PR as consumed, read at least one decisive file or Git tree from both the PR head and current `main`, and name the actual admission surface.

## Issue terminal classification

An issue can close only when its own goal and close gate are satisfied. Do not close:

- #464 until a fresh v2 signed-in Codex run binds a durable result carrier and passes independent Shadow;
- #466 until a real managed Herdr lifecycle produces a terminal, clean, content-bound receipt;
- #508 until durable result-tree replay, exact executor provenance, and a strict worker-result schema pass their controls;
- #512 merely because #467 compilation passes; source truth, applicability, implementation, and verification remain separately typed and require exact source packets.

#467 is validly closed as the compiler/binding method owner. #465 is a valid closed live-canary lane because the owned remote edge was added, read back, removed, and the original denominator was restored on an exact hosted receipt.

## Writer and Shadow laws

- Tech Lead owns implementation/queue/index writes.
- Shadow is read-only and reviews the same immutable subject.
- Exactly one writer owns each shared index or convergence path.
- Path-disjoint work remains sibling work.
- A true child must consume named unmerged parent bytes or contracts.
- External runtime evidence is a process/evidence dependency, not an artificial Git parent.
- A queue never grants merge, force-push, issue-close, provider-activation, semantic-conflict, release, or rollback authority.

## Local Handoff law

Each queue must have:

```text
one immutable repository/commit/tree subject
exactly one ACTIVE item
bounded commands or one explicit unresolved command-contract operation
one receipt path and schema identity
PASS-required exit
forbidden evidence promotions
cleanup and Human authority
```

A one-item epoch is expected when the active item mutates the implementation subject. After it lands, compile the successor queue against the new subject rather than advancing a stale queue.

## Completion report

Report the exact implementation and documentation subjects, merged/closed/draft PR classifications, issue-state changes, runtime/source evidence ceilings, queue paths, active items, failed attempts retained in the denominator, rollback subject, and every `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `EVIDENCE_DEPENDENT`, `HUMAN_ADMIT_REQUIRED`, and `NOT_PERFORMED` state.
