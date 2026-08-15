# Adoption contract for a new repository

This document retargets the shared method without creating a second canonical prompt.

## 0. Decide ownership before copying anything

```text
skills-shared
  owns: portable method + system prompt + generic eval language

consumer repository
  owns: repo profile + AGENTS routing + Git Town config + Bash wrappers + CI + receipts

host/runtime
  owns: executable installation + checksum/provenance/SBOM + credentials

human/trusted operator
  owns: legal acceptance + semantic conflicts + merge/ship + promotion + rollback
```

Do not copy this Skill into `<repo>/.agents/skills/git-town-stacked-pr-worker`. A project-local copy shadows the shared canonical body. Use a requirements-filtered binding, user-level shared Skill installation, or a thin repository pointer.

## 1. Repository preflight

Before adoption, inspect:

- default and protected branches;
- current branch/PR strategy;
- existing `AGENTS.md`, architecture and Harness documents;
- path ownership and generated-file ownership;
- current Git hooks and CI;
- remote names and branch protection;
- worktree support on the execution host;
- whether feature-branch history rewriting is allowed;
- existing delivery Skills and forge-specific rules;
- legal policy for third-party executables.

Record unsupported or unknown facts as `ABSENT` or `NOT_EXERCISED`. Do not make Git Town the first mechanism that defines repository authority.

## 2. Create a repository-owned profile

Copy [`REPO_PROFILE.template.md`](REPO_PROFILE.template.md) to a consumer-owned location such as:

```text
docs/git/REPO_PROFILE.md
```

Fill every required field. The canonical prompt must remain free of repository names, issue IDs, absolute host paths, remote credentials and secret values.

## 3. Add thin Agent routing

Add a short pointer to the consumer root `AGENTS.md`; do not duplicate the complete shared prompt.

Suggested routing text:

```markdown
## Git Town and Stacked PR work

Before creating, synchronizing, publishing or retargeting a stacked branch, read:

1. the shared `git-town-stacked-pr-worker` Skill;
2. `docs/git/REPO_PROFILE.md`;
3. the repository Git/Stacked-PR governance document;
4. the Harness/eval contract;
5. the assigned issue/work packet and nearest README files.

Git Town owns synchronization only. Semantic conflicts, merge/ship, legal acceptance,
permission widening, promotion and production rollback remain human/trusted-operator actions.
```

Claude/Codex projections should point to the same canonical bytes through the repository's normal shared-Skill binding mechanism.

## 4. Establish the repository document layer

A minimal consumer structure is:

```text
AGENTS.md
docs/git/
├── README.md
├── REPO_PROFILE.md
├── STACKED_PRS.md
├── WORKER_PROTOCOL.md
└── GIT_TOWN_ADMISSION.md
docs/harness/ or equivalent
.github/
├── ISSUE_TEMPLATE/
├── PULL_REQUEST_TEMPLATE.md
└── workflows/
scripts/git-town/              # consumer implementation, after evals
receipts/ or governed data root
```

Each directory should have a nearest README explaining owner, allowed contents, forbidden coupling, inputs, outputs, eval routing and evidence boundary.

## 5. Design the first issue stack

Create an epic before implementation. A reliable first stack is:

```text
main
└── governance foundation
    ├── exact Git Town admission
    ├── repository profile and Agent routing
    ├── worktree/lease Worker protocol
    ├── sync/publish Bash adapter
    ├── Harness evals and controls
    └── convergence and cold-start audit
```

Independent writable paths become siblings. Shared indexes, generated aggregate files and final traceability belong to one convergence issue.

Every issue must define evals and negative controls before a branch is created. Use [`EVALS.md`](EVALS.md).

## 6. Admit Git Town explicitly

The consumer/host must pin an exact version and decide how it is acquired. Record:

```text
source repository
immutable version/tag/commit
platform and architecture
binary/package checksum
provenance or package-manager lock
direct license bytes and digest
transitive dependency/SBOM result
required notices
service/host terms when applicable
organization legal approval state
```

A permissive top-level license does not eliminate all legal/commercial risk. Keep each evidence dimension separate.

## 7. Configure branch strategies

The consumer config should express policy, not convenience:

- protected/perennial branches use non-rewriting synchronization such as `ff-only` where supported by policy;
- feature branches use rebase only when rewriting is allowed;
- new branches are not implicitly shared;
- unattended auto-resolution is disabled;
- background sync is no-push by default;
- publication is explicitly guarded;
- merge/ship is not exposed to Workers.

Verify configuration with a mutation test: remove each load-bearing guard and require the gate to turn red.

## 8. Implement the consumer Bash adapter

Only after the issue evals exist, implement repository-owned scripts. Keep Bash limited to Git/worktree/process orchestration; business logic and machine-readable validation may use the repository's primary runtime, such as Bun + TypeScript.

Required adapter surfaces normally include:

```text
doctor
create isolated worktree
acquire/release lease
create/attach stacked branch
sync one owned stack
bounded background sync
propose/update PR
selftest and live integration canary
```

The adapter must use the shared outcome vocabulary and portable receipt schema. It must not become a generic arbitrary-command runner.

## 9. Build controls before trusting the green path

At minimum plant controls for:

- primary/shared checkout rejection;
- dirty worktree;
- wrong branch parent;
- duplicate branch/repository lease;
- overlapping sibling path leases;
- missing task-packet field;
- unresolved profile placeholder;
- wrong Git Town version;
- mutated license/checksum record;
- credential-bearing remote URL;
- attempted editor/credential prompt;
- deterministic rebase conflict;
- timeout;
- unexpected remote ref movement;
- push without both publication guards;
- protected branch rewrite attempt;
- failed cleanup/residue;
- automatic `continue`, `skip`, `undo`, `ship` or semantic edit.

Static checks and live canaries are different evidence lanes.

## 10. Adoption completion boundary

Adoption is complete only when the consumer can show:

1. shared canonical Skill resolved without shadowing;
2. complete repository profile;
3. root Agent routing and nearest README coverage;
4. issue/PR templates that require evals and path leases;
5. exact Git Town admission;
6. isolated worktree and lease controls;
7. dry-run and no-push synchronization canary;
8. planted conflict that fails closed;
9. guarded publication canary or explicit `NOT_EXERCISED`;
10. machine-readable receipts and cleanup evidence;
11. Human Admit for merge order;
12. immutable rollback subject.

Do not report adoption complete from documentation or package presence alone.