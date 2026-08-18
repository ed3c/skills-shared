# `knowledge-continuity`

This Skill removes knowledge gaps that force readers to reconstruct missing context. Its `SKILL.md` is the procedural core; deterministic checks live in `scripts/` and `tests/`; generic routing contracts live in `references/`; domain examples live in `modules/`.

## Read order

1. [`SKILL.md`](SKILL.md) — measure → repair → re-measure procedure and human review.
2. [`references/README.md`](references/README.md) — generic reusable contracts.
3. [`modules/README.md`](modules/README.md) — on-demand domain examples.
4. `scripts/` and `tests/` — executable checks and controls.
5. [`evals.json`](evals.json) — eval inventory.

## Directory ownership

```text
knowledge-continuity/
├── README.md
├── SKILL.md
├── evals.json
├── references/   generic reusable contracts and machine shapes
├── modules/      on-demand domain examples
├── scripts/      the deterministic checker and its semantic gate
└── tests/        controls, frozen refactor treatments and the matched A/B
```

The file-level index is not copied here, because a hand-kept basename list drifts
the moment a file lands — this tree already lost `references/INTENT_BOUND_CONSTRAINTS.md`
that way. Read the current one out of the tree instead:

```bash
# 從 repo 根目錄執行（[`skills/README.md`](../README.md) 的共用路由）
python3 scripts/check_skill_entry_routes.py --skill knowledge-continuity --print-index
```

## State machine

```text
DOCUMENT_SELECTED
→ BREAKPOINTS_MEASURED
→ LOCAL_SUMMARIES_REPAIRED
→ ROUTES_VERIFIED
→ HUMAN_CAUSAL_REVIEW
→ CONTINUITY_ACCEPTED
```

The repository-routing extension uses the same logic: root route → nearest README → machine authority → evidence, while leaving an in-place summary at every hop.

## Decoupling rule

- General method and laws stay in `SKILL.md`.
- Generic route vocabulary stays in `references/`.
- The four-repository worked application stays in `modules/` and is loaded only for cross-repository routing tasks.
- Consumer-specific current states stay in consumer repositories, not here.
