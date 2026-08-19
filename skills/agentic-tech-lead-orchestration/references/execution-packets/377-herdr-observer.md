# Issue #377 — Herdr observer execution packet

Base: `85e6723869bdd545666e07b7c5c6a8f491256cb9`
Branch: `ctl/377-herdr-runtime-observer`
Prep: #381 / #384
Convergence: #379

## Read order

Root Agent/document routes → Agentic Tech Lead nearest AGENTS/README/SKILL → scheduler/worktree/Local Handoff contracts → runtime boundary docs → issue #377. Bettor examples are reference instances only.

## Writable lease

Only issue-owned Herdr observer module, observer receipt schema, checker/tests/fixtures under the Agentic Tech Lead Skill. Shared README/AGENTS/traceability/Git Town indexes are read-only; #379 owns convergence.

## State machine

`WORKTREE_ALLOCATED → HERDR_WORKSPACE_BOUND → AGENT_PROCESS_OBSERVED → RUNNING | BLOCKED | IDLE | DONE_CANDIDATE → CONTROLLER_READBACK → RECEIPT_VERIFIED`.

## Required contract

Bind task, attempt, repo/base/tree, worktree, workspace/pane/process identity, observation time/state and cleanup. Herdr may provision/observe and expose attach/steer/human-takeover metadata. It may not decide semantic dependencies, acceptance PASS, issue close, merge, release or evidence promotion. `DONE_CANDIDATE` is never completion. Preserve direct Codex SDK + standard git worktree fallback when Herdr is absent.

## Shadow controls

Refuse terminal-DONE laundering, wrong pane/worktree, stale/reused process identity, orphan session, incomplete cleanup/residue, credential capture, private-reasoning capture and observer-state substitution for controller receipts.

## Zero-context worker prompt

Implement issue #377 on this branch only. Keep Herdr optional and non-authoritative. Require controller source/diff/test/result readback after observation. Add deterministic positive and mutation controls plus fallback behavior. Do not copy Bettor state into shared core or edit convergence docs. Return exact subjects, changed paths, observer contract, mutation denominator, fallback result, residue/cleanup, evidence ceiling and #379 handoff. Do not claim live Herdr execution from static bytes.

## Completion gate

Positive observer contract PASS; all identity/state/credential/residue mutations refused; fallback preserves the same completion boundary; affected Skill suites remain green; live Herdr observation remains `NOT_EXERCISED` until a consumer/runtime receipt exists.
