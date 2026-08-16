---
name: forgejo-private-repository-loop
description: |
  Run a Forgejo-only repository lineage for source material that must never enter GitHub. Use when private Git objects, domain documents, executables, fixtures, generated knowledge, or runtime evidence must remain local while only independently authored, domain-neutral requirements may cross into a publishable repository. This is a separate mode under dual-forge-repository-loop, not a shared-object-graph variant.
license: MIT
compatibility: Local Git and Forgejo are required for live mutation. Connector-only runtimes may inspect contracts but cannot claim local execution.
metadata:
  version: "0.1.0"
  procedure: "forgejo-private-repository-loop/v1"
---

# Forgejo Private Repository Loop

Use this mode only when the source lineage is prohibited from entering GitHub or another publication provider. It does **not** reuse the dual-forge single-object-graph law.

```text
PRIVATE LINEAGE
  local Git objects + local Forgejo issues/PRs + private runtime evidence

ONE-WAY CLEAN-ROOM BOUNDARY
  abstract capability contracts + state machines + generalized invariants
  + synthetic negative controls + sanitized receipt schemas

PUBLIC LINEAGE
  independently authored files + fresh root + no shared ancestry/alternates
```

## Routing law

If any source item must never enter GitHub history, refs, reviews, Actions, artifacts, caches, releases, packages, LFS, wiki, forks, mirrors, or provider backups, stop the normal dual-forge loop and use this mode. The public implementation may enter `dual-forge-repository-loop` only after the fresh-root and clean-room gates pass.

## State machine

```text
RUNTIME_BOUND
→ PRIVATE_SOURCE_AUDITED
→ FORGEJO_ONLY_BOUND
→ WRITER_FREEZE_ACTIVE
→ PRIVATE_ISSUES_BOUND
→ PRIVATE_WORKTREES_VERIFIED
→ PRIVATE_FORGEJO_PRS_MERGED
→ PRIVATE_MAIN_SEALED
→ CLEANROOM_REQUIREMENTS_EXPORTED
→ PUBLIC_IMPLEMENTATION_REWRITTEN
→ FRESH_ROOT_VERIFIED
→ PUBLICATION_HANDOFF
```

Every state transition binds an exact local subject and a local receipt. Connector evidence cannot satisfy a local or Forgejo transition.

## Hard laws

1. **Separate-lineage law** — private and public repositories do not share commits, trees, non-empty blobs, alternates, bundles, worktrees, or ancestry.
2. **Forgejo-only law** — the private checkout has exactly one admitted remote with exact fetch and push URLs; every other remote is refused.
3. **No-provider-egress law** — private commits, patches, bundles, raw prose, distinctive text, identifiers, paths, fixtures, logs, screenshots, generated corpora, and runtime receipts never cross the boundary.
4. **Clean-room law** — only generalized contracts and synthetic controls may cross; the public implementation is independently authored.
5. **External-deny-input law** — private literal and fingerprint sets remain outside Git. Checkers report rule indexes or digests, never denied source bytes.
6. **Fresh-root law** — public output starts with one new root commit, no remotes, no alternates, no gitlinks, and no common object lineage with the private source.
7. **Provider-disposition law** — local deletion or history rewrite is not provider erasure. Every provider surface receives an explicit terminal or limited disposition.
8. **One-writer law** — each private issue owns one branch writer, one isolated worktree, and explicit path/resource leases.
9. **Three-failure law** — three qualifying failures create a fresh-diagnosis issue and new worktree; no fourth blind patch.
10. **No-secret law** — credentials and provider sessions remain runtime-owned and never enter repository files or receipts.

## Procedure

### 1. Audit the source lineage

Use an external local pattern file. The producer scans refs, commit metadata, annotated tags, object paths, blobs, Git configuration, worktree files, local LFS objects, and alternate-object configuration.

```bash
python3 scripts/audit_git_history.py \
  --repo <private-worktree> \
  --patterns <local-pattern-file> \
  --output <local-receipt.json>
```

Exit `0` means no matches, `2` means denied material was observed, and `64` means the audit could not run.

### 2. Seal the checkout to Forgejo

```bash
bash scripts/configure_forgejo_only.sh \
  <private-worktree> \
  <exact-forgejo-repository-url>

python3 scripts/check_forgejo_only.py <private-worktree>
```

The configuration step backs up local Git config, removes every existing remote, installs an exact-destination pre-push guard, and records only local configuration.

### 3. Deliver private work locally

Compose `forgejo-delivery-loop` and `git-town-stacked-pr-worker`. Keep raw issues, PR receipts, screenshots, logs, fixtures, and generated evidence in the private lineage. Publish only sanitized status and content digests outside it.

### 4. Export a clean-room requirements packet

```bash
python3 scripts/build_private_fingerprints.py \
  --source <private-doc-or-directory> \
  --output <local-fingerprints.json>

python3 scripts/check_cleanroom_packet.py \
  <packet.json> \
  --private-patterns <local-pattern-file> \
  --private-fingerprints <local-fingerprints.json>
```

The packet schema permits capability contracts, state machines, generalized invariants, synthetic negative controls, sanitized receipt schemas, and approved public references. Source-derived fields and payloads fail closed.

### 5. Build and verify the public fresh root

```bash
bash scripts/create_fresh_root_snapshot.sh \
  <independently-authored-public-worktree> \
  <fresh-root-output> \
  --patterns <local-pattern-file> \
  --receipt <local-fresh-root-receipt.json>

bash scripts/assert_no_shared_lineage.sh \
  <fresh-root-output> \
  <private-worktree>
```

Only after both commands pass may the public lineage enter the normal dual-forge publication loop.

### 6. Track provider retention separately

```bash
python3 scripts/check_provider_retention.py <provider-disposition.json>
```

The checker rejects global `ERASED` claims and derives whether all surfaces are terminal or whether provider confirmation/accepted limitations remain.

## Evidence states

Use only:

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
HUMAN_ADMIT_REQUIRED
PROVIDER_DISPOSITION_REQUIRED
```

Hermetic tests prove these software contracts only. A live Forgejo repository, local worktree delivery, provider cleanup, or provider support disposition requires separate runtime evidence.

## Verification

```bash
bash tests/private-lineage/verify.sh
```
