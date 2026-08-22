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

Every queue JSON in `skills/agentic-tech-lead-orchestration/runtime-handoff/` is a projection over the subject **it** was compiled against. There is no single shared subject and no fixed number of queues: read the `subject` field of the exact queue you are acting on, and never infer it from a sibling queue or from a documentation projection such as this one (`../../../skills/agentic-tech-lead-orchestration/runtime-handoff/AGENTS.md:28` states the rule for the Spatial queue explicitly).

The Wave-3 continuation queues (`codex-v2`, `herdr`, `source-evidence`) were compiled against and executed on the PR #516 subject `249abc47847f8295b1c75c9d4c84457c5126fd89` / tree `a24b9b7ace6f4022967d41262ecdc704d5c11646` / rollback `d5993267e03b217dcdab9702dab0400ab03df860`. That commit is also the `parent_commit` of the #508 result-carrier receipt, whose own `implementation_commit` is `243635885f7bcff64c606dffe7fcbe09ada9c5b2` — the two are not interchangeable, and neither is "the receipt-bound subject" of the other.

Admitted `main` had advanced to `129f53c23a3ab15354763167b25bddc45f724c00` when this file was written (PR #511 was the docs-only merge with an empty diff against the owning scripts; PR #516 then landed the #508 implementation on branches cut from the receipt-bound subject). `main` has since advanced repeatedly — through `28f3947` (PR #571), `5341885` (PR #574, the #560 Repository Portfolio Control wave; see `docs/traceability/github-portfolio-control/`), and `674cfe1` (PR #577, the DTCR handoff-queue truth-surface repair) — so `129f53c` is no longer current `main`; always re-derive via `git rev-parse main`. A later documentation merge does not rewrite the receipt-bound subject above. Any implementation change to a queued lane makes the old queue stale and requires a newly compiled queue bound to the newly admitted commit and tree — for #464 this happened on 2026-08-22: the successor queue `codex-v2-live-464-local-handoff-queue.json` was compiled fresh against its own merged implementation head (not appended to the historical `codex-v2-local-handoff-queue.json`, and not bound to the stale `129f53c`), and its live run executed with verdict `PASS`, Shadow pending.

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

- #464 until its live v2 signed-in run — executed 2026-08-22 via `codex-v2-live-464-local-handoff-queue.json` with a committed durable carrier and receipt verdict `PASS` — also passes independent Shadow readback (currently `SHADOW_PENDING`);
- #466 until a real managed Herdr lifecycle produces a terminal, clean, content-bound receipt that also passes independent Shadow — PR #516's receipt was `NOT_EXERCISED` with `sample_count: 0` (blocker RECLASSIFIED to the herdr-0.8.0 `AgentInfo` API-contract mismatch); on 2026-08-22 the observer contract was renegotiated (named-session isolation) and a live lifecycle ran with `sample_count: 20` (`data/handoff/herdr-v3/herdr-lifecycle-receipt.json`, ceiling `LIVE_OBSERVER_LIFECYCLE_SHADOW_PENDING`), so the remaining gate is Shadow readback plus the clean terminal state;
- #512 merely because #467 compilation passes; source truth, applicability, implementation, and verification remain separately typed and require exact source packets. PR #516 executed the first such packet (GitHub issue #435 bytes); the repair itself (classifying six unclassified commits in `evals/commit-roles.json`) has since landed via commit `a2761542`, and the ledger now carries honest dispositions with a 2026-08-22 Shadow binding — verification and further source kinds (PDF/PRD) remain open.

#467 is validly closed as the compiler/binding method owner. #465 is a valid closed live-canary lane because the owned remote edge was added, read back, removed, and the original denominator was restored on an exact hosted receipt. #508 is `CLOSED / COMPLETED` at the 2026-08-22 readback, with a validated `PASS` receipt as the durable-carrier/provenance/schema owner (PR #516); its closure does not claim a live #464 acceptance, which remains a separate `NOT_EXERCISED` lane.

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
