---
name: human-led-agentic-engineering
description: Human-led Agentic Engineering composition for design admission, independent design challenge, typed Tech Lead execution, commit/branch adversarial verification, living-context persistence, and Human-owned delivery. Concrete providers remain trigger-selected adapters.
---

# Human-Led Agentic Engineering

<!-- PORTABLE_CORE_START -->

## Contract

This Skill owns Human design-admission semantics, independent design-adversary separation, provider-neutral port categories, commit/branch reconciliation semantics, living-context persistence routing, and Human-owned delivery boundaries. It composes existing canonical Skills rather than reimplementing their schedulers, Shadow runtime, architecture-delta evaluator, or Git Stack mechanics.

Concrete provider, forge, session, workspace, review, observability and consumer-command bindings are selected only through `modules/domain-profile.md`.

## Core laws

- **CORE-LAW-001 — Human material-design ownership.** Material product taste, architecture choice, irreversible scope and trade-off selection require `HUMAN_DESIGN_ADMITTED` before implementation admission.
- **CORE-LAW-002 — adversary independence.** The Design Adversary is distinct from the Builder/implementation Worker and cannot self-admit design. Model agreement remains advisory.
- **CORE-LAW-003 — provider evidence is candidate evidence.** Review/session/workspace/provider output cannot substitute for deterministic/native/domain correctness, exact-subject evidence, independent live Shadow, or Human Admit.
- **CORE-LAW-004 — modules cannot widen authority.** Trigger-selected adapters may implement ports but may not weaken core laws, suppress material dissent, alter exact-subject identity, or widen filesystem/network/secret/merge/release/production authority.
- **CORE-LAW-005 — deterministic admission cannot promote live authority.** Deterministic method/contract PASS proves only the exact deterministic lane. Live consumer adoption, independent live Shadow, merge, release and production remain separate evidence/authority states.

## State machine

```text
REQUEST_BOUND
→ HUMAN_DESIGN_ACTIVE
→ DESIGN_ADVERSARY_COMPLETE
→ HUMAN_DESIGN_ADMITTED
→ SYSTEM_CONTRACT_EXTRACTED
→ CAPABILITY_PLAN_ASSERTED
→ TASK_DAG_ASSERTED
→ WORKSPACE_LEASED
→ IMPLEMENTATION_ACTIVE
→ COMMIT_CREATED
→ COMMIT_REVIEW_RECONCILED
→ BRANCH_REVIEW_RECONCILED
→ GLOBAL_OBJECTIVE_ASSERTED
→ LIVING_CONTEXT_PERSISTED
→ DELIVERY_READY
→ HUMAN_ADMIT_REQUIRED
```

`HUMAN_DESIGN_ADMITTED` authorizes the frozen material design direction. `HUMAN_ADMIT_REQUIRED` is a later delivery boundary and does not follow automatically from deterministic or model evidence.

## Role DAG

```text
Human Designer
  ├─> Design Adversary [read-only, independent]
  └─> Tech Lead Orchestrator
         ├─> Worker(s) [disjoint leases]
         ├─> Verification provider port(s)
         └─> Shadow Architect Monitor [read-only]

verified implementation
→ branch/global objective reconciliation
→ durable context persistence
→ Stack/delivery handoff
→ Human delivery authority
```

## Data flow

```text
human intent
→ design snapshot
→ independent challenge receipt
→ Human design-admit receipt
→ typed system/task/capability contracts
→ leased implementation artifacts
→ exact commit/tree
→ candidate review evidence
→ native/domain/independent verification
→ branch/global-objective receipt
→ durable context delta
→ delivery traceability packet
→ Human delivery decision
```

## Provider-neutral ports

The portable method recognizes these categories only:

- `IntentLedgerPort`: task/design intent transport only;
- `ReviewProviderPort`: candidate review evidence only;
- `SessionObservabilityPort`: advisory/cost/trace evidence only;
- `WorkspacePort`: workspace lifecycle only;
- `SessionCarrierPort`: presentation/session transport only.

Concrete implementations, licenses, credentials, local paths, issue/PR IDs and runtime sessions belong to `modules/domain-profile.md` or consumer bindings.

## Design admission

A material design requires a receipt shaped by `references/design-admission.schema.json`, including exact repository/subject identity, problem/design digests, Human actor, adversary receipt digest, material decisions, non-goals and disposition. Material adversary dissent must be explicitly dispositioned by the Human; it may not disappear because models agree.

Required refusal vocabulary includes:

```text
MATERIAL_DESIGN_WITHOUT_HUMAN_ADMIT
DESIGN_ADVERSARY_EQUALS_BUILDER
MODEL_CONSENSUS_AUTO_ADMITS_DESIGN
UNRESOLVED_MATERIAL_DISSENT_DROPPED
MUTABLE_OR_WRONG_SUBJECT
DOMAIN_MODULE_OVERRIDES_CORE_LAW
DETERMINISTIC_PASS_PROMOTED_TO_LIVE_OR_RELEASE
```

## Commit and branch reconciliation

Provider review PASS is not branch correctness. Reconcile findings against repository-native/domain assertions; then run branch-wide integration, negative/mutation controls where applicable, and the frozen global objective. A clean per-commit review set cannot self-promote to branch closure.

## Living-context persistence

Before `DELIVERY_READY`, route durable knowledge to its owner:

```text
architecture invariant → ARCHITECTURE.md / owning context document
agent operating rule    → nearest AGENTS.md
local topology/dataflow → nearest README.md
machine transition      → schema/checker/state-machine owner
mutable handoff         → CONTEXT.md / consumer handoff owner
historical rationale    → traceability/ADR when policy admits it
```

Transient plan prose does not become architecture authority merely by being retained.

## Composition ownership

- typed task/capability DAGs, leases, convergence and Local Handoff remain owned by the Tech Lead orchestration Skill;
- read-only Shadow procedure/evidence enforcement remains owned by the Shadow runtime Skill;
- architecture delta/hidden-assumption/failure-surface monitoring remains owned by its architecture-monitoring Skill;
- molecular branch/worktree/Stack mechanics remain owned by the stacked-PR Skill;
- this Skill owns only Human-led composition/admission semantics described above.

## Executable assertions

Structural core/domain separation is checked with:

```bash
python3 scripts/check_skill_core_boundaries.py --skill human-led-agentic-engineering
```

Design-admission deterministic controls are checked with:

```bash
bash skills/human-led-agentic-engineering/tests/design-admission/verify.sh
```

A zero exit proves only those deterministic contracts for the exact checkout. It does not prove live provider execution, independent live Shadow, merge, release or production.

## Stop conditions

Stop on absent Human design admission for material design, same-identity Builder/Design-Adversary, unresolved material dissent with no Human disposition, stale/wrong-subject evidence, overlapping writer authority, provider evidence being promoted to correctness authority, domain module authority widening, or an irreversible delivery action without its owning Human/trusted-policy admission.

<!-- PORTABLE_CORE_END -->

## Domain adapters

Load `modules/domain-profile.md` only when a concrete provider/runtime/forge/session/workspace/review/observability binding is required. The module is trigger-selected and cannot override the portable core.
