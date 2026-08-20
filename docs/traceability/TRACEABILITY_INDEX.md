# Traceability index — current terminal lineage and historical proof routes

Current public-state projection: [`CURRENT_PUBLIC_REPOSITORY_STATE.md`](CURRENT_PUBLIC_REPOSITORY_STATE.md).

This index separates **current terminal/admitted subjects** from historical candidate snapshots. GitHub metadata, exact Git subjects, executable contracts and runtime receipts remain authority.

## Trace model

```text
source / incident
→ applicability / repository decision
→ parent issue
→ molecular issue
→ SIBLING | TRUE_CHILD | CONVERGENCE | PROCESS_DEPENDENCY | EXTERNAL_EVIDENCE
→ eval + negative controls
→ exact Git/runtime subject
→ receipt / evidence state
→ Human Admit when required
→ merge / post-merge readback
→ closure only for earned evidence scope
```

A convergence ancestry edge proves consumed bytes. It does not admit an unmerged parent. An old green head does not follow a moving base/head/interface.

## Current public terminal index

| Line | Issues / PRs | Relation / terminal state | Exact durable subject / evidence | Remaining ceiling |
|---|---|---|---|---|
| Wave-2 Tech Lead control plane | #375–#379 / PR #455 | sibling fan-out → `CONVERGENCE / MERGED` | merge `ca31e0b1e640f0dba2c3d94da9d9786fbed32f2c`, tree `8a75271851f2e9dd47dd3a019c93e4a0f9272d24` | live successors separate |
| Wave-3 infrastructure | #464–#468 / PR #480 + #484 | true-child-at-fork siblings → convergence → merged/post-merge | merge `dd86861972f41f6d36c3de7ac156358ed5fae9d5` + admission route | #464/#466/#467 unresolved |
| GitHub live canary | #465 / executor #490 / registration #494 / REST #496 / event #492 / durable #500/#501 | `EXTERNAL_EVIDENCE / COMPLETED` | run `32296935756`; receipt `da227e94215a1b28a9e550546242c8a482bd718f7b35d67f159ccaa95f23efe5`; `[]→[486]→[]` | `REMOTE_CANARY_EDGE_ONLY`, semantic authority false |
| Live-owner transfer | #485 / #502/#503 | `CONVERGENCE / MERGED` | #503 Human-admitted ownership transfer | #376 retains distinct Development residual |
| GitHub DAG producer repair | #497 / #504 | `REPAIR / MERGED` | current producer selftest `7 positive / 23 mutations` | generic `--apply` and manual Development surface separate |
| Codex result-tree repair | #505 / #507 | `REPAIR / MERGED` | merge `249abc47847f8295b1c75c9d4c84457c5126fd89` | fresh signed-in v2 runtime still `NOT_EXERCISED` |
| Public consumer bootstrap | #361/#364/#366 → external consumer PR #53 | process/external-consumer evidence | consumer merge `02e4f57c229660ffd551c831ce408420cd63ca0b`; merge tree equals reviewed `5e50c8a33197bf994f23e9a0ef888793629ca840` | local Agent/provider/cross-consumer/release unproven |
| UCR capability-preserving refactor | #398–#406 / PR #477 + post-merge #482 | admitted independent programme | current UCR trace/README | unseen domains/provider uplift/release separate |

## Current unresolved owner index

```text
#376  generic Development sidebar manual PR/branch link/unlink
      OPEN / RESIDUAL

#464  signed-in Codex SDK/controller v2 result-tree receipt
      OPEN / NOT_EXERCISED

#466  real Herdr lifecycle
      OPEN / NOT_EXERCISED

#467  article/PDF/PRD truth + real source/provider closure
      OPEN / EVIDENCE_DEPENDENT
```

Release and production promotion remain `NOT_PERFORMED`.

## Wave-2 immutable history

Canonical admission record: [`CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md`](CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md).

At admission the selected sibling denominator was:

```text
Codex SDK       4 / 14
GitHub DAG      6 / 17
Herdr           4 / 18
problem closure 6 / 22
```

Historical consumed source PRs were closed-unmerged and became repository bytes through #455 convergence. Rejected/corrupted/stale ancestors remain in `CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md` and `skills/git-town-stacked-pr-worker/README.md`; they are not alternate current merge candidates.

Post-admission #497/#504 raised the **current** GitHub DAG producer controls to `7 / 23`. It does not rewrite the historical admission denominator.

## Wave-3 immutable history and later live evidence

Canonical infrastructure/admission record: [`WAVE3_ADMISSION.md`](WAVE3_ADMISSION.md).

At admission:

```text
Codex live acceptance   1 / 12
GitHub canary            1 / 6
Herdr lifecycle          2 / 7
source compiler          4 source kinds / 11 mutations
```

The later #465 remote receipt is a distinct stronger evidence lane. It proved one reversible public fixture edge only. It cannot promote #464, #466, #467, #376, release or production.

#505/#507 subsequently repaired the Codex live-acceptance contract so the changed-file denominator is independently bound to an immutable post-turn result tree. Pre-#507 live receipts are historical and cannot satisfy the v2 contract.

## Proof-carrying Skill refactor route

Detailed human trace: [`SKILL_REFACTOR_PROOF_STACK.md`](SKILL_REFACTOR_PROOF_STACK.md).

```text
#307/#309 → PR #308  causal repair
└─ #312 → PR #315    production-shaped hermetic proof
   └─ #319 → PR #323 portable proof contract/registry
      └─ #320 → PR #324 Agent routes + directory State Machines/DAG
         └─ #321 → PR #325 Molecular convergence/index
```

Independent scheduler/Shadow/delivery/provider lanes remain independent evidence rather than fake children.

## Source / article / PDF programmes

Current closure is in [`CURRENT_PUBLIC_REPOSITORY_STATE.md`](CURRENT_PUBLIC_REPOSITORY_STATE.md). Key rule:

```text
SOURCE_PROPOSAL != METHOD_IMPLEMENTED
METHOD_IMPLEMENTED != LIVE_VERIFIED
LIVE_TECHNICAL != USER_VALIDATED
USER_VALIDATED != PAID_VALIDATED
PR_MERGED != RELEASED
```

Representative still-open higher lanes:

- #115 STE100/Controlled Technical Language: no official/proprietary standard-pack compliance claim without exact pack + qualified Human evidence; integrated physical A/B remains separate.
- #362 Dual-Agent contract leaf: local worktree/gates not complete even though parent #359 method is closed.
- #316 physical old/new Tech Lead matched behavioural A/B.
- #368 exact causal context-to-Serena provider chain.
- #357–#373 Product Reverse C/K/E/D plus live user/paid/session evidence.
- #386 Repository Entropy current-main C/K/A/E/X/D closure plus live safe-deletion/adoption/Git Town evidence.

## Open Stack publication classes

These older open programmes are **not** safe to merge from historical ancestry without current-main reconstruction and fresh evidence:

```text
Spatial / Knowledge Graph   #412 → #419 / #420 → #450
Repository Entropy          old #387–#391 / #404 line
Kenn Agentic Engineering    #395 → #396
Productization              #434 provenance-blocked publication
```

Classification: `RECONSTRUCT_ON_CURRENT_MAIN` unless the owning issue proves a narrower exact relation.

## Four-repository documentation history

The Method/Runtime/Consumer/Integration plane relationship remains historical architecture. Consumer snapshots in this repository are navigation only; current consumer state must be read from its repository. The #366 real public consumer bootstrap is a specific bounded canary and not universal cross-consumer proof.

## Controlled Technical Language route

Parent programme #115; architecture law remains [`../architecture/CONTROLLED_TECHNICAL_LANGUAGE_HARNESS.md`](../architecture/CONTROLLED_TECHNICAL_LANGUAGE_HARNESS.md). Merged deterministic leaves retain their own exact-head evidence. Source proposal, official standard-pack admission, safety-critical semantic acceptance, real proprietary-document privacy and official compliance representation remain stronger separate lanes.

## Spatial and substrate methods

Static/deterministic spatial/system contracts do not prove privileged root/KVM/cgroup/seccomp/network/hardware/chaos/security execution. Open Spatial/Knowledge programmes must be rebound to current main before publication; no old Stack head is current authority by name alone.

## Local Handoff route

Historical queues are immutable exact-subject history. Current local queue epoch:

[`../../skills/agentic-tech-lead-orchestration/references/public-main-local-handoff-queue-2026-08-20.json`](../../skills/agentic-tech-lead-orchestration/references/public-main-local-handoff-queue-2026-08-20.json)

Only #464 is in this serial queue. #376 manual UI, #466 independent Herdr and #467 external source/provider evidence remain separately owned.

## Evidence boundary

PR presence, issue state, ancestry, mergeability, documentation completion, deterministic fixture PASS, hosted workflow success, terminal `done`, model agreement or an external link cannot substitute for live effects, source truth, Human Admit, release or production readiness.