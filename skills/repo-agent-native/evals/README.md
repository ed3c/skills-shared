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
- Live carrier receipts belong to the consumer/PR evidence plane. This shared package owns the runner, schemas, cases, weights, and offline controls; it does not persist mutable sessions or live provider state.

## Admission rule

All hard gates must pass, no critical case may regress, weighted quality must improve over `current_skill`, `no_skill`, and `wrong_skill` by their preregistered deltas, and median instruction/context cost must decrease. Missing carrier runs remain `NOT_EXERCISED`.

The current quality metric is intentionally bounded. `anchored_nonforbidden_precision_proxy` proves that emitted records are source-anchored and do not contain a planted forbidden claim; it is not exhaustive fact precision. Ground-truth records use reviewed concept-alias groups so semantically equivalent phrasing can match without an LLM judge. Changing cases, aliases, or weights after seeing candidate output requires a new evaluator digest and both arms must be rescored.

The shared task prompt may specify subject identity and the host-supplied output schema, but it must not restate the Skill's record rules, evidence semantics, or assertion procedure. Otherwise `no_skill` and `wrong_skill` receive the treatment and cease to be controls.

Each physical run must preserve:

```text
same deterministic fixture commit
condition-specific Skill package and instruction digests
carrier home isolation mode and proof that user-level Skill discovery is absent
raw stdout/stderr digests
replayable subject.bundle
schema, ground-truth, weight, and scorer digests
carrier version, duration, usage, and cost when exposed
hard-gate and weighted score
isolation limitations
```

The runner permits one to three repetitions. Where a carrier exposes a seed, use at least three distinct admitted seeds. Where it does not, repetitions remain stochastic samples and must not be described as seeded reproducibility.

## Change contract

Cases and weights are reviewed before candidate results are visible. A candidate PR may add a missing adversarial case, but must rerun baseline and candidate under the same case/version contract.
