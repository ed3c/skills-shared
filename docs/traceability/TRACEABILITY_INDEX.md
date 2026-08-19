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
| Cross-Skill adoption audit | `#322` | delivery PR of `agent/goal-33-issues-batch` (GitHub metadata) | planned process follow-up | `agent/goal-33-issues-batch` / `main` | machine ledger at `skills/skill-refactor-proof-loop/references/skill-adoption-ledger.json`; rendered report at [`SKILL_REFACTOR_ADOPTION_AUDIT.md`](SKILL_REFACTOR_ADOPTION_AUDIT.md), byte-compared by `render_adoption_audit.py --check` in the Skill suite; standard admitted for adoption governance on 2026-08-17 and re-admitted the same day after the subject moved; every measured gap remains owned by its Skill's migration leaf, with #231/#232/#234/#256 keeping their own evidence lanes |

True-child edges are justified by consumed unmerged artifacts:

```text
#308 task/capability contracts and frozen treatments
→ #315 matched L3 proof
→ #323 portable contract and golden registry
→ #324 Agent and State Machine documentation
→ #325 one convergence/index owner
```

Issue #322 is a process dependency after admission, not automatically a Git child. Issues #231, #232, #234 and #256 are independent scheduler, Shadow, delivery and adapter evidence lanes; they may raise #312 from L3 to L4/L5 only with matched exact-subject receipts. They are not fake Stack ancestry.

Adapter lane status (#256): the consolidated recapture on 2026-08-18 ran with all nine provider lanes on one host and the admission binding points at the consolidated receipts. The #231/#234 scheduler/Git-Town/dual-forge receipt-binding acceptance item remains separately owned; its evidence cannot be borrowed merely because provider receipts exist.

Closure generalization (#332): repository-closure, Issue dual-DAG and Molecular Stack index are typed, checked subjects. The matching closure laws are bound into the agentic-tech-lead portable core while historical treatments remain byte-frozen in the refactor proof loop. Static/hermetic proof does not upgrade L4 live model/runtime or L5 delivery/Human Admit.

Offload method binding (#359): the Local/cloud offload method was added as a new frozen treatment rather than repointing an old golden hash. Its executable semantic authority remains the dedicated offload contract verifier; every runtime wire/effect lane stays separate from the method bytes.

## Codex SDK Tech Lead control-plane convergence — #375–#380

Canonical human trace: [`CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md`](CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md). The provider-neutral method remains `skills/agentic-tech-lead-orchestration/SKILL.md`; this section records implementation and delivery subjects only.

### Static implementation siblings

Observed implementation epoch: `main@ccef97dedd7ea8b1873e3afa130ca82b8eabb413`.

| Atom | Issue | PR | Relation | Exact sibling head | Provides | Exact-head hosted gates | Terminal ceiling |
|---|---|---|---|---|---|---|---|
| Codex SDK controller/session adapter | `#375` | `#451` | `SIBLING` | `339ae874b070fb3a8a5fa89b0241d90434257e99` | session/result schemas, bounded SDK runner, path/thread controls, selftest | Skill Suites / Shared Skills Infra / Skill Eval Contract `SUCCESS`; Shadow `STATIC_ADMITTED` | mechanism static/deterministic; live SDK `NOT_EXERCISED` |
| GitHub Issue DAG projection | `#376` | `#452` | `SIBLING` | `b5295df681d6471b19775db38860b2d151339879` | completion-edge projection/readback, ready wave, non-destructive remote policy, selftest | same three hosted gates `SUCCESS`; Shadow `STATIC_ADMITTED` | mechanism static/deterministic; live mutation/readback `NOT_EXERCISED` |
| Herdr runtime observer | `#377` | `#453` | `SIBLING` | `5b6e58d1e7e9e127123dbb4a9189b98e5ff973cf` | optional observer, CWD/session identity, fallback, receipt schema, selftest | same three hosted gates `SUCCESS`; Shadow `STATIC_ADMITTED` | mechanism static/deterministic; live Herdr `NOT_EXERCISED` |
| Problem-closure ledger | `#378` | `#454` | `SIBLING` | `32c5425de1cf4f083bd998e81873a86af8771e1e` | exact source→task/DAG→session/evidence closure schema/checker/renderer/selftest | same three hosted gates `SUCCESS`; Shadow `STATIC_ADMITTED` | deterministic closure consistency; real source/provider closure `EVIDENCE_DEPENDENT` |
| Control-plane design/trace foundation | `#379` refs | `#380` | `SIBLING / DOCUMENTATION` | `7a9d68fcd58b1ed78ed6d05595a8df7eae53f5a5` | nearest traceability Agent route + original design trace | documentation candidate; exact commits carry required provenance trailers | navigation only |

The first rejected candidates are preserved as failed lineage, not force-rewritten away:

```text
#444 → #451   commit-role gate rejected unclassified Contents-API history
#445 → #452   same
#446 → #453   same
#447 → #454   same
```

### Convergence subject

`#379` is the single shared writer. It does **not** serialize the four implementation siblings. Instead, Git records a real multi-parent convergence:

```text
main ccef97dedd7ea8b1873e3afa130ca82b8eabb413
├─ #451 339ae874b070fb3a8a5fa89b0241d90434257e99
├─ #452 b5295df681d6471b19775db38860b2d151339879
├─ #453 5b6e58d1e7e9e127123dbb4a9189b98e5ff973cf
└─ #454 32c5425de1cf4f083bd998e81873a86af8771e1e
        ↓ exact union tree 37cb2c56e7dfc939cacaa0f65cf8f9b0f8318b22
c0f6979f80038394350aea724c598c8dba5ac338  CONVERGENCE
        ↓ PR #380 documentation bytes admitted as separate parent
7a9d68fcd58b1ed78ed6d05595a8df7eae53f5a5
        ↓
af427a13a7096df91d74a48c0a4ca6ce3f3e2ac9  documentation-integrated convergence base
```

Branch: `ctl/379-codex-control-plane-convergence`.

The exact branch head is intentionally read from current GitHub PR/branch metadata after every convergence edit rather than embedded here; self-embedding the mutable final head would make this file stale in the commit that records it. The immutable ancestors above are safe to record.

#379 owns only shared convergence surfaces: ATL `tests/run-all.sh`, nearest Agent/README/module/reference/script/test routes, Shadow relationship, Git Town Molecular index and traceability. Required selftests are wired unconditionally; absence is failure, never an `if file exists` skip.

The four implementation issues remain open for their stronger evidence lanes. Merge/release and semantic conflict remain Human/repository authority.

Open PR heads elsewhere in this index are read from GitHub metadata rather than self-embedded in the same branch. A merged node may record an immutable merge SHA only after its owning checks/evidence are observed and terminal state is truly `MERGED`.

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

Parent programme `#115`. The architecture, evidence law, and full merged ledger live in [`../architecture/CONTROLLED_TECHNICAL_LANGUAGE_HARNESS.md`](../architecture/CONTROLLED_TECHNICAL_LANGUAGE_HARNESS.md); this table records the delivery trace only.

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
| CTL 07A immutable consumer binding | `ed3c/bettor-arena#84` | `ed3c/bettor-arena#85` | `a3bee10b1e8ffc3c85bad518a18d044915a415bb` | read in that repository |
| CTL 07B sealed projection materializer | `ed3c/bettor-arena#88` | none | `0b0d1a5d571dfdda89d655e1a4fd619ad8d27d55` | read in that repository |
| CTL 07B paired carrier canaries | `ed3c/bettor-arena#108` | none | n/a | none — open |
| CTL 08 convergence index | `#133` | none | n/a | none — recording only, not admitted |

Unlike the IBC rows above, every merged CTL leaf had a green owning check at the PR head. The external bettor rows carry no owning check in this repository on purpose; their current checks/state must be read from that repository.

## Spatial-loop systems engineering leaf

| Source | Issue | PR publication subject | Stack class | Publication state | Owning controls |
|---|---|---|---|---|---|
| User-supplied system-engineering proposal | `#128` | `#136` | independent terminal leaf | Open Draft; read exact live state from GitHub | local `tests/run-all.sh` PASS; GitHub jobs remain policy-gated while Draft |

The leaf binds the generalized method to its deterministic contract/checker and negative controls. Live privileged/kernel/hardware/chaos/security execution remains `NOT_EXERCISED`; destructive testing, security acceptance, production promotion, merge and rollback remain Human/trusted-operator boundaries.

## Method lineage

- `knowledge-continuity` supplies the rule that every hop leaves an in-place summary and evidence is not hidden behind unexplained redirects.
- `github-delivery-loop` supplies issue/PR/receipt and publication-state separation.
- `forgejo-delivery-loop` supplies local authoring, deterministic routing/outbox/recovery, and receipt separation.
- `git-town-stacked-pr-worker` supplies sibling/true-child/terminal/convergence branch semantics, machine-readable molecular traceability, and Human boundaries.
- `skill-refactor-proof-loop` supplies treatment freeze, old-strength preservation, proof layers, golden registry, denominator completeness and no evidence promotion.
- `agentic-tech-lead-orchestration` supplies task/capability DAG ownership, linked-worktree execution contracts and the Codex control-plane convergence described above.
- `procedural-shadow-runtime` supplies independent same-subject applicability/contradiction/evidence-ceiling review.
- `spatial-loop-systems-engineering` supplies exact-subject state-space, capability, invariant, teardown, performance, and implementation-gate contracts for substrate-bound work.

## Evidence boundary

PR presence and exact GitHub head metadata prove publication identity only. Documentation completion does not imply route-checker execution, fresh Claude/Codex cold-start, GitHub/Forgejo equivalence, live Codex/Herdr/GitHub dependency effects, real source/provider closure, model behavioral uplift, capability unlock, release promotion, merge, or production readiness.
