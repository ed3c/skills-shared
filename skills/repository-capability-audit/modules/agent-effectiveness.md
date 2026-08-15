# Agent-level effectiveness protocol

The deterministic ablation suite answers whether a procedure is necessary for the committed executable fixtures. It does not answer whether a language-model Agent reads, recalls, or follows the Skill. Agent-level effectiveness is a separate evidence layer and must never be inferred from the deterministic report.

## Evidence layers

```text
Layer A — deterministic procedure ablation
  same physical observations
  rule-aware evaluator versus rule removal
  establishes necessity for planted cases only

Layer B — held-out Agent treatment experiment
  same hidden task and repository subject
  fresh Agent session per arm
  no-skill versus full versus trimmed versus rule ablation
  establishes bounded behavioral uplift only after repeated matched runs
```

A Layer A PASS cannot promote Layer B. A scripted or fixture Agent validates only the harness and always remains `HARNESS_SELFTEST_ONLY`.

## Matched-cell design

One comparison cell fixes every factor except treatment:

```text
hidden task digest
repository identity + immutable commit + tree
repetition
model provider/family/model/version
Agent harness/version
runtime and toolset digest
input/output/tool-call/time budgets
evaluator digest
```

The arm order is randomized and persisted. Each arm starts from a fresh session and isolated workspace. Producer conversation history, prior arm output, labels, expected defects, and evaluator ground truth are unavailable to the Agent.

## Treatment arms

```text
no_skill
current_full_composition
candidate_trimmed_skill
candidate_minus_RCA-###
```

The evaluation wrapper and required output contract are identical across arms. Only the Skill treatment changes. Full composition and trimmed treatment digests are persisted so a silent prompt edit invalidates the cell.

## Independent evaluation

The Agent never assigns its own score. An independent evaluator reads the exact task, repository state, raw tool trace, persisted artifacts, and final claims. Deterministic checks veto advisory semantic judgments.

Each receipt records:

```text
task success
material defects found / total
false passes / opportunities
evidence packet completeness
exact-subject continuity
negative-control validity
explicit non-claim accuracy
trigger correctness
tool calls, tokens, duration, cost
```

The scorer computes a declared weighted quality score and keeps every component visible. A higher fluent-answer score cannot compensate for false PASS, subject mismatch, missing evidence, invalid denial probes, or stronger-claim leakage.

## Admission decision

The thresholds are frozen in [`../evals/agent-effectiveness-contract.json`](../evals/agent-effectiveness-contract.json) before live receipts are observed.

A trimmed Skill is `SUPPORTED` only when:

1. matched live language-model Agent receipts satisfy the minimum repository, model-family, and repetition counts;
2. candidate quality materially exceeds `no_skill` with a positive paired confidence interval;
3. candidate false passes do not increase;
4. candidate and full composition are equivalent inside the declared margin;
5. experiment matching, digests, artifact continuity, and evaluator independence remain valid.

Each core rule receives a separate live state. A rule is live-supported only when removing it causes a deciding paired regression. Missing ablation receipts remain `NOT_EXERCISED`; they are not evidence that the rule is ineffective.

## Generic execution adapter

`run_agent_cell.py` is provider-neutral. An adapter command receives paths through placeholders and must create an Agent output in the isolated workspace. A separate evaluator command emits the metrics JSON.

```bash
python3 scripts/run_agent_cell.py \
  --profile candidate_trimmed_skill \
  --case-id CASE_ID \
  --repository-id OWNER/REPO \
  --commit COMMIT_SHA \
  --tree TREE_SHA \
  --repetition 1 \
  --arm-order 0 \
  --task-file /path/hidden-task.md \
  --treatment-file SKILL.md \
  --evaluator-file /path/evaluator-contract.json \
  --agent-command-json '["/path/agent-adapter","--task","{task_file}","--treatment","{treatment_file}","--workspace","{workspace}"]' \
  --evaluator-command-json '["/path/evaluator","--workspace","{workspace}","--output","{metrics_file}"]' \
  --agent-class language_model_agent \
  --agent-provider PROVIDER \
  --agent-family FAMILY \
  --agent-model MODEL \
  --agent-version VERSION \
  --agent-harness HARNESS \
  --agent-harness-version HARNESS_VERSION \
  --runtime-identity RUNTIME \
  --runtime-version RUNTIME_VERSION \
  --toolset-digest TOOLSET_SHA256 \
  --evaluator-identity EVALUATOR \
  --evaluator-version EVALUATOR_VERSION \
  --evaluator-owner independent \
  --workspace /path/isolated-workspace \
  --output /path/receipt.json
```

Codex, Claude Code, OpenCode, or another Agent is integrated through a small external adapter that maps its CLI to this file contract. The provider-specific command, credentials, workspace policy, and live receipts stay outside `SKILL.md`.

## Scoring

```bash
python3 scripts/score_agent_ab.py \
  --receipts /path/receipts \
  --output /path/agent-effectiveness.json
```

No live receipts produces `NOT_EXERCISED`. Fixture-only receipts produce `HARNESS_SELFTEST_ONLY`. Invalid digests, unmatched cells, missing main arms, mixed budgets, or self-scored output produce `INVALID_EXPERIMENT`, not a low quality score.

## Domain decoupling

Held-out repository tasks, provider adapters, device or runtime procedures, and observed result packets belong in eval or consumer-owned modules. Only a later live ablation with an exact receipt can justify changing the core rule set.
