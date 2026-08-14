# Three-Failure Escalation Contract

This contract prevents an Agent from repeatedly patching the same failing subject
inside one stale context. It is a recovery protocol, not a permission to skip the
owning verifier or merge policy.

## Trigger

Count an attempt only when all of the following are true:

- it targets the same invariant, acceptance criterion, or incident subject;
- it changes the exact implementation subject or its configuration;
- the owning oracle actually executes;
- the oracle returns a subject-bound `FAIL` rather than `ABSENT`,
  `NOT_EXERCISED`, or `SKIPPED_BY_POLICY`;
- the failure trajectory is recorded.

After **three consecutive qualifying failures**, the current repair loop enters
`ESCALATION_REQUIRED`. A fourth speculative patch in the same repair context is
forbidden.

```text
ATTEMPT_1 --FAIL--> ATTEMPT_2 --FAIL--> ATTEMPT_3 --FAIL-->
ESCALATION_REQUIRED
    -> ISSUE_PACKET_BOUND
    -> FRESH_DIAGNOSIS
    -> ROOT_CAUSE_HYPOTHESIS
    -> ISOLATED_WORKTREE
    -> REPAIR
    -> VERIFY
        |- FAIL -> update issue evidence; do not silently reset history
        `- PASS -> COMMIT_ELIGIBLE -> PR_ELIGIBLE -> HUMAN_MERGE_BOUNDARY
```

A changed invariant or acceptance target starts a new counter only when the issue
records why the subject changed. Renaming the same failure does not reset the
counter.

## Issue packet

The escalation issue must preserve enough information for a fresh diagnostician
to reproduce the problem without inheriting the failing conversation as hidden
authority:

```text
exact repository / component
exact commit or artifact digest
target environment identity
invariant / acceptance criterion
owning oracle and exact command
three attempt subjects
three observed failures and relevant logs
hypotheses tried
hypotheses falsified
permissions / capabilities / evidence states
known unknowns
forbidden shortcuts
rollback subject
```

Do not paste secrets, credential-bearing URLs, browser profiles, tokens, or other
private runtime material into the issue.

## Forge routing

For a normal repository bound to the local Forgejo delivery plane:

```text
three qualifying failures
-> create/open Forgejo issue in the admitted repository and milestone
-> attach the failure packet
-> fresh diagnosis
-> new isolated worktree + one-writer branch lease
-> implement smallest falsifiable repair
-> run owning oracle + negative control
-> PASS
-> commit
-> Forgejo PR with issue closure link
-> repository Human/trusted-operator merge policy
-> main
```

Use `forgejo-delivery-loop` for issue/PR identity, routing, receipts, and the
existing Human Admit boundary. The shared method does not invent a Forgejo
repository, credentials, milestone, or merge authority when the consumer has no
binding.

## Fresh ChatGPT Desktop diagnosis

The intended operator workflow uses a **new ChatGPT Desktop question/session**
after the issue packet exists. The fresh session receives the issue packet and
exact repository evidence, but it does not treat the previous repair
conversation as authoritative context.

The fresh diagnosis must output, before code changes:

```text
most likely root cause
competing hypotheses
which evidence distinguishes them
minimal falsifying probe
repair invariant
expected oracle change
non-target regression risks
```

This is a host/operator transition. An Agent runtime that cannot launch ChatGPT
Desktop must stop at `FRESH_DIAGNOSIS_HANDOFF_REQUIRED` and provide the exact
packet to the operator; it must not pretend that a fresh desktop session ran.

## Worktree law

The repair is implemented in a new isolated worktree/branch, not by continuing
to mutate the failed worktree.

Required properties:

- one writer lease;
- exact parent/base identity recorded;
- issue packet linked;
- path lease explicit;
- no unrelated changes;
- original failed worktree remains available as evidence until the repair is
  verified or intentionally retired.

Use `git-town-stacked-pr-worker` when the repository admits Git Town. Git Town
synchronization is not implementation proof and does not grant merge authority.

## GitHub Actions exception

When the incident is a **GitHub Actions or GitHub-hosted CI failure**, GitHub is
the incident/publication authority:

```text
three qualifying GitHub CI repair failures
-> GitHub issue with exact workflow/run/job/head evidence
-> fresh diagnosis
-> isolated worktree
-> repair
-> local owning verification
-> github-delivery-loop publication gate
-> GitHub PR
-> exact-head GitHub Actions evidence
-> Human/trusted-operator merge policy
-> main
```

Do not mirror a GitHub Actions incident into Forgejo as if Forgejo could provide
the authoritative run/job evidence. Use GitHub Actions logs and exact workflow
run identity through the GitHub debugging/publication path.

## Commit and PR gate

A diagnosis is not commit eligibility. A code diff is not PR eligibility.

```text
COMMIT_ELIGIBLE
  = owning oracle PASS on exact repair subject
    + required negative control PASS
    + no blocking invariant regression

PR_ELIGIBLE
  = COMMIT_ELIGIBLE
    + clean issue/subject binding
    + repository publication policy satisfied
```

If verification remains `FAIL`, `ABSENT`, or `NOT_EXERCISED`, update the issue
with new evidence and stay out of the commit/PR success path.

## Merge boundary

A successful repair may proceed to the forge-native PR and the repository's
existing merge process. This contract does **not** convert test success into
merge authority. If the consumer explicitly grants a trusted automation path,
that path may execute the admitted merge; otherwise Human Admit remains
required.

Never broaden credentials, disable branch protection, bypass hooks, force push,
or weaken the verifier in order to complete the recovery loop.
