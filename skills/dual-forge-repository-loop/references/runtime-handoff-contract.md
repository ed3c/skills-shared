# Runtime Handoff Contract

[`runtime-identity-contract.md`](runtime-identity-contract.md) says what each
runtime may claim. It does not say what happens when one of them runs out of
capability halfway through a task, which is the situation that actually occurs.

This contract covers that: splitting work across runtimes before starting, and
passing it on when a boundary is hit.

## The failure it exists to prevent

A runtime that cannot perform a step has three ways to proceed and two of them
are wrong:

```text
weaken the gate that caught it        removes the check for every future caller
fabricate the missing evidence         the substitution every gate here exists to refuse
hand off with the blocker named        costs a round trip and nothing else
```

The third is only available if the handoff carries enough for the receiver to
resume without rediscovering the problem. A handoff that says "this failed, over
to you" is a rediscovery request, not a handoff.

## Worked example: issue #255

A `CHATGPT_GITHUB_CONNECTOR` session reconciled a staged bundle, opened a PR, and
triggered exact-head CI. Every gate passed except one:

```text
COMMIT ROLE RED: 0e9514ce74d8: Driven-By agent-macro is a machine role but the
author address 'mcnum01@gmail.com' is not a <role>@<host>.invalid address
```

GitHub's Git-Data `create_commit` exposes message, tree and parents but not
author or committer identity, so a connector-written commit necessarily carries
the linked account's real address. The connector could not fix its own commit,
and neither weakening the gate nor writing `Driven-By: human` was admissible.

Its handoff named the exact blocker, the exact tree to recreate, the exact
identity to use, and what would count as done. A `CLAUDE_CODE_LOCAL` session
re-authored the same tree with `agent-macro <agent-macro@codex-app.invalid>` and
landed it green. Total local work: one cherry-pick and one commit.

That is the shape this contract generalizes. The capability that was missing is
now a row in the matrix instead of a discovery.

## Capability matrix

Each cell records a verdict **and how it was established**, because a capability
table nobody grounded is a table that will be believed anyway.

```text
OBSERVED         measured in this repository, with a pointer to the observation
OBSERVED_ABSENT  measured and found missing, with the exact failure
DECLARED         stated by runtime-identity-contract.md or vendor documentation
UNKNOWN          neither measured nor declared; treat as absent for planning
```

| Capability | CHATGPT_GITHUB_CONNECTOR | CLAUDE_CODE_LOCAL | CODEX_CLI_LOCAL | GITHUB_ACTIONS |
|---|---|---|---|---|
| `github_read` | OBSERVED | OBSERVED | DECLARED | DECLARED |
| `github_commit_create` | OBSERVED | OBSERVED | DECLARED | DECLARED |
| `git_author_identity` | **OBSERVED_ABSENT** | OBSERVED | DECLARED | DECLARED |
| `local_checkout` | DECLARED absent | OBSERVED | DECLARED | DECLARED (CI workspace) |
| `local_shell` | DECLARED absent | OBSERVED | DECLARED | DECLARED |
| `git_worktree` | DECLARED absent | OBSERVED | DECLARED | UNKNOWN |
| `forgejo_loopback` | DECLARED absent | OBSERVED | UNKNOWN | DECLARED absent |
| `provider_execution` | DECLARED absent | OBSERVED | UNKNOWN | UNKNOWN |
| `agent_session_spawn` | UNKNOWN | OBSERVED | OBSERVED | UNKNOWN |
| `actions_execution` | DECLARED absent | DECLARED absent | DECLARED absent | OBSERVED |

`DECLARED absent` entries come from the non-equivalence laws already in
[`runtime-identity-contract.md`](runtime-identity-contract.md); they are not new
policy. `UNKNOWN` is planned around as absent, and a step that needs it must
either probe first or route elsewhere.

The one bold cell is the whole reason this file exists. It was not predictable
from the runtime's description — it had to be run into.

## Handoff packet

A packet binds the subject, the steps, and who can perform each one:

```text
subject            repository, exact commit and tree at handoff
sender             runtime identity, and what it completed
blocker            the exact observation that stopped it, reproducibly
steps              each with required capabilities and an assigned runtime
receiver           runtime identity, and the capabilities it must have
done_when          the condition that ends the handoff, checkable by the receiver
```

Shape: [`runtime-handoff.schema.json`](runtime-handoff.schema.json). A validated
instance built from #255: [`runtime-handoff.example.json`](runtime-handoff.example.json).

```bash
python3 skills/dual-forge-repository-loop/scripts/check_runtime_handoff.py \
  check --packet path/to/handoff.json
python3 skills/dual-forge-repository-loop/scripts/check_runtime_handoff.py selftest
```

## What the checker refuses

| Code | Refused shape |
|---|---|
| `STEP_EXCEEDS_RUNTIME` | a step assigned to a runtime whose matrix row lacks a capability the step requires |
| `IDENTITY_LAUNDERED` | a step that writes a commit assigned to a runtime without `git_author_identity`; the #255 failure, generalized |
| `CAPABILITY_UNEVIDENCED` | a capability marked available with no evidence grade, or `OBSERVED` with no pointer |
| `HANDOFF_WITHOUT_BLOCKER` | a packet with no blocker, or a blocker with no reproducible observation |
| `RECEIVER_CANNOT_RESUME` | the receiver lacks a capability some remaining step needs |
| `NO_TERMINAL_OWNER` | a step no admitted runtime can perform and no human is assigned |
| `SUBJECT_UNBOUND` | no exact commit and tree at the handoff point |
| `DONE_CONDITION_UNCHECKABLE` | a completion condition the receiver cannot evaluate |

`NO_TERMINAL_OWNER` is the one that turns a stuck task into a human decision
rather than a loop. If no runtime can do a step, that is a fact about the task,
and the packet has to say so instead of assigning it to whoever is next.

## What a handoff is not

It does not transfer evidence. A receipt produced under one runtime stays bound
to that runtime, and the receiver re-establishes anything it wants to claim —
[`runtime-identity-contract.md`](runtime-identity-contract.md) already says
previous environment evidence does not automatically transfer.

It does not transfer authority. Merge, promotion, permission widening and
release admission stay where they were before the handoff.

It does not make two runtimes one writer. One mutable branch still has one
active writer; a handoff moves the lease, it does not share it.
