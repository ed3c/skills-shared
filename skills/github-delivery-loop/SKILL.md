---
name: github-delivery-loop
description: |
  Use a receipt-driven delivery method that binds immutable subjects, executable verification, publication admission,
  remote re-observation, and integration authority. Apply when work must move from a local implementation loop into a
  forge or review surface without confusing local success with remote delivery. The portable procedure is forge-neutral;
  GitHub, GitHub Actions, PR labels, host permissions, and provider-specific controls live in modules/.
---

# Delivery Loop

This Skill owns the delivery boundary between an implementation loop and an external integration surface. It does not own the task-specific prompt, business-domain logic, test oracle, provider credentials, or release authority.

## Portable procedural core

The core method is deliberately independent of GitHub, a particular CI product, or a specific Agent host.

```text
DL-01 INTENT_BOUND
→ DL-02 SUBJECT_BOUND
→ DL-03 EVIDENCE_CONTRACT_BOUND
→ DL-04 LOCAL_VERIFICATION
→ DL-05 PUBLICATION_ADMISSION
→ DL-06 REMOTE_PUBLICATION
→ DL-07 REMOTE_REOBSERVATION
→ DL-08 INTEGRATION_ADMISSION
→ DL-09 TERMINAL_RECEIPT
```

### Procedure atoms

**DL-01 — Bind delivery intent before mutation.** Name the requested outcome, owner, effect class, rollback subject, and evidence required for completion. A branch, issue, or transport action is an implementation detail, not the intent itself.

**DL-02 — Bind the immutable subject.** Record repository/resource identity plus an immutable revision or content digest before judging, publishing, or integrating. Rebind after any mutation that changes the subject.

**DL-03 — Bind the evidence contract.** Define the positive oracle, at least one falsifying control for every load-bearing invariant, expected terminal states, and evidence producer before claiming readiness.

**DL-04 — Execute local verification.** Run fixed commands or typed probes against the exact subject. Preserve command identity, exit status, bounded output/artifact digests, runtime identity, and verifier result. Prose, a checklist, or model self-report cannot substitute for executed evidence.

**DL-05 — Admit publication separately from local progress.** Frequent local checkpoints are allowed; expensive or externally visible publication is a separate transition. Publication requires a current verification receipt, a named publication intent, and an authority/policy decision for the exact subject.

**DL-06 — Publish through one bounded transition.** Use a fixed, reviewable publication adapter. Do not expose an arbitrary shell, ambient credentials, unrestricted network authority, or host-global mutation as the portable publication API.

**DL-07 — Re-observe after the trust boundary.** Read the remote/ref/artifact/check state back after publication and bind its identity. A successful local command or transport exit does not prove the external surface accepted, executed, or persisted the intended subject.

**DL-08 — Admit integration against the same reviewed subject.** Merge, release, promotion, or equivalent integration must be pinned to the exact reviewed head/content and its required remote evidence. A moved head invalidates prior admission.

**DL-09 — Emit one terminal receipt.** Preserve the final subject, evidence sources, authority decision, external observation, integration result, and remaining gaps. Never collapse unavailable, unimplemented, unexecuted, failed, skipped, and passed states.

## Hard laws and executable assertions

Each hard law has a deterministic assertion surface. The commands are repository-local examples of the invariant; domain adapters may add stricter checks but may not weaken them.

| ID | Hard law | Executable assertion |
|---|---|---|
| DL-L01 | An immutable subject is bound before judgment/publication. | `python3 scripts/check_procedural_core.py --root .` |
| DL-L02 | Local evidence and remote/provider evidence are distinct. | `python3 scripts/check_procedural_core.py --root .` |
| DL-L03 | Every load-bearing claim has executable verification and a falsifying control. | `bash tests/run-all.sh` |
| DL-L04 | Local checkpoint cadence is independent from remote publication cadence. | `bash tests/ci-publish-gate/verify.sh` |
| DL-L05 | Publication uses an admitted fixed transition, never arbitrary shell or ambient authority. | `bash tests/evidence-producers/verify.sh` |
| DL-L06 | Remote state is re-observed before delivery is claimed. | `bash tests/check-receipt/verify.sh` |
| DL-L07 | Integration is pinned to the same reviewed subject. | `bash tests/merge-gate/verify.sh` |
| DL-L08 | Evidence states remain distinct: `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`. | `python3 scripts/check_procedural_core.py --root .` |
| DL-L09 | Portable receipts contain no credential values, host-global mutation authority, or permission widening. | `bash tests/evidence-producers/verify.sh` |
| DL-L10 | Merge/release/promotion is external authority unless a bounded policy explicitly delegates it. | `bash tests/merge-gate/verify.sh` |

Run the complete zero-network Skill suite with:

```bash
bash skills/github-delivery-loop/tests/run-all.sh
```

## Evidence-state discipline

Use these terminal evidence states without substitution:

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
```

A lower evidence state may block only the transition that needs it. Static or documentation work may continue when safe, but it cannot be promoted to runtime or external-delivery `PASS`.

## Domain decoupling

The portable core above must not absorb forge-specific transport, CI billing/provider behavior, host hook syntax, repository labels, or consumer-specific paths. Those belong to modules and may be loaded only when their domain is selected.

- GitHub repository/PR/check/Actions mechanics: [modules/github-domain.md](modules/github-domain.md)
- Delivery registry, receipts, metrics, and authority model: [modules/delivery-mechanism.md](modules/delivery-mechanism.md)
- CI publication and provider-cost controls: [modules/ci-publication.md](modules/ci-publication.md) and [modules/github-actions-cost-control.md](modules/github-actions-cost-control.md)
- Host permission planes: [modules/host-permissions.md](modules/host-permissions.md)
- Commit identity/trailers: [modules/commit-role.md](modules/commit-role.md)
- Integrated state machines: [modules/state-machines.md](modules/state-machines.md)
- Traceability index: [modules/traceability-index.md](modules/traceability-index.md)

A domain module may instantiate `DL-01..DL-09`; it may not redefine those atoms or move provider/consumer facts back into the portable core.

## GitHub domain route

When GitHub is the selected forge, load [modules/github-domain.md](modules/github-domain.md) and the specialist modules it references. Existing executable surfaces remain authoritative for exact field shapes and exits:

```text
scripts/github_delivery.py
scripts/delivery_sync.py
scripts/local_verification.py
scripts/github_actions_snapshot.py
scripts/ci_publish_gate.py
scripts/ci_publish.py
scripts/ci_publish_guard.py
scripts/ci_workflow_policy.py
scripts/merge_gate.py
```

The GitHub module maps these mechanisms onto the portable atoms; GitHub-specific implementation details are not universal procedure law.

## Change protocol

Any change to the portable core must:

1. preserve `DL-01..DL-09` or version the procedure explicitly;
2. preserve `DL-L01..DL-L10` or version the hard-law contract;
3. add/update a positive control and a planted negative when a load-bearing invariant changes;
4. keep provider/forge/host/consumer facts in `modules/`;
5. run `scripts/check_procedural_core.py` and `tests/run-all.sh`;
6. publish only the strongest evidence state actually observed.

Do not weaken an assertion only to make a fixture pass. A domain-specific success is evidence for that domain and exact subject only; it is not proof that the portable method works on every forge, host, provider, or repository.
