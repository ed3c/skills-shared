# Closure audit ledger

Machine packets in this directory record one reviewed closed-Issue disposition each. They are checked by `../../scripts/assert_issue_closure_contract.py` against `../issue-closure-contract.schema.json`.

## State Machine

```text
PROVIDER_FACTS_READ
→ ACCEPTANCE_CLASSIFIED
→ CANDIDATE_PR_BOUND
→ LANDING_BOUND_OR_TRANSFER_BOUND
→ RESIDUAL_OWNER_BOUND
→ EVIDENCE_CEILING_BOUND
→ INDEPENDENT_SHADOW_REVIEWED
→ PACKET_VALIDATED
```

## DAG and data flow

```text
GitHub Issue ────────────────┐
GitHub PR / merge commit ────┼→ issue-*.json → schema → semantic gate → CI receipt
cross-repo landing ──────────┤
successor/residual Issues ───┘
```

The JSON packet is a checked projection; GitHub/Git provider subjects remain the source for state and immutable identities.

## Initial audited denominator

| Issue | Disposition | Implementation / landing | Evidence ceiling |
|---|---|---|---|
| `#312` | `SCOPE_TRANSFERRED` | Phase-1 PR `ed3c/skills-shared#315`; Phase-2 → `#231/#232/#234/#256` | `DETERMINISTIC` |
| `#403` | `CONSUMED_BY_CONVERGENCE` | candidate `ed3c/skills-shared#404` closed-unmerged; landed closure route via `#511` | `DETERMINISTIC` |
| `#505` | `DIRECTLY_LANDED` | `ed3c/skills-shared#507` | `DETERMINISTIC` |
| `#366` | `DIRECTLY_LANDED` | cross-repo `ed3c/website-design-compiler#53` | `HUMAN_ADMITTED` for the bounded consumer-bootstrap lane |

## Evidence ceiling

CI validates packet shape and semantic closure laws. It does not independently query GitHub during execution and cannot prove provider facts beyond the immutable identities compiled into each reviewed packet. Any provider movement or newly discovered contradiction requires a fresh packet review, not silent reinterpretation.
