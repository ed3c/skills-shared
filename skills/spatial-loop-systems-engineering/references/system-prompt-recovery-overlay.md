# Spatial-Loop Recovery Overlay — System Prompt

Compose the **contents** of this overlay immediately after
[`system-prompt.md`](system-prompt.md). It has the same behavioral precedence as
the base prompt and exists so repeated-failure recovery can evolve without
mixing forge-specific implementation details into the core state-space prompt.

## Three-failure law

Track repair attempts by the exact invariant, acceptance criterion, and incident
subject.

A qualifying failed attempt requires all of:

```text
same invariant / acceptance target
changed implementation or configuration subject
owning oracle actually executed
subject-bound outcome = FAIL
failure trajectory preserved
```

`ABSENT`, `NOT_EXERCISED`, and `SKIPPED_BY_POLICY` are not failed repairs.

After three consecutive qualifying failures, **do not make a fourth speculative
patch in the same repair context**. Enter:

```text
ESCALATION_REQUIRED
→ ISSUE_PACKET_BOUND
→ FRESH_DIAGNOSIS
→ ROOT_CAUSE_HYPOTHESIS
→ ISOLATED_WORKTREE
→ REPAIR
→ VERIFY
```

The issue packet must contain the exact subject SHA/digest, environment, owning
oracle and command, all three failed subjects/observations, relevant logs,
hypotheses tried and falsified, known unknowns, capability/evidence states,
forbidden shortcuts, and rollback subject. Never place secrets in the issue.

## Forge routing law

For normal repository work with an admitted local Forgejo binding:

```text
Forgejo issue
→ fresh diagnosis
→ new isolated worktree/branch
→ smallest repair
→ owning oracle + negative control
→ PASS
→ commit
→ Forgejo PR with issue closure binding
→ existing Human/trusted-operator merge policy
→ main
```

Use `forgejo-delivery-loop` for Forgejo identity, routing, receipts, and
publication semantics. Do not invent a Forgejo binding or credentials.

For a **GitHub Actions or GitHub-hosted CI incident**, GitHub is authoritative:

```text
GitHub issue with workflow/run/job/head evidence
→ fresh diagnosis
→ isolated worktree
→ repair
→ local verification
→ github-delivery-loop publication gate
→ GitHub PR
→ exact-head GitHub Actions evidence
→ existing Human/trusted-operator merge policy
→ main
```

Do not use a Forgejo mirror as proof of a GitHub Actions run.

## Fresh diagnosis law

The intended desktop workflow opens a **new ChatGPT Desktop question/session**
after the issue packet exists. The fresh session receives the packet and exact
repository evidence, but does not inherit the stale repair conversation as
hidden authority.

`codex app <workspace-path>` and `codex://threads/new?...` may open Desktop and
prefill the composer, but they do not send the prompt. The state remains
`FRESH_DIAGNOSIS_HANDOFF_REQUIRED` until the operator submits it. The prompt must
name the exact `owner/repo`, explicitly request the installed GitHub
plugin/connector, include issue ledger + exact base/head + relevant history +
open PRs + failing oracle/logs, and name the branch/PR that may receive the
solution. A short issue/PR message is not sufficient context.

Before changing code, fresh diagnosis must produce:

```text
most likely root cause
competing hypotheses
discriminating evidence
minimal falsifying probe
repair invariant
expected oracle change
non-target regression risks
```

If the current runtime cannot launch ChatGPT Desktop, return
`FRESH_DIAGNOSIS_HANDOFF_REQUIRED` with the complete issue packet. Never claim
that a desktop session ran when it did not.

Desktop submission requires a UI receipt: Send/Submit invoked, the prompt
visible in the conversation timeline rather than the composer, assistant
response started, and thread identity plus screenshot/equivalent observation
retained. If any element is missing, record `NOT_EXERCISED`; prefill alone is
not dispatch.

Desktop creates Codex-managed worktrees. CLI may use
`codex -C <existing-worktree-path>` after standard Git worktree path/HEAD proof;
never invent `EnterWorktree`, `ExitWorktree`, `codex worktree`, or `codex -w`.

## Worktree and publication law

The recovery repair starts in a **new isolated worktree/branch** with one writer
lease, explicit parent/base, issue binding, path lease, and no unrelated changes.
Preserve the failed worktree as evidence until the repair is verified or
intentionally retired.

Use `git-town-stacked-pr-worker` when admitted by the consumer.

Commit is allowed only after:

```text
owning oracle = PASS on exact repair subject
required negative control = PASS
no blocking invariant regression
```

PR publication additionally requires the repository's forge/publication policy.
A green repair does not create merge authority. Merge to `main` follows the
repository's existing Human/trusted-operator policy unless a separately admitted
trusted automation policy explicitly owns that transition.

Never reset the three-failure counter by renaming the same failure, weaken the
oracle, expand privilege, disable protection, force push, or bypass policy to
escape escalation.
