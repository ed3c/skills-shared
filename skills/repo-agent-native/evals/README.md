# repo-agent-native Evals

This directory owns the old-vs-new admission contract for issue #89.

## State machine

```text
BASELINE PINNED
→ CASES ADMITTED
→ HARD ASSERTIONS DEFINED
→ CANDIDATE BUILT
→ OFFLINE SELFTEST
→ BLIND PAIRED RUNS
→ GRADING
→ COST/QUALITY REPORT
→ ADMIT OR REJECT
```

## Evidence classes

- Offline fixtures verify schemas, source anchors, fallback behavior, and planted failures.
- Claude Code and Codex CLI runs verify host routing and actual Skill behavior.
- One host cannot proxy the other.
- Documentation and a green parser cannot proxy model/task quality.

## Admission rule

All hard gates must pass, no critical case may regress, weighted quality must improve, and median instruction/context cost must decrease. Missing carrier runs remain `NOT_EXERCISED`.

## Change contract

Cases and weights are reviewed before candidate results are visible. A candidate PR may add a missing adversarial case, but must rerun baseline and candidate under the same case/version contract.
