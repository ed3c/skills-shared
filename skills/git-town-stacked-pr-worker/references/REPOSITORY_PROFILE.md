# skills-shared Git Town repository profile

Makes this repository an explicit consumer of the admitted Git Town method.
Validated by [`../scripts/check_repository_profile.py`](../scripts/check_repository_profile.py).

## Supported configuration storage

Git Town 24.0.0 reads two stores, and this repository uses both for different
purposes. Observed against the admitted binary, not inferred:

```text
.git-town.toml            checked in; the binary documents it as
                          "which you commit"; repository policy
git config git-town.*     clone-local; OVERRIDES the committed file
```

No other configuration file is invented here. `git-town config setup` does not
exist at 24.0.0 and `git-town init` is interactive, so the non-interactive
surfaces are exactly these two.

## What this profile does not enforce

**A clone-local `git config git-town.main-branch` beats `.git-town.toml`.**
Confirmed by experiment: setting the Git config changed the effective trunk while
the committed file was unchanged, and unsetting it restored the file's value.

So this profile is policy, not a boundary. It states what a correctly configured
clone should do. It cannot stop a clone from doing otherwise, and nothing here
should be read as if it could. The enforcement boundaries that do hold are
elsewhere: `github-delivery-loop`'s merge gate, the repository's PreToolUse
hooks, and GitHub's own branch rules.

A second silent failure mode the validator exists for: **Git Town ignores keys it
does not recognise.** A misspelled key produces a file that parses cleanly, reads
correctly, and has no effect. `ADMITTED_KEYS` in the validator therefore lists
only keys observed taking effect in a real `git-town config` run, and any other
key is refused rather than passed through.

## Trunk and perennial branches

```text
main branch    main        equals the repository's GitHub default branch
perennials     []          declared empty: there are no long-lived release lines
```

`main` is perennial by type in Git Town's model, so it is not repeated in the
`perennials` list — repeating it is refused.

An empty list is a declaration. Omitting the key would be an absence, and the
validator distinguishes the two.

## Synchronisation strategy

```text
feature-strategy     rebase     keeps a stacked leaf's own commits contiguous
                                when its parent moves, which is what makes a
                                stack reviewable one leaf at a time
perennial-strategy   ff-only    a perennial branch never acquires merge commits
                                from a sync
auto-resolve         false      DEFAULT IS TRUE
push-branches        false      DEFAULT IS TRUE
tags                 false      DEFAULT IS TRUE
```

The three overridden defaults matter more than the two chosen strategies. Git
Town 24.0.0 ships with phantom-conflict auto-resolution, branch pushing, and tag
syncing all **on**. For an unattended Worker each of those is wrong:

- a conflict it cannot judge must stop, and a silently resolved semantic conflict
  is indistinguishable from one that never occurred;
- background synchronisation must never publish;
- tags are release identity, and a sync has no business moving them.

The Worker also passes `--no-push` explicitly. The profile makes the default
match the requirement rather than relying on every caller remembering the flag.

## Lease roots

A lease is the claim that one Worker owns a branch and a set of paths, so two
Workers cannot edit the same bytes concurrently.

```text
branch lease root   refs/heads/<family>/<nn>-<slug>
                    families in use: ibc/, ctl/, feat/, fix/, docs/, ci/, agent/

path lease root     one Skill directory, or one docs subtree, per active leaf
                    skills/<skill-name>/**
                    docs/<area>/**

worker lease root   one in-progress leaf per family at a time
```

Sibling leaves must hold disjoint path leases. Overlapping paths make a sibling
pair a false sibling: they are really a stack, and merging them independently
produces the add/add conflicts that a squash merge then makes hard to read.

Leases are declared, not enforced by this file. The enforcement surface is the
stack contract in [`STACK_CONTRACT.schema.json`](STACK_CONTRACT.schema.json) and
its checker.

## Publication gate

```text
.github-delivery/ci-policy.json     ABSENT
```

This repository is **not** enrolled in the canonical private CI publication
policy — that is issue #82, and it is open. So:

- `github-delivery-loop`'s `ci_publish.py` fails closed here, by design;
- a raw `git push` to GitHub is not gated by `ci_publish_guard.py` in this
  repository, because the guard only fires for enrolled repositories;
- publication cadence is therefore currently governed by discipline and by the
  workflow trigger types, not by a gate.

Recording it as `ABSENT` rather than omitting it is the point: an unstated
publication gate reads as a present one.

## Merge and ship

`git-town ship` is merge. Merge here goes through
`github-delivery-loop`'s `merge_gate.py` with its four-layer authority stack, so
no Git Town shipping path is admitted for automated use. The validator refuses
`git-town ship` or a force push appearing in an executable position anywhere in
this Skill.

The `[ship]` values in the profile exist so that a **human** running `git-town
ship` interactively gets the repository's squash-merge convention rather than a
different default. They do not admit automated shipping.

## Evidence boundary

```text
checked-in profile validated statically      IMPLEMENTED
keys observed taking effect at 24.0.0        EXERCISED (disposable repository)
this repository's real branch graph          NOT_EXERCISED
Worker execution against this profile        NOT_EXERCISED
publication                                  NOT_EXERCISED — gate ABSENT
merge / ship                                 HUMAN_ADMIT_REQUIRED
```

The disposable canary in `tests/live-git-town/` proves the executable and fixture
behaviour. It does not prove this repository's clone-local configuration, real
branch graph, Workers, publication, or merge.
