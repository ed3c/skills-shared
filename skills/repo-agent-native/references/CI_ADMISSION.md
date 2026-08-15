# repo-agent-native CI Admission Contract

> Phase-2 implementation contract for #92 / PR #93. This document does not replace the workflow. Until an owning workflow actually executes the exact candidate head, CI evidence remains `NOT_EXERCISED`.

## Why this exists

The repository-level `Skill Eval Contract` validates the global eval/evolution control plane. Its path filters do not own `skills/repo-agent-native/**`, and its Python suites do not execute the Bun structural/output selftests for this Skill family.

A different green workflow cannot proxy repo-agent-native admission.

## Required workflow identity

Target path:

```text
.github/workflows/repo-agent-native-contract.yml
```

Failure domain:

```text
repo-agent-native portable structure
+ deterministic output assertions
+ module-routing controls
```

It must not perform provider/model A/B execution.

## Trigger contract

```text
pull_request:
  ready_for_review
  reopened
  synchronize
  paths: skills/repo-agent-native/** + own workflow

push:
  branches: main
  same paths

workflow_dispatch:
  explicit recovery/diagnostic lane
```

Draft PR checkpoints must not allocate a runner-backed contract job.

Feature-branch `push` by itself must not create an extra run.

## Security and cost contract

```text
permissions: contents: read
checkout persist-credentials: false
PR/ref concurrency: cancel obsolete heads
timeout: <= 10 minutes
networked providers: forbidden
model calls: forbidden
production memory/graph writes: forbidden
```

GitHub Actions must be pinned by immutable commit SHA. The reviewed setup-bun action identity captured during Phase 2 is:

```text
oven-sh/setup-bun@0c5077e51419868618aeaa5fe8019c62421857d6
```

The workflow must also pin an explicit reviewed Bun runtime version rather than silently tracking latest.

## Required execution steps

### 1. Exact candidate identity

Record at minimum:

```text
GITHUB_SHA
git rev-parse HEAD
git rev-parse HEAD^{tree}
bun --version
```

The checked-out `HEAD` must equal the workflow candidate identity.

### 2. Deterministic selftest

```bash
bun skills/repo-agent-native/tests/selftest.ts
```

The current selftest is expected to exercise:

- canonical structural PASS;
- portable-frontmatter mutation;
- metadata-shape mutation;
- Skill line-budget mutation;
- broken relative reference;
- absolute machine path;
- missing provider module/state-machine section;
- module-law override;
- missing/invalid module-routing controls;
- exact source-ref/range/digest verification;
- working-tree bytes cannot replace recorded Git subject;
- unsupported `D` fact;
- graph/memory candidate without source read-back;
- observed-head mismatch/absence;
- negative invariant without declared search boundary;
- empty factual PASS;
- stable CLI exit behavior.

A load-bearing hollow mutation that survives is a contract failure.

### 3. Canonical structural validation

```bash
bun skills/repo-agent-native/scripts/validate-skill.ts \
  --skill-root skills/repo-agent-native \
  --json <temporary-receipt>
```

Exit must be `0` and the receipt must parse as JSON.

### 4. Declarative fixture syntax

Validate at least:

```text
skills/repo-agent-native/evals/evals.json
skills/repo-agent-native/evals/fixtures/module-routing-cases.json
skills/repo-agent-native/evals/fixtures/scenarios.json
skills/repo-agent-native/evals/fixtures/trigger-cases.json
```

JSON syntax-only success is not a substitute for `selftest.ts`.

## Evidence states

```text
workflow file absent                  NOT_IMPLEMENTED
workflow exists, candidate still Draft NOT_EXERCISED
runner not allocated                  NOT_EXERCISED
job allocated but test fails          FAIL
job executes exact head and passes     PASS for structural/output contract only
```

Never reinterpret `NOT_EXERCISED` as PASS.

## Boundary to Phase 3

This owning workflow does **not** establish:

- better Claude Code output;
- better Codex CLI output;
- provider search/graph/memory quality;
- cross-harness generalization;
- capability unlock;
- canonical release admission.

Those belong to Phase 3 #95 and final release #88.
