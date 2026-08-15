# Intent-Bound Constraint Harness

## Purpose

The Harness converts an Agent's meta-intent into a falsifiable proof chain. A constraint is valid only when it names the intent and proof obligation that it protects.

```text
Meta Intent
→ Proof Obligation
→ Constraint
→ Evaluator
→ Positive / Negative / Mutation Control
→ Exact-subject Receipt
→ Completion Decision
```

Failure uses a controlled diagnostic loop:

```text
Constraint Failure
→ Intent-at-Risk
→ Diagnosis Code
→ Allowlisted Repair
→ Expected Measurable Delta
→ Re-evaluation
→ VERIFIED | BLOCK | REJECT | HUMAN_ADMIT_REQUIRED
```

## Authority boundaries

| Authority | Role |
|---|---|
| Contract schema | portable interchange shape |
| Semantic closure evaluator | cross-reference, evidence, repair, and module laws |
| Domain evaluator | decides the declared domain subject |
| Negative and mutation controls | prove that a hard assertion can turn red |
| Diagnostic Reflection Receipt | records a bounded decision without private chain-of-thought |
| Exact-subject receipt | binds repository/artifact, contract, evaluator, fixtures, and freshness |
| Human Admit | owns semantic conflict, merge, permission widening, promotion, and destructive rollback |

The closure evaluator does not replace existing Skill evaluators. Domain Skills register their current checkers as evaluator identities.

## Core laws

1. Every meta-intent declares one or more proof obligations.
2. Every proof obligation is discharged by a constraint that protects the owning intent.
3. Every hard constraint has a deciding deterministic or externally observed evaluator.
4. Every hard constraint has a negative control and a mutation control.
5. Deterministic failure vetoes advisory success.
6. Missing or stale external evidence is not `PASS`.
7. A repairable constraint declares an allowlist, a retry budget, and an expected delta metric.
8. A Human-owned or terminal constraint has zero automatic retries.
9. No-improvement stops the repair loop.
10. A module may add or tighten constraints. A module cannot weaken constraints, widen effects, or bypass Human Admit.
11. Ambiguous module routing blocks execution.
12. A receipt becomes stale when its subject, contract, evaluator, fixture, or environment identity changes.

## Reflection boundary

Do not request, persist, or publish private chain-of-thought. Emit only operationally necessary diagnostic fields:

```text
run_id
subject_identity
contract_identity
evaluator_identity
failed_constraint_id
intent_at_risk
observation_summary
evidence_refs
diagnosis_code
repair_hypothesis
selected_repair
expected_delta
retry_index
actual_delta
decision
stop_reason
```

## State machine

```text
DISCOVERED
→ INTENT_BOUND
→ PLAN_VALIDATED
→ PRECONDITIONS_VERIFIED
→ EXECUTING
→ ASSERTING
    ├── VERIFIED
    └── CONSTRAINT_FAILED
          → DIAGNOSED
              ├── REPAIRING → ASSERTING
              ├── BLOCKED
              ├── REJECTED
              └── HUMAN_ADMIT_REQUIRED
```

`VERIFIED` requires evidence for the exact current subject. An old-SHA, documentation-only, skipped, or unavailable lane remains distinct.

## Procedure / domain separation

```text
repository-wide schemas and closure evaluator
  generic intent/constraint/receipt semantics

domain Skill
  stable intents, proof obligations, evaluator registrations, controls

consumer repository
  exact paths, branches, task packets, environment, receipts

Human / trusted operator
  authority-changing decisions
```

## Git Town mapping

A Stack edge represents a real proof or byte dependency, not scheduling preference.

```text
foundation
├── path-disjoint sibling
├── path-disjoint sibling
└── true child that consumes parent bytes

admitted leaves
└── convergence/index leaf
```

A child receipt is stale when the declared parent head changes. Independent work remains siblings. Shared indexes belong to a separate convergence owner.

## Commands

```bash
python3 scripts/check_intent_bound_constraints.py \
  contract evals/fixtures/intent-bound-constraint/valid-contract.json

python3 scripts/check_intent_bound_constraints.py \
  receipt evals/fixtures/intent-bound-constraint/valid-receipt.json \
  --contract evals/fixtures/intent-bound-constraint/valid-contract.json

python3 -m unittest tests/test_intent_bound_constraints.py -v
```

Exit states:

```text
0   declared subject passed
2   evaluated contract or receipt failed
64  input or usage error
70  evaluator failure
```

## Evidence boundary

These files prove only schema syntax and semantic closure behavior when executed. They do not prove a domain evaluator, live Git Town operation, remote publication, physical model run, consumer canary, merge, or release.
