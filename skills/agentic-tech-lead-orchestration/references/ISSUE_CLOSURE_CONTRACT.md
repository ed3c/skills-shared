# Issue Closure Contract

Machine authority: `issue-closure-contract.schema.json` plus `../scripts/assert_issue_closure_contract.py`. This document is navigation, State Machine, DAG and evidence-ceiling guidance only.

## Why this exists

GitHub `closed/completed` is lossy. It cannot distinguish a directly landed implementation from a closed-unmerged leaf consumed by convergence, a completed phase whose residual was transferred, or a superseded line. The closure contract makes that distinction explicit without rewriting historical Issue prose.

A PR number is repository-local, not globally unique. Every candidate PR and every landing therefore binds `owner/repo` plus PR number; every durable landing additionally binds immutable commit and tree identity. This is required for cross-repository closure such as `skills-shared#366 → website-design-compiler#53`.

## State Machine

```text
ISSUE_DEFINED
→ ACCEPTANCE_FROZEN
→ IMPLEMENTATION_BOUND
→ EVIDENCE_BOUND
→ RESIDUAL_CLASSIFIED
→ LANDING_BOUND
→ SHADOW_REVIEWED
→ CLOSURE_ELIGIBLE
→ CLOSED
```

A missing binding is `ABSENT`. Issue state, PR state, Markdown, branch names and model agreement cannot fill it.

## Closure DAG and data flow

```text
Issue acceptance ───────────────┐
implementation candidate PRs ───┼→ closure contract → deterministic gate → Shadow readback
immutable convergence/main ─────┤                                  │
residual/successor owners ──────┘                                  └→ projection / Human closure decision
```

`DIRECTLY_LANDED` requires a merged direct candidate plus repository-qualified immutable landing commit/tree. `CONSUMED_BY_CONVERGENCE` requires the closed-unmerged consumed candidate and a separate repository-qualified immutable landing subject. `SCOPE_TRANSFERRED` requires every transferred acceptance obligation to name its successor. `SUPERSEDED` and `NOT_PLANNED` preserve explicit non-completion semantics rather than laundering them into implementation success.

## Initial Shadow audit cases

- `#312`: semantic drift control. Phase 1 may be satisfied, but Phase 2 cannot disappear behind `completed`; bind the successor owners explicitly.
- `#403/#404`: indirection control. A closed-unmerged documentation leaf is not landed merely because its Issue is closed; bind the admitted convergence/current-main subject.
- `#505/#507`: positive direct-landing control.
- `#366`: positive real-consumer cross-repository closure pattern; intermediate `READY_FOR_HUMAN_ADMIT` did not substitute for final post-merge readback and `website-design-compiler#53` must not be represented as ambiguous bare `#53`.

## Evidence ceiling

The checker is deterministic and zero-network. A green result proves only that the supplied closure packet is internally consistent with these laws. It does not query GitHub, prove that a claimed SHA is on current `main`, execute a consumer/runtime, perform Human admission, merge, release or production promotion. Provider metadata and immutable Git subjects must be read independently before constructing the packet.

## Local Handoff Execution Queue

```text
1. run unit controls for assert_issue_closure_contract.py
2. validate every closure-audit packet against Draft 2020-12 schema
3. execute the semantic gate for every audited packet
4. confirm exact provider subjects for #312/#403/#505/#366
5. run exact-head repository governance / Skill Suite arrivals
6. independent Shadow checks exact branch head and changed-file denominator
7. only then consider Human Admit / merge
```

The ChatGPT GitHub connector can publish repository bytes and read provider metadata but is not a local checkout. Local Git Town/Forgejo execution remains `NOT_EXERCISED` until an exact-subject local/runtime receipt exists.
