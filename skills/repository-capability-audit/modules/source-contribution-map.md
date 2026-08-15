# Source contribution map

The effectiveness percentage counts semantic procedural claims, not words or tokens. A long explanation and a one-line invariant each count once only when they express one independently removable procedure.

The current committed fixture set supports these source fractions:

| Source | Runtime-supported claims | Candidate claims | Fraction |
|---|---:|---:|---:|
| Current auditor system prompt | 13 | 16 | 81.25% |
| Spatial systems method | 5 | 7 | 71.43% |
| External verification method | 2 | 3 | 66.67% |
| Judge routing method | 1 | 3 | 33.33% |
| Controlled-language harness | 2 | 4 | 50.00% |
| Knowledge-continuity method | 1 | 3 | 33.33% |
| Delivery-loop method | 3 | 5 | 60.00% |
| Dependency aggregate | 14 | 25 | 56.00% |

Overlapping claims can map several sources to one retained core rule. The aggregate answers “how many source claims are supported in this audit niche”; it is not a sum of unique core laws and is not a quality score for the source skill outside this niche.

Unproven claims remain in `evals/contract.json`. `UNPROVEN_FOR_CORE` means the current fixture set has no deciding delta, not that the procedure is generally useless.

## Deterministic support versus live Agent support

The percentages above are Layer A measurements: removal of semantic procedure claims changes a deterministic executable-fixture outcome. They do not measure whether an Agent reads or applies the text.

Layer B uses [`agent-effectiveness.md`](agent-effectiveness.md) and `evals/agent-effectiveness-contract.json`. Until matched live language-model Agent receipts exist, every live per-rule and per-source contribution remains `NOT_EXERCISED`; the deterministic 56% dependency fraction must not be relabeled as model-level causal contribution.
