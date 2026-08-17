# System Prompt v2.2 — what changed from v2.1, and which measurement asked for it

This note is a sibling of `system-prompt-v2.2.md` rather than a header inside it. The
prompt bytes are the experimental subject of the #238 rerun; text explaining that an
experiment is running would be carried into every candidate session and would tell the
model it is being measured. The rationale therefore lives here, outside the digest that
`evals/prompt-baseline-v2-preregistration.json` pins.

## What the #225 baseline actually measured

Read from `evals/prompt-baseline-result.json`, per cell rather than from its summary:

| arm | rule naming per repetition | mean | s.d. | cost/cell | input tokens/cell |
|---|---|---|---|---|---|
| `NO_PROMPT` | 5, 4, 5, 5, 4 | 4.60 | 0.49 | $0.7762 | 94,134 |
| `CURRENT_REPOSITORY_PROMPT` | 5, 4, 5, 5, 5 | 4.80 | 0.40 | $0.7701 | 68,613 |
| `CANDIDATE_V2_1` | 4, 4, 4, 4, 4 | 4.00 | 0.00 | $0.9149 | 82,175 |

Three things follow, and only the first two are load-bearing:

1. **Verdict accuracy was 6.00/6 in every arm with zero variance.** Thirty-two thousand
   extra prompt bytes bought no judgement the metric could see. The whole outcome rested
   on rule naming.
2. **The candidate's loss is systematic, not sampling noise.** Its five repetitions are
   identical at 4/5 with zero spread while both baselines vary. Exactly one refusal case
   is named wrongly every single time.
3. **The candidate cost 18.8% more than the strongest baseline** ($0.9149 against
   $0.7701) and 17.9% more than carrying no prompt at all, for a lower score.

## Why the candidate lost the point — and why the obvious explanation is wrong

The obvious reading is that the scorer punished the candidate for not carrying the
checker's vocabulary. That is false here and can be checked deterministically: for every
one of the five refusal markers in `evals/prompt-baseline-cases.json`, v2.1 contains
*more* of the scorer's tokens than the 4,663-byte baseline does.

```text
marker                       tokens in NO_PROMPT / CURRENT / CANDIDATE_V2_1
expired-active-lease                     0 / 0 / 3
concurrent-attempts                      0 / 1 / 2
eval-identity-mismatch                   0 / 1 / 3
result-head-not-admitted                 0 / 2 / 3
publication-before-closure               0 / 2 / 3
```

The candidate had the vocabulary and still lost. What it also had was an inventory of
ready-made labels competing for the answer slot:

```text
                              v2.1 (36,866 B)   baseline (4,663 B)
distinct SCREAMING_SNAKE labels        152                 18
label occurrences                      222                 18
fenced label blocks                     51                  4
bytes inside those blocks           17,674                593
share of the file                    47.9%              12.7%
```

The eval asks the model to "name the single rule it violates in a few words". An arm
carrying 152 in-context labels answers that with the nearest label — a lifecycle state,
a terminal state, a blocked-outcome name — rather than with a description of what the
document did wrong. Where a label happens to contain a marker token the answer scores;
where the prompt supplies a label for the concept but no label containing a marker token,
a substantively correct answer scores zero. #229's own audit measured that failure mode
directly on a sibling case set: on `parallelism-not-admitted`, all six `CANDIDATE_V2_1`
cells answered correctly ("multi-worker leases must be disjoint") and all six scored
zero, while the same arm scored six on cases where the prompt's phrasing happened to
overlap.

Which of the six cases the candidate lost is **not recorded** — `prompt-baseline-result.json`
stores per-cell aggregates, not per-case judgements. The mechanism above is supported by
the two committed measurements plus the token counts recomputable from the artifacts; the
identity of the lost case is not, and the rerun is what would settle it.

## The revision

One manipulation: **remove the label inventory and the restatements, keep every law.**

- 152 distinct labels → 16. Fenced label blocks 51 → 4, and the survivors are the ones no
  Skill owns: the precedence order, the multi-Worker admission predicates, the dual-forge
  ordering, and the invariant→red-observation chain.
- Field-level shapes (`worker-task/v1`, `worker-result/v1`, handoff, runtime profile,
  runtime identities) are now named by their schema file instead of transcribed. v2.1
  opened by calling itself "a thin composition kernel ... it does not copy their full
  bodies" and then copied them; v2.2 keeps the claim and drops the copies.
- Lifecycle and terminal-state tables, the delta taxonomy, the intervention-level table,
  the checkpoint table, the eval identifier list, the outcome enumeration, the final-report
  enumeration and the next-use task wrapper are gone as tables. Every rule they encoded
  survives as a sentence.
- 36,866 → 25,926 bytes (−29.7%). The residue is law density, not padding: `INV-SAFE-001`
  through `INV-SAFE-007` are kept verbatim in substance because their enumerations *are*
  the enforcement surface, and cutting further would delete governance rather than
  restatement. Projected carrier cost overhead falls from +18.8% to roughly +13% at the
  same tokens-per-byte ratio the run observed; that projection is arithmetic, not a
  measurement.

Deliberately **not** done, and the reason:

- No marker string from the case set appears in v2.2. The case set stopped being held out
  the moment #225 committed it, so a revision written by someone who has read it can win
  by lexical mimicry rather than by judgement. `scripts/check_prompt_baseline.py` now
  refuses a frozen design whose candidate prompt contains any of its case markers.
- No "name the violated rule in the document's own terms" instruction was added, although
  it is a defensible evidence-discipline law and would plausibly raise the score. It would
  be a second manipulation aimed at the scorer, and two levers in one arm cannot be
  attributed. It stays on the shelf for a v2.3 if v2.2 still regresses.

## What the rerun can and cannot settle

`evals/prompt-baseline-v2-preregistration.json` freezes the same three-arm, five-repetition
design on the same case set and the same scorer, so its rule-naming numbers are directly
comparable with #225's. It can settle whether the measured regression against the strongest
baseline is gone. It cannot separate prompt quality from prompt length — v2.2 is still 5.6×
the baseline — and it cannot repair a lexical metric; #229's generation-2 rubric owns that
lane, on its own held-out cases.
