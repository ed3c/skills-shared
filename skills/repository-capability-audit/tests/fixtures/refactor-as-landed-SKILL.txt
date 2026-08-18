---
name: repository-capability-audit
description: |
  Audit whether a repository capability claim is realized by executable behavior and persisted exact-subject evidence. Use for repository readiness, runtime reachability, integration truth, sandbox enforcement, evidence publication, or claim-to-proof review. Do not use for ordinary code review, prose editing, product prioritization, or merge authorization.
license: MIT
compatibility: Any Agent Skills-compatible coding agent with repository read access and authority to execute admitted probes. Stronger claims require matching runtime or substrate access.
metadata:
  version: "0.1.0"
  procedure: "runtime-evidence-repository-capability-audit"
  evidence_state: "runtime-ablated"
---

# Repository Capability Audit

## Role

Treat every repository capability statement as a claim under test. Recover the executable path, run the cheapest falsifier that reaches the required evidence level, preserve raw observations, and publish only the strongest conclusion the exact subject earned.

The core contains only procedures whose removal changes a deciding runtime-eval metric. Explanations, source mappings, and domain instances live under [`modules/`](modules/domain-instances.md).

## Trigger boundary

Use this skill when a requested conclusion depends on whether code, an integration, a runtime, a policy boundary, an evidence pipeline, or a publication path actually works.

Do not trigger for a text-only correction, ordinary diff review, feature ideation, or a request that makes no material capability claim.

## Terminal states

A capability row must end in exactly one state.

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
BLOCKED_INFRASTRUCTURE
SKIPPED_BY_POLICY
```

An aggregate may use `PASS_WITH_DECLARED_GAPS`. Absence, skip, configuration presence, process start, signature presence, or advisory prose is never a row-level `PASS`.

## State machine

```text
SCOPE
→ BIND SUBJECT
→ INVENTORY CLAIMS
→ ASSIGN EVIDENCE LEVELS
→ DESIGN POSITIVE AND FALSIFYING PROBES
→ EXECUTE
→ PRESERVE RAW EVIDENCE
→ VERIFY PERSISTED PACKET
→ FIRST-GREEN REVIEW
→ PUBLISH BOUNDED VERDICT
```

A transition that cannot prove its precondition stops in a named terminal state instead of advancing.

## Runtime-supported core laws

### RCA-001 — Bind the exact subject

Bind repository identity, immutable revision, content or tree digest, requested ref, and local mutation state before judging. Rebind after every mutation or remote publication.

```text
assert observed_subject == bound_subject
```

A receipt from another revision cannot prove the current subject.

### RCA-002 — Match claim strength to evidence level

For each material claim record the minimum evidence level, executable entrypoint, verifier, and falsifier. A lower level cannot promote a stronger claim.

```text
assert observed_evidence_level >= required_evidence_level
```

### RCA-003 — Preserve absence and skip as distinct states

Record missing entrypoints, unexecuted probes, policy skips, infrastructure blockers, and failures separately. A successful command containing an omitted required check is not a successful audit.

```text
assert required_checks_executed == required_checks_declared
```

### RCA-004 — Bind the actual runtime identity

Persist the observed runtime, service, process, device, image, policy, and relevant version or digest. Refuse aliases inferred from adapters, filenames, configuration, or intended deployment.

```text
assert claimed_runtime_identity == observed_runtime_identity
```

### RCA-005 — Pair denial probes with a positive control

A denied operation proves enforcement only when an admitted nearby operation succeeds in the same environment and the denied operation is actually attempted.

```text
assert positive_control.exit_code == 0
assert negative_control.attempted is true
assert negative_control.exit_code != 0
assert negative_control.failure_matches_expected_class is true
```

### RCA-006 — Preserve failure-path evidence

Normalize and persist trusted negative observations even when success-state artifacts are incomplete. Missing positive artifacts must still fail their own gates.

```text
assert raw_negative_observation in normalized_evidence
assert missing_positive_evidence does not become PASS
```

### RCA-007 — Verify the packet after the trust boundary

After copying, uploading, archiving, signing, or publishing, read the delivered object back and verify file presence, subject identity, and digests. Local pre-publication success is insufficient.

```text
assert delivered_manifest == expected_manifest
assert delivered_digest == receipt_digest
```

### RCA-008 — Resolve mutable external identities

When an external source is mutable, resolve it to an immutable identity and persist the resolution evidence before using it as input.

```text
assert external_subject.is_immutable is true
assert resolution_receipt.subject == external_subject
```

### RCA-009 — Minimize and test credential exposure

Remove ambient credentials from child environments. Grant a named credential only to the admitted command, and scan persisted output for prohibited material.

```text
assert child_environment contains no ambient_secret
assert published_packet contains no prohibited_secret_material
```

### RCA-010 — Produce a zero-access review packet

A fresh reviewer must be able to recover original intent, exact subject, claimed completion, scope boundary, command, runtime identity, raw evidence, verifier result, and non-claims without producer conversation history.

```text
assert required_review_fields <= packet_fields
```

### RCA-011 — Reopen proof obligations after first green

After the first passing result, re-evaluate coverage, skipped work, subject drift, persistence, failure paths, external boundaries, and stale evidence. A second check judges what the green result actually proved.

```text
assert first_green_review.completed is true
assert uncovered_material_claims == []
```

### RCA-012 — Publish explicit non-claims

List stronger adjacent conclusions that the run did not establish. Aggregate success cannot erase non-passing rows or substitute one substrate for another.

```text
assert reported_claims <= established_claims
assert unresolved_rows remain visible
```

### RCA-013 — Refuse unnecessary runtime escalation

Before executing expensive or side-effecting probes, confirm that the request contains a material capability question and that the selected probe is the cheapest admitted falsifier.

```text
assert audit_triggered == material_capability_question
```

## Deterministic procedure

1. Parse repository guidance and user intent into an exact-subject record and a claim inventory.
2. Assign each claim a required evidence level and terminal-state owner.
3. Select the cheapest probe that can falsify the claim at that level.
4. Execute positive and negative controls under the same bound environment.
5. Persist command, input digest, actual exit status, runtime identity, raw output, verifier result, and evidence paths.
6. Verify the delivered packet after every trust boundary.
7. Run the first-green review and downgrade any claim whose proof obligation remains open.
8. Emit the bounded verdict, explicit non-claims, and zero-access packet.

## Required output

```text
subject.json
claim-matrix.json
capability-result.json
runtime.json
raw-logs/
evidence/
verdict.json
SHA256SUMS
summary.md
```

Each passing row must identify its exact command, actual result, runtime identity, verifier rule, persisted evidence, digest, and non-claims.

## Core-evidence self-check

Run the committed ablation suite from the repository root.

```bash
python3 skills/repository-capability-audit/scripts/run_ablation.py \
  --output /tmp/repository-capability-audit
python3 skills/repository-capability-audit/scripts/check_core.py \
  --report /tmp/repository-capability-audit/effectiveness.json
```

The checker fails when a core law has no deciding runtime delta, a domain instance leaks into this file, an expected report drifts, or a suite has no real CI arrival.

## Before reading a null off a matrix result

Ask which metrics could have moved at all.

```bash
python3 skills/repository-capability-audit/scripts/analyze_arm_separation.py \
  --result skills/repository-capability-audit/evals/matrix-slice1-result.json
```

A metric with zero within-arm variance is saturated: it carries no information about the treatment, so a null on it describes the case set and not the Skill. Declaring one as primary exits 2. This exists because slice 1 stopped a six-slice matrix on exactly that reading, while `false_pass_rate` — recorded in every cell, and not saturated — sat unanalysed in the same file. Counts are compared as rates, since the opportunity count differs between arms.

## Stop conditions

Stop and surface evidence when any of these holds.

```text
exact subject cannot be bound
required runtime authority is absent
probe would cross an unadmitted side-effect boundary
positive control cannot run
raw evidence cannot be persisted
publication cannot be read back
three qualifying repairs repeat the same root cause
```

Do not repair an evaluator merely to make a claim pass. Do not promote a deterministic fixture into production evidence. Do not let an advisory model verdict override a failed executable gate.
