# Repository Portfolio Control — C0 Foundation Trace

Tracking: `ed3c/skills-shared#560`  
Owner: `agentic-tech-lead-orchestration`  
Stage terminal: `PORTFOLIO_CONTROL_C0_DETERMINISTIC_READY_FOR_HOSTED_EPOCH`

## Problem closure

The repository already owns task DAGs, capability admission, Shadow review, Git Town delivery, GitHub observation, Local Handoff, bootstrap, and Issue closure. The missing layer was one portfolio-level snapshot, acceptance compiler, seven-graph model, Codex subagent join barrier, and one-shot hosted-evidence contract.

C0 adds that narrow composition. It does not create a new mega-Skill or second task-state owner.

## Mandatory execution sentence

```text
Use subagents. Wait for all agents and consolidate their findings.
```

This sentence is stored in the canonical controller prompt and every role template. The deterministic join gate refuses early, missing, duplicate, stale, failed-agent-dropped, contradiction-dropped, and state-mismatched joins.

## Directory → owner → state transition

| Surface | Owner | Provides | Evidence ceiling |
|---|---|---|---|
| `references/REPOSITORY_PORTFOLIO_CONTROL.md` | Tech Lead law | authority split, state machine, graph/join/CI laws | static law |
| `references/prompts/repository-portfolio-controller-v3.md` | controller prompt | zero-context portfolio execution procedure | prompt persistence |
| `references/contracts/*.schema.json` | contract plane | snapshot, acceptance, graph, dispatch/result/join and CI shapes | schema consistency |
| `references/codex-agents/*.toml.template` | Codex binding plane | seven trigger-selected role templates | parse/persistence only |
| `scripts/compile_repository_portfolio.py` | compiler | snapshot + acceptance → G1-G7 + ready waves | deterministic fixture/current input |
| `scripts/assert_portfolio_multigraph.py` | graph gate | cycle, ancestry, conflict, wave and convergence refusal | deterministic |
| `scripts/assert_subagent_dispatch.py` | runtime/model gate | exact model, egress, role lease and terminal denominator | deterministic |
| `scripts/assert_subagent_join.py` | join gate | complete dispatch/result denominator and verdict | deterministic |
| `scripts/assert_one_shot_ci_epoch.py` | CI gate | one Ready transition, frozen head, non-empty hosted evidence | deterministic packet validation |
| `tests/portfolio-control/**` | eval plane | schema/TOML/compiler/positive/mutation denominator | hermetic C0 |
| `.github/workflows/repository-portfolio-control.yml` | GitHub hosted arrival | ready-for-review and exact-main C0 execution | hosted deterministic when exercised |

## State machine

```text
C0_CONTRACTS_ABSENT
→ C0_PROMPT_AND_ROLE_BINDINGS_PRESENT
→ C0_SCHEMAS_VALID
→ C0_GRAPH_COMPILER_VALID
→ C0_DISPATCH_GATE_VALID
→ C0_ALL_AGENT_JOIN_VALID
→ C0_ONE_SHOT_CI_GATE_VALID
→ C0_HERMETIC_DENOMINATOR_GREEN
→ C0_DRAFT_PUBLISHED
→ C0_READY_ONCE
→ C0_EXACT_HEAD_HOSTED_GREEN
→ C0_SHADOW_READBACK
→ READY_FOR_HUMAN_ADMIT
```

A Draft PR or locally green fixture is not `C0_EXACT_HEAD_HOSTED_GREEN`. A workflow run from another SHA cannot satisfy this stage.

## Molecular DAG

```text
#560 frozen problem/authority contract
└─ C0 contract + prompt foundation
   ├─ seven schemas                         SIBLING files / one interface atom
   ├─ seven Codex role templates            SIBLING files / read-mostly bindings
   ├─ graph compiler + semantic gate         TRUE_CHILD of frozen schemas
   ├─ dispatch/result/join gates             TRUE_CHILD of frozen schemas
   ├─ one-shot CI packet gate                TRUE_CHILD of frozen schema
   └─ C0 selftest + dedicated workflow       CONVERGENCE
         ↓
      exact-head hosted receipt
         ↓
      independent Shadow readback
         ↓
      Human merge admission
```

The C0 implementation is path-disjoint from the open Kenn and Spatial/Knowledge-Graph Draft stacks observed during preparation. A fresh changed-path readback is still required before merge because path ownership is mutable.

## Data flow

```text
trusted GitHub/local snapshot
+ exact Issue/PR acceptance packets
→ compile_repository_portfolio.py
→ portfolio-multigraph/v1
→ assert_portfolio_multigraph.py
→ ready waves
→ subagent-dispatch/v1 packets
→ exact terminal subagent-result/v1 packets
→ assert_subagent_join.py
→ subagent-join-receipt/v1
→ frozen Draft candidate
→ one ready-for-review transition
→ exact-head GitHub workflow readback
→ one-shot-ci-epoch/v1
→ Issue Closure Contract / residual owners
```

## Deterministic denominator

C0 requires:

```text
7 Draft 2020-12 schemas valid
7 TOML role templates parse
7 templates contain the exact join barrier
prompt contains G1-G7, all-agent join and one-shot CI laws
compiler emits truthful TRUE_CHILD and conflict serialization
multigraph positive + 6 mutations
subagent dispatch positive + 6 mutations
subagent join positive + 6 mutations
one-shot CI positive + 6 mutations
private path/secret-shaped leakage scan
```

## Evidence ceiling and residual lanes

C0 can prove portable deterministic mechanics on the exact candidate bytes. It cannot prove:

```text
live Codex CLI subagents                  NOT_EXERCISED
continuous independent Shadow runtime     NOT_EXERCISED
private-repository provider egress         NOT_EXERCISED / admission required
current six-PR reconstruction program      OUTSIDE C0
real one-shot CI                           NOT_EXERCISED until exact-head run
new-repository bootstrap canary            NOT_IMPLEMENTED in C0
merge/release/production                   HUMAN_ADMIT_REQUIRED
```

These residuals remain owned by `#560` successor atoms and the existing runtime/bootstrap authorities. No lower lane may be promoted to close them.
