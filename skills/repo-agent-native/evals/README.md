# repo-agent-native Evals

This directory owns the old-vs-new admission contract for issue #89.

## Measurement authority

At the `skills-shared` repository root, `docs/SKILL_EVAL_ROADMAP.md`, `evals/schema/run-trace.schema.json`, and `evals/schema/skill-scorecard.schema.json` own cross-Skill run identity, aggregation, mutation promotion, and the separation of ecosystem quality from verified capability. They are repository authorities rather than portable-package dependencies, so this Skill does not link or resolve outside its own root. This directory owns only the `repo-agent-native` task contract, fixture observer, and local receipts. It must not invent a second universal total score.

`Skill.md-native` is a downstream runtime/evidence plane: use it for digest-pinned compatibility cells, reproducibility/confidence, least privilege, and non-compensable security gates. It does not replace the behavior/generalization matrix here, and its weighted score cannot compensate for a failed source predicate or capability hard gate.

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

All hard gates and the bounded procedure gate must pass. Admission quality uses only independently re-observed structured predicates and procedure-contract coverage; it must improve over `current_skill`, `no_skill`, and `wrong_skill` by preregistered deltas while instruction/context cost decreases. Missing carrier runs remain `NOT_EXERCISED`.

The current quality metric is intentionally bounded. Each scored claim carries a stable predicate ID/operator/value and source reference; the evaluator independently observes its value from the exact committed fixture. This is stronger than checking whether final prose happens to contain an alias, but it remains fixture coverage rather than exhaustive fact precision.

Concept-alias matching is retained only for diagnosis under `lexical_advisory`. It cannot promote a run, affect `admission_quality`, or rescue a hard failure. Changing predicates, observers, cases, weights, or aliases after seeing candidate output changes the evaluator digest and requires every arm to be rerun.

The shared task prompt may specify subject identity and the host-supplied output schema, but it must not restate the Skill's record rules, evidence semantics, or assertion procedure. Otherwise `no_skill` and `wrong_skill` receive the treatment and cease to be controls.

`no_skill` is an untreated Skill-discovery condition, not an ignorant model and not an automatic tool stack. It receives the same task, immutable subject, and schema adapter only. It does not automatically load procedural generalization or invoke grepai, Serena, SCIP, Tree-sitter, SQLite projections, or mem0; this fixture prohibits optional providers so source reading is the common execution surface.

## Same subject and evaluator

The comparator rejects a matrix unless all four condition receipts have byte-identical identities for:

```text
carrier id/version
scenario id
fixture commit
replayable subject.bundle digest
output schema digest
ground-truth digest
eval-config digest
scorer digest
```

Only the condition-specific instruction package/digest may differ. “Same subject” is therefore not a matching path or branch name; it is the deterministic commit plus replay bundle. “Same evaluator” is the complete digest set above, not merely the same script filename.

## Procedure and generalization evidence

One output has three evidence origins:

```text
verifier_observed       deterministic subject/source/absence observations
artifact_asserted       required record groups present in the artifact
model_reported_advisory routes/tools/fallback claimed by output prose
```

Only the first two enter the local bounded procedure contract. Full procedural generalization requires at least three repetitions per condition, at least two real harnesses, and held-out perturbations spanning source mutation, provider degradation, memory conflict, and cross-module impact. The canonical cross-harness run identity and aggregation live at the repository-level Skill eval framework. Root adapters re-run this package's task-specific observer from the replay bundle, normalize results into `skill-eval-run/v1`, and enforce the complete 24-cell matrix. This Skill-local scorer must not become a competing global ranking authority.

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

The runner permits one to three repetitions. Where a carrier exposes a seed, use at least three distinct admitted seeds. Where it does not, repetitions remain stochastic samples and must not be described as seeded reproducibility. The currently implemented offline source-mutation suite is a mechanism calibration control, not the required physical cross-harness matrix.

## Adapter receipt captures

`receipts/` holds one capture: nine lanes bound to one commit. `check_adapter_receipts.py`
refuses a directory whose receipts span two commits, because a set read as one picture of
one tree has to be one picture of one tree.

There was briefly a second directory, `receipts-git-town-darwin/`: the darwin git-town
artifact was Human-admitted (`git-town-darwin-admission.json`) after the original
nine-lane capture, so its first exercised receipt ran at a later commit and could not
join the earlier set without spanning two subjects. The promised consolidation happened
on 2026-08-18: every provider went live on one host (persistent tree-sitter/lancedb venv,
built grepai index over ollama, serena project config, local Forgejo, the admitted
git-town binary), all nine lanes were recaptured at one commit, and the interim directory
was deleted by that capture — its receipt superseded by the consolidated
`receipts/git-town.receipt.json`, still bound to the same admission record and artifact
digest.

The rule that follows: a capture directory is one subject, one run, and one moment. Adding
a lane later adds a directory, never a receipt with a different subject.

## Change contract

Cases and weights are reviewed before candidate results are visible. A candidate PR may add a missing adversarial case, but must rerun baseline and candidate under the same case/version contract.
