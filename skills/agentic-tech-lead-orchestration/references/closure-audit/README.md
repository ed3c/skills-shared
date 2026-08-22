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

## Shadow binding (#606)

`shadow_review.verdict = PASS` is a claim about a *second* identity, so a new packet must carry that identity and the artifact it left behind:

```json
"shadow_review": {
  "verdict": "PASS",
  "packet_author": {"host_class": "CLAUDE_CODE_LOCAL", "session_id": "…", "worktree": "…"},
  "shadow_identity": {"host_class": "CLAUDE_CODE_LOCAL", "session_id": "…", "worktree": "…"},
  "receipt": {"path": "docs/traceability/…/shadow-audit/…json", "sha256": "…"}
}
```

The gate refuses an unbound `PASS`, an anonymous Shadow (`session_id` null), a Shadow whose `(host_class, session_id, worktree)` equals the packet author's, and a receipt path that is absent or does not hash to its bound `sha256`. This is the same law as `../contracts/live-shadow-case-delta-receipt.schema.json`'s builder≠shadow rule, applied to the packet author instead of the builder.

`HUMAN_ADMIT_REQUIRED` remains the honest self-authored terminal and needs no binding. When no independent Shadow actually read the packet, that is the verdict — not a `PASS` with invented names.

Packets that were already green before this law are listed one by one in `enforced-from.json` and stay green as historical artifacts. Their verdicts were not flipped and no Shadow identity was backfilled for them, because both would be invention. Nothing may be added to that list: an entry admits one exact file name at one exact Issue number with one exact verdict, so editing a grandfathered packet's verdict drops it out of the set and the binding is required again.

## Evidence ceiling

CI validates packet shape and semantic closure laws. It does not independently query GitHub during execution and cannot prove provider facts beyond the immutable identities compiled into each reviewed packet. Any provider movement or newly discovered contradiction requires a fresh packet review, not silent reinterpretation.
