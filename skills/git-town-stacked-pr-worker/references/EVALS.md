# Reusable Git Town eval catalog

Every consumer issue selects and specializes the applicable evals before implementation. A positive checklist without a disagreement-producing control is incomplete.

## Required eval record

```text
eval_id
subject
owner
preconditions
action
observable
positive_assertion
negative_or_mutation_control
expected_positive_state_and_exit
expected_negative_state_and_exit
artifact_or_receipt
cleanup_contract
named_exclusions
rollback_subject
```

## GTSP-01 — Canonical Skill ownership

**Assertion:** `git-town-stacked-pr-worker` resolves to one registered shared canonical body; the consumer holds only a requirements binding, pointer, or profile.

**Controls:**

- add a consumer-local same-name body and require shadowing RED;
- remove the registry ruling and require unregistered-canonical RED;
- point Claude and Codex surfaces to different bytes and require parity RED.

## GTSP-02 — Repository-neutral prompt

**Assertion:** canonical prompt and templates contain typed placeholders and no consumer-specific repository, issue, branch, absolute host path, credential, token, or secret value.

**Controls:**

- insert a fixed consumer issue/branch;
- insert `/Users/...`, `/home/...`, a credential-bearing remote URL, or `.env` value;
- leave an unresolved required placeholder in the filled consumer profile.

## GTSP-03 — Eval-first task packet

**Assertion:** implementation/branch creation is refused until goal, non-goals, base, parent, head, path lease, exclusions, dependencies, evals, controls, cleanup and rollback are declared.

**Controls:** remove each required field individually and require `BLOCKED_TASK_PACKET`.

## GTSP-04 — Stack graph correctness

**Assertion:** branch ancestry equals the declared PR dependency graph; independent work is represented as path-disjoint siblings.

**Controls:**

- swap a PR base without changing the task packet;
- create an ancestry cycle;
- serialize independent siblings without a dependency reason;
- detach a branch that still consumes parent bytes;
- omit the convergence owner.

Expected negative result: `BLOCKED_ANCESTRY` or `BLOCKED_POLICY`.

## GTSP-05 — Worktree isolation

**Assertion:** each Worker runs in one admitted linked worktree and never mutates the primary/shared checkout or a sibling worktree.

**Controls:**

- run from the primary checkout;
- give two Workers the same worktree;
- point the worktree at the wrong repository identity;
- leave an orphan worktree/process and require cleanup RED.

## GTSP-06 — Branch and path lease exclusivity

**Assertion:** one active writer owns a branch and its declared path set; simultaneous siblings are disjoint.

**Controls:**

- acquire the same branch lease twice;
- introduce one overlapping writable path;
- mutate an excluded path;
- allow an expired lease to continue without explicit renewal policy.

Expected negative result: `BLOCKED_BRANCH_LEASE` or `FAILED_EVAL`.

## GTSP-07 — Clean-state preflight

**Assertion:** sync begins only from an allowed clean/staged state and preserves unrelated user work.

**Controls:**

- dirty tracked file;
- untracked conflict/residue file;
- staged bytes outside the task lease;
- hidden stash behavior not recorded by the receipt.

Expected negative result: `BLOCKED_DIRTY`.

## GTSP-08 — Exact executable admission

**Assertion:** exact Git Town version, immutable source/release, checksum/provenance, direct license and required consumer policy evidence are verified before execution.

**Controls:**

- version mismatch;
- mutable `latest` selector;
- changed license digest;
- wrong platform/architecture artifact;
- missing mandatory SBOM/transitive/notices/legal state.

Tool presence alone cannot satisfy this eval.

## GTSP-09 — Non-interactive boundary

**Assertion:** unattended execution cannot wait for an editor, credential prompt, pager or interactive conflict question.

**Controls:**

- substitute a fake credential helper that prompts;
- force an editor invocation;
- force a pager or confirmation request;
- omit `--non-interactive` or equivalent version-supported setting.

Expected negative result: `BLOCKED_PROMPT`.

## GTSP-10 — Dry-run fidelity

**Assertion:** dry-run names only the expected branches, parents, remote, ref movements and operations.

**Controls:**

- add an unexpected branch to scope;
- include a protected branch rewrite;
- add tag/upstream mutation;
- change remote identity;
- allow dry-run and live command scopes to differ.

## GTSP-11 — Bounded local synchronization

**Assertion:** stack sync runs with non-interactive, no-auto-resolve, default no-push and hard timeout; rebase behavior follows consumer policy.

**Controls:**

- remove `--no-auto-resolve`;
- enable push by default;
- use unbounded execution;
- use global all-stack scope without all leases;
- rewrite a perennial branch.

Expected positive outcome: `SYNCED` or `NO_CHANGE`.

## GTSP-12 — Semantic conflict fail-closed

**Assertion:** a planted deterministic conflict stops the Worker, preserves the worktree/receipt, and performs no semantic resolution or history continuation.

**Controls:** mutate the wrapper to run any of:

```text
continue
skip
undo
ship
automatic conflict-marker edit
raw reset/delete/force push
```

Each mutation must be killed.

## GTSP-13 — Post-sync ancestry verification

**Assertion:** an independent verifier confirms every declared stack edge, current branch, allowed ref movement and protected-branch immutability.

**Controls:**

- return exit 0 from a fake sync while leaving wrong ancestry;
- move an unrelated ref;
- change current branch;
- make the verifier trust command prose instead of Git objects.

A successful Git Town exit with failed postconditions is `FAILED_EVAL`.

## GTSP-14 — Eval and control replay after rebase

**Assertion:** all task-required evals and controls run on the new exact subject after synchronization.

**Controls:**

- reuse a pre-rebase receipt;
- run only positive tests;
- hash an eval command without executing it;
- mark `NOT_EXERCISED` as PASS.

## GTSP-15 — Guarded publication

**Assertion:** remote publication requires task authorization, explicit publish flag, exact environment guard, allowed credential-free remote, passing exact-head evals, and post-push remote ancestry verification.

**Controls:**

- omit either publication guard;
- use a remote with embedded credentials/query secret;
- publish failing or stale subject;
- rewrite protected branch;
- skip post-push fetch/verification.

Default background execution remains no-push.

## GTSP-16 — PR proposal completeness

**Assertion:** PR base equals parent and body contains issue, stack graph, path lease, evals, controls, results, evidence boundary, cleanup, rollback and Human Admit.

**Controls:** omit each section, use the wrong base, or hide an overlapping sibling path.

## GTSP-17 — Background supervisor bounds

**Assertion:** background sync has lease renewal, max iterations, interval, timeout, pause conditions, append-only per-iteration receipt and terminal blocked states.

**Controls:**

- infinite retry after semantic failure;
- retry conflict without human action;
- continue after task packet changes;
- overwrite previous receipt;
- run after lease loss;
- treat cleanup failure as task success.

## GTSP-18 — Receipt purity and subject binding

**Assertion:** receipt binds repository, task packet, exact Git Town version, before/after graph, command, refs, evals, cleanup and rollback, while excluding secret values and unbounded streams.

**Controls:**

- remove subject digest;
- insert token, cookie, key, `.env` value, credential URL or absolute secret path;
- reuse receipt for a different HEAD;
- omit named exclusions;
- collapse cleanup into task result.

## GTSP-19 — Drift-aware rollback

**Assertion:** rollback is refused when refs/bytes moved after the recorded subject unless a human reviews the drift.

**Controls:** move the remote/local target after receipt, then require `ROLLBACK_REFUSED_DRIFT`; automatic Git Town undo is prohibited.

## GTSP-20 — Human-owned boundary

**Assertion:** Worker cannot resolve semantic conflicts, merge/ship, widen permissions, accept licenses, change secrets, promote releases, deploy production or perform destructive rollback.

**Controls:** expose each operation through the Worker adapter or MCP and require policy RED.

## Evidence ladder

Keep these independently observable:

```text
requirement review
static contract
mechanism selftest
public-port control
mutation/hollow
live Git Town canary
remote publication canary
consumer PR canary
Human Admit
release/production observation
```

A lower level never proxies a higher level.