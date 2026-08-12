# skills-shared — canonical cross-repository Skills

`skills-shared` is the **Instruction / Method Plane** shared by Claude Code and Codex CLI projects. A shared Skill name has one canonical body and one Git history. Classification authority is [`registry.json`](registry.json); portable behavior lives in each `SKILL.md`.

> **Agent entry:** read [`AGENTS.md`](AGENTS.md), [`CONTEXT.md`](CONTEXT.md), [`ARCHITECTURE.md`](ARCHITECTURE.md), and [`docs/INDEX.md`](docs/INDEX.md). Current Skill Eval/Evolution truth is in [`docs/AGENT_INTEGRATION_STATE.md`](docs/AGENT_INTEGRATION_STATE.md); target phases are in [`docs/SKILL_EVAL_ROADMAP.md`](docs/SKILL_EVAL_ROADMAP.md).

## Four-repository role

```text
skills-shared
  procedural Skills, generic method contracts, Skill eval/evolution truth
        |
        v
runtime-env
  secret-free variable/module/profile/workload/policy closure
        |
        v
bettor-arena
  module composition, proof/control/mutation, Context Capsules,
  stateless MCP, project bootstrap, origin/external-release acceptance
        |
        v
agent-shield-monorepo
  domain product modules, provider adapters, and product canaries
```

The arrows represent immutable releases, requirements, bindings, locks, and receipts—not mutable sibling imports. Local symlinks are development projections, not release identity. See [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md).

## Document routing

All four repositories use compatible route names:

```text
README.md
AGENTS.md
CLAUDE.md
CONTEXT.md
ARCHITECTURE.md
docs/INDEX.md
docs/architecture/DOCUMENT_ROUTING.md
docs/architecture/STATE_MACHINES.md
docs/integration/CROSS_REPO_INTEGRATION.md
docs/traceability/TRACEABILITY_INDEX.md
<governed-directory>/README.md
```

The route is:

```text
task
→ root procedure/current/stable context
→ docs index
→ nearest directory README
→ machine authority
→ current evidence and traceability
```

Each hop leaves a local summary before linking away. Markdown is navigation, not a second registry, schema, verifier, receipt, or merge authority.

## Skill anatomy

```text
skills/<name>/
├── README.md          navigation, ownership, state-machine and data-flow map
├── SKILL.md           procedural generalization: workflow, method, laws, stop conditions
├── references/        reusable host-neutral contracts/templates
├── modules/           domain instances loaded only when their trigger matches
├── scripts/           executable mechanisms
├── tests/             positive, hollow, mutation and integration controls
├── evals.json         eval inventory when used
└── cases.json         deterministic routing/case inventory when used
```

The separation is load-bearing:

- `SKILL.md` remains portable and procedural.
- `references/` remains reusable and domain-neutral.
- `modules/` carries detailed Forgejo, repository, provider, or product instances and is loaded on demand.
- Consumer branch names, paths, credentials, runtime sessions, and live receipts remain in consumer bindings and environments.

Worked patterns:

- [`knowledge-continuity`](skills/knowledge-continuity/README.md) — procedural continuity loop + generic routing reference + on-demand four-repository example.
- [`forgejo-delivery-loop`](skills/forgejo-delivery-loop/README.md) — procedural delivery law + generic contracts + Forgejo domain modules + deterministic Bun router + consumer registry binding.
- [`github-delivery-loop`](skills/github-delivery-loop/README.md) — GitHub delivery, Actions publication, and merge-preflight state machines.
- [`git-town-stacked-pr-worker`](skills/git-town-stacked-pr-worker/README.md) — portable molecular branch/worktree/sync method.

## Repository topology → state-machine ownership

```text
skills-shared/
├── registry.json                   shared/repo-owned admission ledger
├── skills/                         canonical Skill artifact and method state
├── evals/
│   ├── cases/                      public dev + gold-replay contracts
│   ├── holdout/                    sealed post-selection contracts
│   ├── fixtures/                   replay + verifier calibration inputs
│   ├── verifiers/                  deterministic outcome authority
│   ├── runtime/                    executor/model/harness/environment identity
│   ├── adapters/                   external harness normalization
│   ├── capability-unlocks.json     verified held-out capability state
│   ├── releases.json               admitted release registry
│   └── scorecards/                 ecosystem quality and verified capability
├── mutations/                      hypothesis/candidate/evidence/promotion lineage
├── scripts/                        deterministic control-plane transitions
├── tests/                          regression and mutation-kill proofs
├── .github/workflows/              orchestration, not semantic authority by itself
└── docs/                            routing, current handoff, roadmap and traceability
```

## Integrated Skill state machine

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

Authority separation is intentional: canonical distribution does not prove capability; an LLM judge does not create hard-gate truth; adaptive mutation cannot read holdout outcomes; ecosystem quality cannot compensate for failed capability gates; release requires deterministic multi-stack evidence, rollback material, and Human Admit.

## Evidence data flow

```text
SKILL.md + implementation
        ├── registry/shared-skills-infra → canonical projection and drift evidence
        └── cases + sealed holdout
                    ↓
        implementation-target validation + verifier calibration
                    ↓
        runtime / harness adapters
                    ↓
        canonical run trace
                    ↓
        deterministic verifier receipt
                    ↓
        content-bound evidence bundle
             ┌──────┴──────┐
             ↓             ↓
       mutation lane   sealed holdout lane
             ↓             ↓
       lineage and     capability unlock
       promotion            ↓
             └────────→ release receipt
                           ├── separated scorecards
                           ├── rollback artifact
                           └── Human Admit
```

## Current implementation state — 2026-08-12

Landed mechanisms include:

- implementation-target binding for real-incident evals (#72);
- verifier positive/hollow calibration (#73);
- evidence-driven mutation admission and holdout isolation (#74);
- canonical-drift mutation proof (#75);
- verified capability release receipts, scorecard separation, and rollback contract (#76);
- isolated Shared Skills Infra CI (#77);
- private GitHub Actions publication gating and billing circuit behavior (issue #43 and the landed implementation line).

The Phase 4/5 contract Stack is no longer active: #73, #74, and #76 are merged. The only current open PR at this snapshot is the document-routing sibling [`#85`](https://github.com/ed3c/skills-shared/pull/85); exact open-head identity remains GitHub metadata, not embedded prose.

The capability/release registries remain intentionally empty:

```text
evals/capability-unlocks.json  unlocks = []
evals/releases.json            releases = []
```

Therefore:

```text
release hard-gate mechanism     IMPLEMENTED
first physical capability unlock NOT_EXERCISED / absent
first canonical capability release NOT_EXERCISED / absent
```

Real post-selection evidence still requires deterministic verification across at least two real model/harness stacks before Human Admit.

## Git Town / molecular PR model

Git Town is optional tooling; GitHub PR base/head metadata is publication truth.

```text
independent path-disjoint work
→ sibling branches

unmerged contract/data dependency
→ true child branch

smallest reviewable behavior + tests/evidence
→ terminal leaf

stable merged siblings + shared index/cold-start audit
→ convergence leaf
```

The current four-repository documentation set is four independent siblings:

```text
skills-shared#85
runtime-env#30
agent-shield-monorepo#78
bettor-arena#37
```

After all four merge, `bettor-arena#38` owns exact merged commit/tree indexing and fresh Claude/Codex cold-start convergence. Do not create that branch early.

## Local canonical projection

The repository stores no machine-specific path in versioned contracts. Install/projection discovers the checkout from the running script and writes local path state only to ignored/host-owned surfaces.

```bash
python3 skills/shared-skills-infra/scripts/shared_skills.py install \
  --project /path/to/project-a --project /path/to/project-b

python3 skills/shared-skills-infra/scripts/shared_skills.py check
python3 skills/shared-skills-infra/scripts/shared_skills.py report
bash skills/shared-skills-infra/tests/verify.sh
```

A project-local shared-name copy is shadowing unless `registry.json` classifies the name as repo-owned.

## Evidence states

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
```

A workflow skipped by trigger policy is not execution evidence. A job that never receives a runner is not repository-test FAIL or PASS. Source prose, diagrams, package presence, an old SHA, or another environment cannot create current capability truth.

## Source-proposal boundary

The attached architecture document proposes E2B/Firecracker, local/cloud synchronization, mobile, wallet, security, licensing, cost, latency, and repair. These are candidate domain/provider inputs—not current shared-method or runtime facts. Independent verification, implementation, evals, canaries, receipts, and Human Admit are required.

## Agent continuation checklist

1. Read root routes and [`docs/AGENT_INTEGRATION_STATE.md`](docs/AGENT_INTEGRATION_STATE.md).
2. Inspect current `main`, exact open PR base/head, and whether owning workflows executed.
3. Identify the state-machine transition and authority boundary.
4. Select procedural core, optional references, and domain modules explicitly.
5. Preserve holdout, verifier, optimizer, release, and Human authorities.
6. Run the owning positive and hollow/mutation controls.
7. Update the nearest README, current handoff, and traceability when topology changes.
