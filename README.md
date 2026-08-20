# skills-shared — canonical cross-repository Skills

`skills-shared` is the canonical **Instruction / Method Plane** shared by Claude Code, Codex CLI and repository consumers. A shared Skill has one canonical body and one Git history. Classification authority is [`registry.json`](registry.json); portable behavior lives in each `SKILL.md`; executable truth lives in contracts, scripts, tests, receipts, workflows and exact Git subjects.

> **Agent entry:** read [`AGENTS.md`](AGENTS.md), [`CONTEXT.md`](CONTEXT.md), [`ARCHITECTURE.md`](ARCHITECTURE.md), [`docs/INDEX.md`](docs/INDEX.md), then [`docs/traceability/CURRENT_PUBLIC_REPOSITORY_STATE.md`](docs/traceability/CURRENT_PUBLIC_REPOSITORY_STATE.md) before historical programme snapshots.

## Repository role

```text
skills-shared
  Instruction / Method Plane
  portable procedures + contracts + deterministic proof/eval/evolution law

runtime-env
  Runtime Contract Plane
  secret-free runtime/profile/policy/wire-shape closure

consumer repositories
  domain composition + live runtime + product acceptance + mutable receipts

external evidence / Human
  source truth, provider/live effects, manual UI, merge, release, promotion
```

Cross-repository arrows represent immutable releases, requirements, locks and receipts—not mutable sibling imports. See [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md) and [`docs/architecture/DOMAIN_DECOUPLING.md`](docs/architecture/DOMAIN_DECOUPLING.md).

## Current public repository state

Canonical human projection: [`docs/traceability/CURRENT_PUBLIC_REPOSITORY_STATE.md`](docs/traceability/CURRENT_PUBLIC_REPOSITORY_STATE.md).

Current audit baseline after the #505 repair:

```text
main 249abc47847f8295b1c75c9d4c84457c5126fd89
tree a24b9b7ace6f4022967d41262ecdc704d5c11646
```

The baseline is an immutable observation, not a floating alias. Re-read `main` before action.

### Closed/admitted control-plane line

```text
Wave-2 #375/#376/#377/#378
        ↓ selected sibling bytes
#379 / PR #455                       MERGED
        ↓
Wave-3 #464/#465/#466/#467
        ↓ selected sibling bytes
#468 / PR #480 + #484                MERGED / POST-MERGE CLOSED
        ↓
#465 public Issue Dependencies canary LIVE_GITHUB_DEPENDENCY_CANARY_PASS
#485 / PR #503                       live-owner transfer MERGED
#497 / PR #504                       generic blockedBy producer repair MERGED
#505 / PR #507                       Codex result-tree repair MERGED
#366 external public consumer        hosted bootstrap + consumer CI + merge CLOSED
```

Important current evidence split:

```text
#376 Development sidebar generic link/unlink  RESIDUAL / MANUAL_OR_UNEXPOSED_API
#464 signed-in Codex v2 acceptance            NOT_EXERCISED after #507
#466 real Herdr lifecycle                     NOT_EXERCISED
#467 article/PDF/PRD + provider truth         EVIDENCE_DEPENDENT
release / production promotion                NOT_PERFORMED
```

A closed mechanism parent does not close its live successor. #465's bounded fixture-edge PASS does not grant semantic task-DAG authority and does not satisfy #376's manual Development-link residual.

## Document routing

```text
task
→ root AGENTS / CONTEXT / ARCHITECTURE
→ docs/INDEX.md
→ CURRENT_PUBLIC_REPOSITORY_STATE.md for current closure work
→ nearest governed-directory AGENTS.md + README.md
→ machine authority
→ exact issue/PR/runtime/evidence subject
```

Markdown is navigation and human projection, not a second registry, schema, verifier, receipt, workflow result or merge authority.

## Skill anatomy

```text
skills/<name>/
├── AGENTS.md          local read order, writer/authority law, completion packet
├── README.md          directory ownership, State Machine, DAG, data flow, evidence ceiling
├── SKILL.md           portable workflow, laws and stop conditions
├── references/        reusable host-neutral contracts/templates
├── modules/           trigger-selected instances/adapters
├── scripts/           executable mechanisms
├── tests/             positive, hollow, mutation and integration controls
├── evals.json         eval inventory when used
└── cases.json         deterministic routing/case inventory when used
```

The separation is load-bearing. Consumer branches, paths, credentials, sessions, local indexes and live receipts remain in consumer/runtime bindings.

Worked patterns:

- [`agentic-tech-lead-orchestration`](skills/agentic-tech-lead-orchestration/README.md) — task/capability DAG, Workers, convergence, result-tree-bound Codex acceptance and Local Handoff.
- [`git-town-stacked-pr-worker`](skills/git-town-stacked-pr-worker/README.md) — molecular sibling/child/convergence/worktree/sync method and terminal PR index.
- [`skill-refactor-proof-loop`](skills/skill-refactor-proof-loop/README.md) — frozen treatments, old-strength retention, matched proof layers and golden registry.
- [`github-delivery-loop`](skills/github-delivery-loop/README.md) — GitHub publication and merge-preflight boundaries.
- [`forgejo-delivery-loop`](skills/forgejo-delivery-loop/README.md) — local forge contracts and recovery routing.
- [`knowledge-continuity`](skills/knowledge-continuity/README.md) — procedural continuity and routed evidence.

## Repository topology → State Machine ownership

```text
skills-shared/
├── registry.json                   shared/repo-owned classification
├── skills/                         canonical methods + module/proof owners
├── evals/                          cases, holdouts, fixtures, verifier/release contracts
├── mutations/                      hypothesis/candidate/evidence/promotion lineage
├── scripts/                        deterministic control-plane transitions
├── tests/                          regression and mutation-kill proofs
├── .github/workflows/              execution arrival; never semantic authority by itself
└── docs/                            routing, State Machines, current handoff and traceability
```

## Integrated Skill evolution State Machine

```text
DISCOVERED
→ CANONICALIZED
→ CLAIM_REGISTERED
→ CASE_BOUND
→ VERIFIER_CALIBRATED
→ EXECUTABLE
→ EVIDENCE_COLLECTED
→ MUTATION_EVALUATED
    ├── lost / tie / reverted → PRESERVED
    └── won + recomputed evidence → PROMOTION_ELIGIBLE
→ sealed post-selection holdout
→ CAPABILITY_UNLOCKED
→ RELEASE_ADMITTED
→ CANONICAL_RELEASED
    └── regression / drift → ROLLBACK or new mutation
```

Canonical distribution does not prove capability; an LLM judge does not create hard-gate truth; adaptive mutation cannot read holdout outcomes; release requires deterministic evidence, rollback material and Human Admit.

## Proof-carrying Skill refactor State Machine

Every material Skill refactor follows [`skill-refactor-proof-loop`](skills/skill-refactor-proof-loop/README.md):

```text
REFRACTOR_PROPOSED
→ OLD_BEHAVIOR_FROZEN
→ TREATMENTS_FROZEN
→ OLD_STRENGTHS_BOUND
→ ROUTES_ASSERTED
→ CONTRACTS_ASSERTED
→ HERMETIC_TASK_EXECUTED
→ DENOMINATOR_RECONCILED
→ GOLDEN_PROOF_REGISTERED
→ ADOPTION_READY
→ LIVE_AB_PENDING | LIVE_AB_VERIFIED
→ DELIVERY_EVIDENCE_BOUND
→ HUMAN_ADMIT_REQUIRED
```

Proof layers remain separate:

```text
L0 SOURCE_FREEZE
L1 STRUCTURAL_REACHABILITY
L2 EXECUTABLE_CONTRACT
L3 HERMETIC_REAL_TASK
L4 MATCHED_LIVE_MODEL_RUNTIME
L5 DELIVERY_AND_HUMAN_ADMIT
```

A lower layer cannot be promoted by prose. Failed, stale, blocked, cancelled and superseded attempts remain in the denominator.

## Current Tech Lead / Shadow evidence flow

```text
request / source
→ exact repository subject
→ contract + task/capability DAG
→ path/resource/worktree/session leases
→ deterministic mechanisms + negative controls
→ isolated attempts
→ source/diff/test/result-tree readback
→ optional GitHub/Herdr/source evidence lanes
→ independent Shadow same-subject review
→ problem/closure recomputation
→ convergence or Local Handoff
→ Human Admit when required
```

The current signed-in Codex acceptance contract is v2: the Worker materializes an immutable result tree using a private Git index, the controller reads `base_sha^{tree}`, recomputes exact base→result-tree changed paths, then requires controller source/diff/test readback. A prior v1 live receipt cannot satisfy this v2 contract.

## Source / article / PDF boundary

Source documents are `SOURCE_PROPOSAL`. The current closure matrix is in [`CURRENT_PUBLIC_REPOSITORY_STATE.md`](docs/traceability/CURRENT_PUBLIC_REPOSITORY_STATE.md).

Examples:

```text
STE100 / CTL            method/deterministic architecture exists; official pack/Human/live A/B remain stronger lanes
Dual-Agent              parent method closed; #362 local executable contract still open
Parallel-Agent          individual adapters exist; one causal provider chain remains open
Product Reverse         C/K/E/D programme not fully admitted
Repository Entropy      PARTIALLY_INTERNALIZED / NOT_CLOSED; stale Stack needs current-main reconstruction
```

Never turn package/license/performance/source prose into repository or legal truth without its own evidence.

## Git Town / molecular PR model

Git Town is optional tooling; GitHub PR base/head metadata is publication truth.

```text
independent path-disjoint work → SIBLING
unmerged byte dependency      → TRUE_CHILD
shared index/integration      → CONVERGENCE
ordering without ancestry     → PROCESS_DEPENDENCY
runtime/source/manual proof   → EXTERNAL_EVIDENCE
prior immutable subject       → HISTORICAL
```

Current terminal Molecular index is in [`skills/git-town-stacked-pr-worker/README.md`](skills/git-town-stacked-pr-worker/README.md). Old Spatial/Knowledge, Entropy, Kenn and other stale programme PRs must be reconstructed/revalidated on current main before publication; old green evidence is not carried forward by branch name.

## Local Handoff

Historical queue epochs stay immutable. Current local queue:

[`skills/agentic-tech-lead-orchestration/references/public-main-local-handoff-queue-2026-08-20.json`](skills/agentic-tech-lead-orchestration/references/public-main-local-handoff-queue-2026-08-20.json)

The serial ACTIVE item is #464 signed-in Codex v2 acceptance. Independent #376 manual UI, #466 Herdr and #467 source/provider evidence stay on their own issues rather than being falsely serialized.

## Local canonical projection

The repository stores no machine-specific checkout path in versioned portable contracts.

```bash
python3 skills/shared-skills-infra/scripts/shared_skills.py install \
  --project /path/to/project-a --project /path/to/project-b

python3 skills/shared-skills-infra/scripts/shared_skills.py check
python3 skills/shared-skills-infra/scripts/shared_skills.py report
bash skills/shared-skills-infra/tests/verify.sh
```

Immutable consumer binding lifecycle: [`docs/modular-consumer-contract.md`](docs/modular-consumer-contract.md).

## Evidence states

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
EVIDENCE_DEPENDENT
HUMAN_ADMIT_REQUIRED
```

A skipped workflow is not execution evidence. A source proposal, historical SHA, issue closure or documentation check cannot create a stronger runtime/provider/user/release truth.

## Agent continuation checklist

1. Read root routes and current public-state trace.
2. Inspect current `main`, exact open PR base/head and owning workflow arrival.
3. Identify transition, path owner and authority boundary.
4. Reconstruct stale Stack programmes on current main instead of reusing old green ancestry.
5. For refactors, freeze A/B0/B1+ and protected old strengths before mutation.
6. Preserve holdout, verifier, denominator, cleanup, release and Human authorities.
7. Run owning positive/hollow/mutation/matched-task controls.
8. Update nearest `AGENTS.md`, README, current handoff and traceability only through one convergence owner.