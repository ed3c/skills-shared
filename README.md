# skills-shared — canonical cross-repository Skills

`skills-shared` is the **Instruction / Method Plane** shared by Claude Code, Codex CLI and admitted consumers. A shared Skill name has one canonical body and one Git history. Classification authority is [`registry.json`](registry.json); portable behavior lives in each `SKILL.md`.

> **Agent entry:** read [`AGENTS.md`](AGENTS.md), [`CONTEXT.md`](CONTEXT.md), [`ARCHITECTURE.md`](ARCHITECTURE.md), [`docs/INDEX.md`](docs/INDEX.md), [`registry.json`](registry.json), then the nearest Skill README and machine authorities. Before refactoring a shared `SKILL.md`, read [`skills/procedural-core-refactor/README.md`](skills/procedural-core-refactor/README.md).

## Repository role and four-plane data flow

```text
skills-shared
  portable procedures, schemas, deterministic assertions, proof methods
        │ immutable Skill/release/binding identities
        ▼
runtime-env
  secret-free runtime/module/profile/workload/policy closure
        │ exact environment receipts
        ▼
bettor-arena
  composition, Context Capsules, proof/control/mutation and acceptance
        │ admitted product binding
        ▼
agent-shield-monorepo and other consumers
  domain products, provider adapters, production canaries and live receipts
```

The arrows represent immutable releases, requirements, bindings, locks and receipts—not mutable sibling imports. Local symlinks are development projections, not release identity. See [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md).

## Document routing

```text
task
→ README / AGENTS / CONTEXT / ARCHITECTURE
→ docs index
→ registry + skills index
→ nearest directory README
→ SKILL.md / references / selected modules
→ scripts / tests / evals / cases
→ exact issue / branch / PR / head / CI / receipt
→ Human or runtime handoff
```

Every complex directory README maps ownership, current integration state, inputs/outputs, State Machine, DAG, data flow, assertion owner, evidence ceiling, stop/handoff and traceability. Markdown is navigation, not a second registry, schema, verifier, runtime receipt or merge authority.

## Skill anatomy

```text
skills/<name>/
├── README.md          current state, ownership, State Machine, DAG and data flow
├── SKILL.md           portable procedure, laws, evidence ceilings and handoff
├── references/        host-neutral contracts, schemas, immutable identities
├── modules/           trigger-selected domain/provider/consumer/proof specializations
├── scripts/           executable assertions and receipt emitters
├── tests/             positive, hollow, mutation, integration and A/B controls
├── evals.json         runnable claim inventory when used
└── cases.json         deterministic case/routing inventory when used
```

The separation is load-bearing, but separation alone is insufficient. A correct design also requires executable routes, module trigger/predecessor/receipt causality, evidence ceilings and matched proof for any behavioral claim.

## Canonical procedural-core refactor standard

[`procedural-core-refactor`](skills/procedural-core-refactor/README.md) is mandatory before changing the ownership boundary of another shared Skill.

```text
REQUEST_BOUND
→ BASELINE_FROZEN
→ OWNERSHIP_CLASSIFIED
→ CORE_EXTRACTED
→ DOMAIN_MODULED
→ ROUTES_WIRED
→ ASSERTIONS_BOUND
→ STRUCTURAL_AB
→ REAL_TASK_AB
→ GOLDEN_PROOF_ADMITTED
→ REGISTRY_INDEXED
→ DELIVERY_HANDOFF
```

It prevents a common false improvement: a cleaner provider-neutral `SKILL.md` whose scripts, assertions, modules or runtime transitions became unreachable.

Required proof properties:

- historical treatment bytes are immutable;
- old strengths and intermediate regressions remain visible;
- every hard law reaches a checker and planted control;
- module reachability is separate from trigger/predecessor/receipt-gated invocation;
- fixture and synthetic evidence cannot become live model/provider/delivery PASS;
- behavioral A/B uses the same task, base/tree, immutable tests, budgets, carrier and denominator;
- local success cannot overrule the global objective or cleanup;
- issue → branch → PR → exact head/tree → CI → receipt → evidence ceiling is traceable;
- merge, publication, provider activation, permission change, semantic conflict, release and promotion remain Human/repository authority.

## Agentic Tech Lead golden proof

The current worked proof is [`agentic-tech-lead-orchestration`](skills/agentic-tech-lead-orchestration/README.md).

### Structural/executable comparison

```text
A   old monolith             9 / 11
B0  refactor as landed       6 / 11
B1  reachability repaired   10 / 11
B2  causal DAG repaired     11 / 11
```

The result preserves two truths:

1. the old monolith had real strengths, including an explicit T0–T10 causal narrative and pre-dispatch assertion;
2. the first modular refactor regressed by disconnecting semantic assertion ordering, concrete module routing and self-activation refusal.

B2 retains provider neutrality while adding task shape/semantic gates and trigger-, predecessor-, subject-, module- and receipt-gated capability transitions.

### Production-shaped deterministic task

A matched canary uses one immutable repository subject and the same contracts, tests, budgets and deterministic Worker carrier. It executes real linked worktrees and overlapping subprocesses, a three-candidate tournament with a failed candidate retained, checkpoint/retry lineage, wrong-base convergence refusal, local-pass/global-fail veto, global-objective closure and cleanup.

```text
A   PASS
B0  BLOCKED_DISPATCH_ROUTE_ABSENT
B1  PASS
B2  PASS
```

The executed arms produced equivalent final bytes. The demonstrated B2 advantage is stronger causal admissibility, not superior model-generated code.

Evidence ceilings:

```text
structural proof                         PASS / DETERMINISTIC_FIXTURE
production-shaped orchestration          PASS / SYNTHETIC_RUNTIME
live model/provider adapters              NOT_EXERCISED
Git Town / Forgejo / publication          NOT_EXERCISED
merge / promotion                         HUMAN_ADMIT_REQUIRED
```

## Repository topology → state ownership

```text
skills-shared/
├── registry.json                   shared/repo-owned admission ledger
├── skills/                         canonical procedures and per-Skill proof surfaces
├── evals/
│   ├── cases/                      public development and replay contracts
│   ├── holdout/                    sealed post-selection contracts
│   ├── fixtures/                   replay and verifier calibration inputs
│   ├── verifiers/                  deterministic outcome authority
│   ├── runtime/                    executor/model/harness/environment identity
│   ├── adapters/                   external harness normalization
│   ├── capability-unlocks.json     verified held-out capability state
│   ├── releases.json               admitted release registry
│   └── scorecards/                 ecosystem quality and verified capability
├── mutations/                      hypothesis/candidate/evidence/promotion lineage
├── scripts/                        deterministic control-plane transitions
├── tests/                          regression and mutation-kill proofs
├── .github/workflows/              orchestration; not semantic authority by itself
└── docs/                            routing, current handoff, roadmap and traceability
```

## Integrated Skill Eval/Evolution state machine

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

Canonical distribution does not prove capability. An LLM judge does not create hard-gate truth. Adaptive mutation cannot read holdout outcomes. Ecosystem quality cannot compensate for failed capability gates. Release requires deterministic evidence, rollback material and Human Admit.

## Current molecular Stack — 2026-08-17

### Tech Lead repair and real-task proof

```text
#307 / PR #308
  branch: fix/307-tech-lead-runtime-reachability
  exact candidate: 504c18f10d3380be4874a59f7cfad5c290daa93f
  evidence: DETERMINISTIC_FIXTURE
  │
  └─ #312 / PR #315
     branch: agent/312-tech-lead-real-task-ab
     exact candidate: 403a4f041c5f8c07b0d7c8bb0ef2ccc44ac0f113
     evidence: SYNTHETIC_RUNTIME
```

### Refactor standard

```text
#326 epic
└─ #327 / PR #330  portable method + typed contract
   exact candidate: cffa44526d0d3e895256df36c2c7a1628fff49e2
   │
   └─ #328 / PR #331  checker + mutations + Tech Lead golden proof
      exact candidate: f65e19c848831f2fcac5ed1f9c66e80b5680243f
      │
      └─ #329 / convergence PR  AGENTS/README/registry/CI/Stack indexes
```

These are true child edges because each child consumes unmerged parent contracts or bytes. Path-disjoint live lanes remain independent:

- #231 — live multi-Worker scheduler lifecycle;
- #232 — independent Shadow/global-objective enforcement;
- #234 — actual Git Town plus dual-forge consumer delivery;
- #256 — exact-subject provider/tool receipts;
- #312 Phase 2 — matched live model/harness A/B.

See [`skills/git-town-stacked-pr-worker/README.md`](skills/git-town-stacked-pr-worker/README.md) for the complete molecular index. A pending or absent workflow stays `NOT_EXERCISED`; PR existence is not CI PASS.

## Git Town / molecular PR model

```text
independent path-disjoint work
→ sibling branches

unmerged contract or implementation dependency
→ true child branch

smallest reviewable behavior + tests/evidence
→ terminal leaf

verified parent/children + shared indexes/registry/CI
→ convergence leaf
```

Git Town is optional tooling. GitHub PR base/head metadata and exact Git objects are publication truth. A logical Stack is not evidence that the Git Town binary ran.

## Local canonical projection

The repository stores no machine-specific path in versioned contracts. Install/projection discovers the checkout from the running script and writes local path state only to ignored or host-owned surfaces.

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
IMPLEMENTED
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
INSUFFICIENT_EVIDENCE
CONTESTED
HUMAN_ADMIT_REQUIRED
```

A workflow skipped by trigger policy is not execution evidence. A job that never receives a runner is not PASS or FAIL. Source prose, diagrams, package presence, an old SHA, a fixture, a synthetic canary or another environment cannot create current live capability truth.

## Source-proposal boundary

Attached architecture documents and PDFs are `SOURCE_PROPOSAL`. Their proposed worktree fan-out, tournament prompts, Contract-First constraints, DAGs, Stacked PRs, code-intelligence tools, cloud/local runtimes, cost, latency, licensing, recovery and security require independent verification, implementation, exact receipts and Human Admit before becoming repository truth.

## Agent continuation checklist

1. Read root routes and current integration state.
2. Inspect current `main`, exact open PR base/head and whether owning workflows executed.
3. Identify the state-machine transition and authority boundary.
4. Invoke `procedural-core-refactor` before changing another shared Skill boundary.
5. Select procedural core, references and modules from frozen triggers.
6. Preserve verifier, holdout, optimizer, release, runtime and Human authorities.
7. Run owning positive, hollow, mutation and matched A/B controls.
8. Update nearest README, AGENTS/current handoff and molecular trace when topology changes.
9. Report residual `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `INSUFFICIENT_EVIDENCE` and `HUMAN_ADMIT_REQUIRED` states.
