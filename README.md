# skills-shared — canonical cross-repository Skills

`skills-shared` is the **Instruction / Method Plane** shared by Claude Code, Codex CLI and repository consumers. A shared Skill name has one canonical body and one Git history. Classification authority is [`registry.json`](registry.json); portable behavior lives in each `SKILL.md`; executable truth lives in contracts, scripts, tests, receipts, workflows and exact Git subjects.

> **Agent entry:** read [`AGENTS.md`](AGENTS.md), [`CONTEXT.md`](CONTEXT.md), [`ARCHITECTURE.md`](ARCHITECTURE.md), [`docs/INDEX.md`](docs/INDEX.md), [`docs/architecture/STATE_MACHINES.md`](docs/architecture/STATE_MACHINES.md), and [`docs/traceability/TRACEABILITY_INDEX.md`](docs/traceability/TRACEABILITY_INDEX.md).

## Four-repository role

```text
skills-shared
  procedural Skills, generic contracts, proof/eval/evolution truth
        ↓ immutable requirements/releases
runtime-env
  secret-free variable/module/profile/workload/policy closure
        ↓ exact bindings
bettor-arena
  module composition, proof/control/mutation, Context Capsules,
  stateless MCP and consumer acceptance
        ↓ admitted consumer contracts
agent-shield-monorepo
  domain product modules, provider adapters and product canaries
```

The arrows represent immutable releases, requirements, locks and receipts—not mutable sibling imports. Local symlinks are development projections, not release identity. See [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md).

## Document routing

```text
task
→ root AGENTS/current/stable context
→ docs index and State Machines
→ nearest AGENTS.md + README.md
→ machine authority
→ exact evidence and traceability
```

Each hop leaves a local summary before linking away. Markdown is navigation, not a second registry, schema, verifier, receipt, workflow result or merge authority.

## Skill anatomy

```text
skills/<name>/
├── AGENTS.md          mandatory local read order and authority contract when needed
├── README.md          directory ownership, State Machine, DAG, data flow, current handoff
├── SKILL.md           portable workflow, laws and stop conditions
├── references/        reusable host-neutral contracts/templates
├── modules/           trigger-selected domain/golden/provider instances
├── scripts/           executable mechanisms
├── tests/             positive, hollow, mutation and integration controls
├── evals.json         eval inventory when used
└── cases.json         deterministic routing/case inventory when used
```

The separation is load-bearing. Consumer branches, paths, credentials, sessions, local indexes and live receipts remain in consumer/runtime bindings.

Worked patterns:

- [`knowledge-continuity`](skills/knowledge-continuity/README.md) — procedural continuity and routed evidence.
- [`forgejo-delivery-loop`](skills/forgejo-delivery-loop/README.md) — local forge contracts, deterministic router and consumer binding.
- [`github-delivery-loop`](skills/github-delivery-loop/README.md) — GitHub publication and merge-preflight boundaries.
- [`git-town-stacked-pr-worker`](skills/git-town-stacked-pr-worker/README.md) — molecular sibling/child/worktree/sync method.
- [`agentic-tech-lead-orchestration`](skills/agentic-tech-lead-orchestration/README.md) — task/capability DAG, Workers, tournament and convergence.
- [`skill-refactor-proof-loop`](skills/skill-refactor-proof-loop/README.md) — frozen treatments, old-strength retention, matched proof layers and golden registry.

## Repository topology → State Machine ownership

```text
skills-shared/
├── registry.json                   shared/repo-owned admission ledger
├── skills/                         canonical methods, modules and proof owners
├── evals/                          cases, holdouts, fixtures, verifiers, runtime identities,
│                                   adapters, capability unlocks, releases and scorecards
├── mutations/                      hypothesis/candidate/evidence/promotion lineage
├── scripts/                        deterministic control-plane transitions
├── tests/                          regression and mutation-kill proofs
├── .github/workflows/              execution arrival; not semantic authority by itself
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

Canonical distribution does not prove capability; an LLM judge does not create hard-gate truth; adaptive mutation cannot read holdout outcomes; ecosystem quality cannot compensate for failed capability gates; release requires deterministic evidence, rollback material and Human Admit.

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
→ LIVE_AB_PENDING / LIVE_AB_VERIFIED
→ DELIVERY_EVIDENCE_BOUND
→ HUMAN_ADMIT_REQUIRED
```

Proof layers:

```text
L0 SOURCE_FREEZE
L1 STRUCTURAL_REACHABILITY
L2 EXECUTABLE_CONTRACT
L3 HERMETIC_REAL_TASK
L4 MATCHED_LIVE_MODEL_RUNTIME
L5 DELIVERY_AND_HUMAN_ADMIT
```

A lower layer cannot be promoted by prose. A matched L3+ comparison uses the same base/tree/contracts/tests/budget/carrier and retains failed, stale, blocked, cancelled and superseded attempts. Eligible golden proofs are content-bound and reference their owner implementation without copying it.

## Evidence data flow

```text
SKILL.md + implementation
        ├── registry/shared-skills-infra → canonical projection/drift evidence
        ├── refactor-proof contract      → frozen treatment and route evidence
        └── cases + sealed holdout
                    ↓
        implementation-target validation + verifier calibration
                    ↓
        runtime / harness adapters or hermetic matched carrier
                    ↓
        canonical trace + deterministic receipts
                    ↓
        content-bound evidence bundle / golden registry
             ┌──────┴───────────┐
             ↓                  ↓
       mutation lane      matched live/delivery lanes
             ↓                  ↓
       promotion gate      separate evidence owners
             └────────────→ release receipt
                               ├── separated scorecards
                               ├── rollback artifact
                               └── Human Admit
```

## Current implementation state — 2026-08-17

The repository now carries the first proof-carrying Skill-refactor line:

```text
PR #308  deterministic Tech Lead reachability and receipt-gated causal repair
└─ PR #315 production-shaped matched hermetic real-task A/B
   └─ PR #323 canonical `skill-refactor-proof-loop` and golden registry
      └─ Agent documentation / State Machine / DAG / data-flow leaf
```

The matched deterministic carrier observed:

```text
A_OLD_MONOLITH             PASS
B0_REFACTOR_AS_LANDED      BLOCKED_DISPATCH_ROUTE_ABSENT
B1_REACHABILITY_REPAIRED   PASS
B2_CAUSAL_DAG_REPAIRED     PASS
B3_CLOSURE_LAWS_BOUND      PASS
A/B1/B2/B3 final bytes      equivalent
```

Current proof ceiling:

```text
L0 source freeze              PASS
L1 structural reachability    PASS
L2 executable contract        PASS
L3 hermetic real task         PASS
L4 matched live model/runtime NOT_EXERCISED
L5 delivery/Human Admit       HUMAN_ADMIT_REQUIRED
```

B2 improves causal and evidence closure, not live model quality. B3 binds the dual-DAG and lane-substitution closure laws into the same core and dominates B2 on the deterministic criteria; the proof ceiling above is unchanged by it. Open evidence owners are #312 Phase 2, #231 scheduler, #232 independent Shadow, #234 Git Town/dual-forge, and #256 exact-subject code-intelligence/executor adapters. Merge, release and production remain outside Agent authority.

Other landed control-plane mechanisms include implementation-target binding, verifier calibration, mutation admission, holdout isolation, capability/release schemas, isolated Shared Skills Infra CI, Intent-Bound Constraints, pinned Git Town canaries, Skill-suite arrival coverage, [controlled-language authority gates](docs/architecture/CONTROLLED_TECHNICAL_LANGUAGE_HARNESS.md), repository capability audits and procedural Shadow contracts. Current capability/release registries may still be empty; mechanism implementation does not imply the first physical unlock or release.

## Git Town / molecular PR model

Git Town is optional tooling; GitHub PR base/head metadata is publication truth.

```text
independent path-disjoint work → sibling branches
unmerged contract dependency  → true child branch
smallest behavior + tests      → terminal leaf
stable prerequisites + indexes → one convergence leaf
```

A child must name the parent artifact/contracts it consumes. A branch, PR, issue close or green documentation check cannot substitute for implementation/evidence state. Semantic conflict, force push, ship, merge, release and rollback remain bounded Human/trusted-operator actions.

## Local canonical projection

The repository stores no machine-specific path in versioned contracts. Install/projection discovers the checkout and writes local path state only to ignored/host-owned surfaces.

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
HUMAN_ADMIT_REQUIRED
```

A workflow skipped by policy is not execution evidence. A job that never receives a runner is not repository-test FAIL or PASS. Source prose, diagrams, package presence, an old SHA, another environment or a hermetic lower-layer proof cannot create current live/delivery truth.

## Agent continuation checklist

1. Read root routes, State Machines and traceability.
2. Inspect current `main`, exact open PR base/head and owning workflow arrival.
3. Identify the transition, path owner and authority boundary.
4. For a refactor, freeze A/B0/B1+ and protected old strengths before mutation.
5. Select procedural core, references and triggered modules explicitly.
6. Preserve holdout, verifier, optimizer, denominator, cleanup, release and Human authorities.
7. Run owning positive/hollow/mutation/matched-task controls.
8. Update nearest `AGENTS.md`, README, current handoff and traceability when topology changes.
