# Source contribution map

The effectiveness percentage counts semantic procedural claims, not words or tokens. A long explanation and a one-line invariant each count once only when they express one independently removable procedure.

The table this file used to carry by hand is now derived from [`../evals/contract.json`](../evals/contract.json) and published as [`../evals/live-source-contribution.md`](../evals/live-source-contribution.md) (machine-readable: `live-source-contribution.json`, `rule-to-source-overlap.json`, `receipt-index.json`, `SHA256SUMS`). `scripts/publish_source_contribution.py --check` runs in the suite, so the published numbers cannot drift from the contract they summarise.

Overlapping claims can map several sources to one retained core rule. The published report therefore keeps four denominators apart — unique retained rules, unique semantic claims, source mappings, and dependency source mappings — and gives each source a bounded pair rather than a share. The old aggregate answered “how many source claims are supported in this audit niche”; it was never a sum of unique core laws and never a quality score for the source skill outside this niche.

Unproven claims remain in `evals/contract.json`. `UNPROVEN_FOR_CORE` means the current fixture set has no deciding delta, not that the procedure is generally useless.

## Deterministic support versus live Agent support

The published fractions are Layer A measurements: removal of semantic procedure claims changes a deterministic executable-fixture outcome. They do not measure whether an Agent reads or applies the text.

Layer B uses [`agent-effectiveness.md`](agent-effectiveness.md) and `evals/agent-effectiveness-contract.json`, and its lane states live in [`../evals/live-evidence-state.json`](../evals/live-evidence-state.json). Until matched live language-model Agent receipts exist, every live per-rule and per-source contribution remains `NOT_EXERCISED`; the deterministic dependency fraction must not be relabeled as model-level causal contribution.

What the numbers cannot decide, and why overlap prevents an independent share, is in [`measurement-limits.md`](measurement-limits.md).
