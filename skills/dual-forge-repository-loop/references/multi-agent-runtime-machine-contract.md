# Repository Multi-Agent Runtime Machine Contract

This reference turns the v2.1 system prompt's topology, Worker, Shadow, budget,
and merge-boundary laws into a deterministic offline gate.

## Authority boundary

```text
system-prompt.md
  = portable Agent procedure and stop conditions

multi-agent-runtime-contract.schema.json
worker-task.schema.json
worker-result.schema.json
  = structural vocabulary and closed fields

check_multi_agent_runtime.py
  = semantic authority for one submitted contract

consumer repository/runtime
  = real task packets, attempts, leases, checkpoints, receipts, branches,
    worktrees, provider observations, and live execution
```

The checker never creates Workers, worktrees, branches, issues, PRs, CI runs, or
merges. It validates a content-bound statement about those subjects. A passing
fixture is not live runtime evidence.

## Contract state

```text
RUNTIME_BOUND
→ TOPOLOGY_SELECTED
→ PARALLELISM_ADMITTED or SINGLE_BUILDER_FALLBACK
→ TASKS_AND_ATTEMPTS_BOUND
→ PATH_AND_RESOURCE_LEASES_BOUND
→ RESULTS_BOUND
→ OWNING_EVALS_AND_CONTROLS_BOUND
→ BUDGET_LEDGER_CLOSED
→ SHADOW_AND_MERGE_BOUNDARIES_CLOSED
→ CONTRACT_PASS
```

## Deterministic checks

The checker requires:

- exact repository base/current subjects in the admitted-subject set;
- `UNKNOWN` runtime to fail closed before commit/publication;
- a missing budget profile to degrade to one `SINGLE_BUILDER`;
- all quantitative consumption to stay within limits;
- every `MULTI_WORKER` admission predicate to be true;
- unique attempt, branch, and worktree identities; `task_id` names the logical
  slice and repeats across retries of that slice;
- an acyclic dependency graph with no unknown dependency;
- writable paths, mutable-state ownership, and external-resource leases to be
  disjoint between writers that are **concurrently leased**; a released
  predecessor may hand ownership to a successor that declares it as a
  dependency, and a reuse ordered by nothing is refused as an unordered handoff;
- path containment to be segment-aware, so `src/parser2` is a sibling of
  `src/parser` rather than a child of it;
- active tasks to hold active leases and terminal tasks to release them;
- an `ACTIVE` lease to expire strictly after `evaluation_time`;
- per logical task: at most one active attempt, at most one accepted
  verified/integrated attempt, attempts within `repository.max_attempts_per_task`,
  and every retry to name a terminal `parent_attempt_id` of the same slice —
  stale and superseded attempts remain terminal evidence, not duplicate tasks;
- every verified task to have one matching `worker-result/v1`;
- result base, attempt, and owned paths to match the task packet;
- every result head to appear in the admitted-subject set;
- a verified result's `checkpoint_identity` to equal its task attempt's non-null
  checkpoint digest;
- verified positive evals and negative controls to be `PASS` with evidence, and
  their IDs to equal the task's `required_evals` / `negative_controls` exactly —
  a passing oracle that is not the owning oracle is refused;
- closure-claiming delivery states (`LOCAL_VERIFIED` and every publication state)
  to require one accepted attempt with one accepted result per logical task;
- Worker and global budget ledgers to reconcile exactly;
- in-process logical Shadow review to remain `NOT_EXERCISED` for independence;
- an observed (`PASS`/`FAIL`) independence state on any other execution mode to
  carry `shadow.independence_evidence` naming where it was observed and which two
  identities it separated, and to refuse one identity on both sides — the rule
  above only ever refused the in-process overclaim, so a `SEPARATE_MODEL` review
  could assert independence with nothing behind it;
- L3 Shadow outcomes to be enforced and keep delivery `BLOCKED`;
- Agent merge action to remain `DENY`;
- merge eligibility and observed merge to remain external authority states.

## Recording the prompt that governs this contract

The contract above governs one run. A separate gate governs whether the System
Prompt driving those runs may become a *recorded* prompt at all:

```text
prompt prose
!= runtime execution
!= task success
!= portable effectiveness
!= recording authority
```

A prompt may exist as a candidate on a branch or in a Draft PR with evaluation
authority only. It enters an active registry, instruction projection, or default
Agent context only through `system-prompt-runtime-receipt/v1`, which binds exact
prompt bytes, the evaluation contract, the runtime and model identity, the
execution trace, a deterministic verifier result, and a scoped promotion decision.

```bash
python3 skills/dual-forge-repository-loop/scripts/check_system_prompt_record.py \
  path/to/system-prompt-runtime-receipt.json
# exit 0 supported | 2 claims authority the evidence does not carry | 64 invalid | 70 no jsonschema
```

Load-bearing refusals: `RECORDED` without a verifier PASS, without killed negative
controls, without replay, or without release admission; `PROJECTED` without
`RECORDED`; `PORTABLE_RECORD` backed by a single observed stack — portability is a
claim about more than one, and one stack wearing a portable label is the specific
overclaim this gate exists to stop. Declaring no negative controls is refused as
absent controls rather than accepted as passing ones. Honest terminal states stay
open: an unproven candidate and a refused candidate are both admitted, because a
receipt recording refusal is evidence, not a failure.

## Command

```bash
python3 skills/dual-forge-repository-loop/scripts/check_multi_agent_runtime.py \
  path/to/repository-multi-agent-runtime.json
```

Exit codes:

```text
0   structural and semantic closure PASS for the submitted contract
2   structurally valid contract violates a runtime invariant
64  absent, unreadable, malformed, or schema-invalid input
70  pinned schema validator unavailable; validation is not skipped
```

## Consumer-owned profile

Start from [`multi-agent-runtime-profile.template.json`](multi-agent-runtime-profile.template.json),
then keep the filled profile in the consuming repository. Shared Skills do not own
consumer budgets, branches, paths, runtime identities, or live receipts.

## Evidence boundary

The deterministic gate proves only the contract relationships it replays. It
cannot prove:

- a live multi-Agent scheduler or model process ran;
- a separate Shadow context/model was actually independent — the gate checks that
  a claim of independence is bound to evidence, never that the bound evidence is
  sound; the live canary behind that binding is
  `skills/procedural-shadow-runtime/evals/receipts/shadow-canary.receipt.json`
  and covers one Builder provider, one Shadow provider and one disposable subject;
- heartbeats, lease expiry, checkpoint/resume, or straggler cancellation occurred;
- Git Town synchronized a real stack;
- Forgejo/GitHub/provider observations are authentic unless separately captured;
- organization-level alignment, production safety, legal acceptance, or merge authority.

Those remain `NOT_EXERCISED` until an owning environment emits exact-subject
evidence.
