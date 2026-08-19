# Issue #377 — Herdr observer execution packet

Replacement base: `4ca9417b1da5ff32f1d4d3e7af64a15908749024`  
Historical candidates: PR #446 → PR #453 (closed, not merged)  
Convergence: #379

## Read order

Root Agent/document routes → Agentic Tech Lead nearest AGENTS/README/SKILL → scheduler/worktree/Local Handoff contracts → runtime boundary docs → issue #377. Consumer examples are reference instances only.

## Writable lease

Only issue-owned Herdr observer module, receipt schema, abstract binding example, execution packet, runtime observer and dedicated selftest under the Agentic Tech Lead Skill. Shared README/AGENTS/traceability/Git Town indexes are read-only; #379 owns convergence.

## State machine

```text
WORKTREE_ALLOCATED
→ HERDR_WORKSPACE_BOUND
→ AGENT_PROCESS_OBSERVED
→ WORKTREE_AND_SESSION_IDENTITY_BOUND
→ FRESHNESS_AND_LIVENESS_BOUND
→ RUNNING | BLOCKED | IDLE | DONE_CANDIDATE | UNKNOWN
→ CLEANUP_RESIDUE_OBSERVED_WHEN_TERMINAL
→ CONTROLLER_READBACK
→ RECEIPT_VERIFIED
```

## Required contract

Bind task, attempt, exact 40-hex repo base/tree, worktree, workspace/pane/process identity, process start-time, native session, fresh source observation time/state and cleanup/residue. Herdr may observe and expose attach/steer/human-takeover metadata. It may not decide semantic dependencies, acceptance PASS, issue close, merge, release or evidence promotion. `DONE_CANDIDATE` is never completion. Preserve direct Codex SDK + standard git worktree fallback when Herdr is absent.

## Shadow controls

Refuse terminal-DONE laundering, wrong pane/worktree, stale/reused process identity, future/stale observation, dead nonterminal process, orphan session, incomplete cleanup/residue, credential capture, private-reasoning/transcript capture and observer-state substitution for controller receipts.

## Completion gate

Dedicated deterministic positive PASS; every planted identity/freshness/liveness/cleanup mutation refused; fallback preserves the same completion boundary; repository-wide exact-head workflows remain green. Live Herdr observation remains `NOT_EXERCISED` until a consumer/runtime receipt exists. #379 alone owns aggregate test-suite/README/index convergence.
