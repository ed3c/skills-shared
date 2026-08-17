# Traceability index — document routing and proof-carrying Skill delivery

## Trace model

```text
source / incident
→ repository decision
→ parent issue
→ molecular issue
→ sibling or true-child PR
→ eval / negative control
→ immutable or GitHub-read subject
→ receipt / current evidence state
→ Human Admit
```

## Proof-carrying Skill refactor Stack

Detailed human trace: [`SKILL_REFACTOR_PROOF_STACK.md`](SKILL_REFACTOR_PROOF_STACK.md). Machine authority:

```text
skills/skill-refactor-proof-loop/references/refactor-proof-stack.json
skills/skill-refactor-proof-loop/references/refactor-proof-stack.schema.json
skills/skill-refactor-proof-loop/scripts/check_refactor_proof_stack.py
```

| Node | Issue | PR publication subject | Stack class | Branch / base | Current state source |
|---|---|---|---|---|---|
| Tech Lead task/capability causal repair | `#307/#309` | `#308` | root | `fix/307-tech-lead-runtime-reachability` / `main` | current GitHub PR metadata and owning workflows |
| Production-shaped hermetic golden proof | `#312` | `#315` | true child | `agent/312-tech-lead-real-task-ab` / PR #308 branch | current GitHub PR metadata and Skill Suites |
| Generalized proof contract + golden registry | `#319` | `#323` | true child | `agent/319-skill-refactor-proof-contract` / PR #315 branch | current GitHub PR metadata and Skill Suites/Shared Skills Infra |
| Agent routes + directory State Machines/DAG/data flow | `#320` | `#324` | true child | `agent/320-refactor-proof-agent-docs` / PR #323 branch | current GitHub PR metadata and route/check workflows |
| Molecular Stack + traceability convergence | `#321` | `#325` | convergence | `agent/321-refactor-proof-stack-index` / PR #324 branch | current GitHub PR metadata and exact-head workflows |
| Cross-Skill adoption audit | `#322` | delivery PR of `agent/goal-33-issues-batch` (GitHub metadata) | planned process follow-up | `agent/goal-33-issues-batch` / `main` | machine ledger at `skills/skill-refactor-proof-loop/references/skill-adoption-ledger.json`; rendered report at [`SKILL_REFACTOR_ADOPTION_AUDIT.md`](SKILL_REFACTOR_ADOPTION_AUDIT.md), byte-compared by `render_adoption_audit.py --check` in the Skill suite; standard admitted for adoption governance on 2026-08-17 (`skills/skill-refactor-proof-loop/evals/proof-standard-admission.json`); per-gap migration issues and migration ordering still open |

True-child edges are justified by consumed unmerged artifacts:

```text
#308 task/capability contracts and frozen treatments
→ #315 matched L3 proof
→ #323 portable contract and golden registry
→ #324 Agent and State Machine documentation
→ #325 one convergence/index owner
```

Issue #322 is a process dependency after admission, not automatically a Git child. Issues #231, #232, #234 and #256 are independent scheduler, Shadow, delivery and adapter evidence lanes; they may raise #312 from L3 to L4/L5 only with matched exact-subject receipts. They are not fake Stack ancestry.

Adapter lane status (#256): 8/9 adapter lanes (grepai, scip, tree-sitter, serena, sqlite, lancedb, worktree, forgejo) carry live receipts on main at commit `f50b2b9822db9e534169b5e63b523d940b32bb3c`; git-town is honestly `ABSENT` pending a Human admission decision for a darwin-compatible Git Town artifact (the committed admission is pinned by SHA-256 to `linux_intel_64`). The completion-report matrix is [`skills/repo-agent-native/evals/ADAPTER_RECEIPT_MATRIX.md`](../../skills/repo-agent-native/evals/ADAPTER_RECEIPT_MATRIX.md). The #231/#234 scheduler/Git-Town/dual-forge receipt-binding acceptance item remains `NOT_EXERCISED` pending those issues' remaining slices. On 2026-08-17 the owner admitted the darwin git-town artifact (`skills/repo-agent-native/evals/git-town-darwin-admission.json`, v24.0.0 darwin-arm64 pinned to the runtime-env catalog digest) and the ninth lane was implemented and exercised live; its receipt lives in the single-subject directory `skills/repo-agent-native/evals/receipts-git-town-darwin/` because `check_adapter_receipts.py` correctly refuses receipt sets spanning two capture subjects — the consolidated nine-lane recapture at one commit on a fully-live host remains open.

Closure generalization (#332): the repository-closure contract, Issue dual-DAG and Molecular Stack index are now typed, checked subjects — schemas, examples and deterministic gates live at `skills/agentic-tech-lead-orchestration/references/` (`repository-closure-contract.schema.json`, `issue-dual-dag.schema.json`, gate `scripts/assert_repository_closure_contract.py`) and `skills/git-town-stacked-pr-worker/references/` (`molecular-stack-index.schema.json`, gate `scripts/assert_molecular_stack_index.py`), with the atom law bound into the git-town portable core (CORE-LAW-006). The matching closure laws are now bound into the agentic-tech-lead portable core as `CORE-LAW-009` (start-readiness and completion-readiness are two edge classes) and `CORE-LAW-010` (closure lanes do not substitute); `references/REPOSITORY_CLOSURE_RECONCILIATION.md` remains the know-why for the schemas and the gate, not the home of the laws. That binding went through the refactor proof loop rather than around it: the golden-proof-pinned body was frozen byte-for-byte as `tests/fixtures/causal-dag-repaired-SKILL.txt`, so `B2_CAUSAL_DAG_REPAIRED` keeps its registered blob `3fd01571` on an immutable path, and the live `SKILL.md` is the new treatment `B3_CLOSURE_LAWS_BOUND` (blob `f6d66795`) registered in `skills/skill-refactor-proof-loop/references/golden-proof-registry.json`. All five arms were re-run on the same base by `skills/agentic-tech-lead-orchestration/tests/run-all.sh`: A 9, B0 6, B1 10, B2 11, B3 12 of 12 deterministic criteria, with B3 dominating B2 and no criterion regressed. Evidence ceiling unchanged: `L4_MATCHED_LIVE_MODEL_RUNTIME` stays `NOT_EXERCISED` and `L5_DELIVERY_AND_HUMAN_ADMIT` stays `HUMAN_ADMIT_REQUIRED`. Publication subject: delivery PR of `agent/goal-33-issues-batch` (GitHub metadata).

Open PR heads are read from GitHub metadata rather than self-embedded in the same branch. A merged node may record an immutable merge SHA only after its owning checks/evidence are observed and terminal state is truly `MERGED`.

## Four-repository documentation stack

| Plane | Issue | PR publication subject | Stack class | State | Merged commit |
|---|---|---|---|---|---|
| Parent integration contract | `ed3c/bettor-arena#35` | n/a | parent | open | n/a |
| Instruction / Method | `ed3c/skills-shared#84` | `ed3c/skills-shared#85` | independent sibling | Merged | `e3b327ad49c088f1962c33167ecd5ac9d28125fb` |
| Runtime Contract | `ed3c/runtime-env#29` | `ed3c/runtime-env#30` | independent sibling | Merged | `4a333ccf106ef60bc6942b922b7f5efffb3876f5` |
| Domain Product / Consumer | `ed3c/agent-shield-monorepo#77` | `ed3c/agent-shield-monorepo#78` | independent terminal sibling | Merged | `1af04c1ef5cb68eab198987feba008c93d3ec22f` |
| Integration / Acceptance | `ed3c/bettor-arena#36` | `ed3c/bettor-arena#37` | independent sibling | Merged | `1f94d3d77992a1396959a15b2ada7836c07bf300` |
| Exact merged index and cold-start audit | `ed3c/bettor-arena#38` | n/a | convergence leaf | Closed | n/a |

All four siblings have merged and the convergence owner `bettor-arena#38` is closed, so this stack is no longer pending work. The parent contract issue `bettor-arena#35` remains open and is the only live item on that plane.

The exact candidate head of an *open* PR is read from GitHub PR metadata rather than embedded in the same branch: self-embedding a commit SHA would make the document stale in the commit that updates it. Merged commits above are immutable and therefore safe to record.

The four implementation branches were siblings because each edited only its repository's documentation and consumed merged inputs. A serial stack would have added false dependencies.

## Intent-Bound Constraint stack

| Leaf | Issue | PR | Merged commit | Merged tree | Owning workflow at the admitted head |
|---|---|---|---|---|---|
| IBC 01 contract + closure evaluator | `#98` | `#104` | `fe660a990e9c66d364afd6519579048276ac7980` | `ea5e0a23ffc57b35039e8ffaf085f65d2bf3aa08` | `Skill Eval Contract` SUCCESS |
| IBC 02 Git Town Stack binding | `#99` | `#105` | `0f18b483d6f31cbfd59c887ef146833fa2186f77` | `1891f98129daacf3fa75401a69254eea00a49419` | **none — zero runs at that head** |
| IBC 03 knowledge-continuity adapter | `#100` | `#106` | `6d0c54f63cfa8aa7224d395095efe0cc5cf9b7e2` | `261b6aed0c7a92ab17a03b1a7595cc17736e290e` | **none — zero runs at that head** |
| IBC 04 forgejo-delivery-loop adapter | `#101` | `#111` | `9d937458178f0315220710f4cc356a4d6549e977` | `f6bed242309c9f9904d12f0a14b4eb0a2b4b37e0` | `Forgejo Delivery Loop Contract` SUCCESS |
| IBC 05 pinned live Git Town canary | `#102` | `#107` | `c8f4813b402095ed1d72060dcb81f1ac0edfc838` | `60b6425b568293b644057b6028b2955686b93586` | `Git Town Stacked PR Worker / live-canary` SUCCESS |

IBC 02 and IBC 03 merged with **no workflow run at their head commits at all**. That is an absence of evidence, not a pass, and it is recorded here rather than smoothed over. Its consequences and the repairs that followed are in [`../AGENT_INTEGRATION_STATE.md`](../AGENT_INTEGRATION_STATE.md).

## Controlled Technical Language stack

Parent programme `#115`. The architecture, evidence law, and full merged ledger live in
[`../architecture/CONTROLLED_TECHNICAL_LANGUAGE_HARNESS.md`](../architecture/CONTROLLED_TECHNICAL_LANGUAGE_HARNESS.md);
this table records the delivery trace only.

| Leaf | Issue | PR | Merged commit | Owning check at the PR head |
|---|---|---|---|---|
| CTL 01 contract foundation | `#116` | `#117` | `a711316ec6ab50a952e2ec3df64c7feea2d181b1` | `contract` SUCCESS |
| CTL 01 hotfix false-PASS paths | `#124` | `#125` | `65c72f7ab67af49d6237245eb64298cf62c11e14` | `contract` SUCCESS |
| CTL 02 Harness core and STE profile | `#118` | `#126` | `061ff5e479e0f4595def11ec08bc4ddff8959708` | `controlled-technical-language-harness` SUCCESS |
| CTL 03 deterministic evaluators | `#119` | `#127` | `edfa2922856a457167b56d32a73d679577718492` | `controlled-technical-language-harness` SUCCESS |
| CTL 03 hardening exact subjects | `#129` | `#137` | `6764c67e7df9206dbc36f731f38f4c7dd252d51d` | `controlled-technical-language-harness` SUCCESS |
| CTL 03 hardening calibration controls | `#129` | `#139` | `8e13b3ab9a2e34b75384c8fbc87ea5f8a3249f22` | `controlled-technical-language-harness` SUCCESS |
| CTL 04 intent-promotion writeback gate | `#120` | `#130` | `8c040362eaad3fdf8d81a50cb594d15a7de8feb6` | `contract` SUCCESS |
| CTL 04B authority substitutions | `#134` | `#138` | `c737e43d2cb6713a3fbbfd1f8d54c3b81b1870a7` | `contract` SUCCESS |
| CTL 04C external authority readback | `#141` | `#143` | `a7b278aba8bdf744e901f605ea07b09e3b468e60` | `authority` SUCCESS |
| CTL 05 document format and privacy routing | `#121` | `#131` | `e4f22e887bd1dfaea9cf673d75bb0a19a30d0ca6` | `controlled-technical-language-harness` SUCCESS |
| CTL 06 integrated A/B canary | `#132` | `#140` | `47cbb259c0157535d6f40b703b487e225a1a9de1` | `controlled-technical-language-harness` SUCCESS |
| CTL 06B A/B against external authority bytes | `#144` | `#152` | `b3d47948feb6e2d44d84261354117aecfaa4f5dc` | `controlled-technical-language-harness` SUCCESS |
| CTL 07 consumer binding and canaries | `ed3c/bettor-arena#83` | none | n/a | none — open in another repository |
| CTL 08 convergence index | `#133` | none | n/a | none — blocked on CTL 07 |

Unlike the IBC rows above, every merged CTL leaf had a green owning check. That check ran at the **PR head**, which is a different commit from the merge commit recorded beside it; a green head is evidence about the reviewed bytes, not a re-run of `main`.

CTL 08 is the convergence owner and stays unopened: its contract forbids creating the branch before every prerequisite merges, and CTL 07 is open in `bettor-arena`. A convergence PR cannot repair an implementation leaf, so the unmet condition sits with its owner rather than being absorbed here.

## Spatial-loop systems engineering leaf

| Source | Issue | PR publication subject | Stack class | Publication state | Owning controls |
|---|---|---|---|---|---|
| User-supplied system-engineering proposal | `#128` | `#136` | independent terminal leaf | Open Draft; read exact live state from GitHub | local `tests/run-all.sh` PASS; GitHub jobs remain policy-gated while Draft |

The leaf binds the generalized method to `spatial-loop-system-contract/v1`, its deterministic checker, positive/hollow/mutation controls, the trigger-loaded Linux isolation module, and the Skill Suites arrival. The exact open-PR head and workflow state are read from GitHub rather than self-embedded here.

Live root, KVM, cgroup, seccomp, network-namespace, hardware-performance, chaos, exploit, and sandbox-escape execution remain `NOT_EXERCISED`. Destructive privileged testing, security acceptance, production promotion, permission widening, merge, and rollback remain Human/trusted-operator boundaries.

## Method lineage

- `knowledge-continuity` supplies the rule that every hop leaves an in-place summary and evidence is not hidden behind unexplained redirects.
- `github-delivery-loop` supplies issue/PR/receipt and publication-state separation.
- `forgejo-delivery-loop` supplies local authoring, deterministic routing/outbox/recovery, and receipt separation.
- `git-town-stacked-pr-worker` supplies sibling/true-child/terminal/convergence branch semantics, machine-readable molecular traceability, and Human boundaries.
- `skill-refactor-proof-loop` supplies treatment freeze, old-strength preservation, proof layers, golden registry, denominator completeness and no evidence promotion.
- `agentic-tech-lead-orchestration` supplies the first production-shaped matched hermetic golden proof.
- `spatial-loop-systems-engineering` supplies exact-subject state-space, capability, invariant, teardown, performance, and implementation-gate contracts for substrate-bound work.

## Evidence boundary

PR presence and exact GitHub head metadata prove publication identity only. Documentation completion does not imply route-checker execution, fresh Claude/Codex cold-start, GitHub/Forgejo equivalence, live provider canaries, model behavioral uplift, capability unlock, release promotion, merge, or production readiness.
