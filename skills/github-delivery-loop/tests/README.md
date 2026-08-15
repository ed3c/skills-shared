# `github-delivery-loop/tests/`

This directory proves that the shared delivery mechanisms can turn red. A green test suite is meaningful only when positive controls reach the intended public entrypoint and hollow/mutation controls fail for the intended reason.

## Harness index

| Directory | Mechanism | Load-bearing assertion |
|---|---|---|
| [`check-receipt/`](check-receipt/) | delivery-line check | missing artifact is `UNMATERIALIZED`, not skip |
| [`evidence-producers/`](evidence-producers/) | local verification and GitHub snapshot producers | exact HEAD, fixed argv, safe env, one PR, exact check, billing classification |
| [`ci-publish-gate/`](ci-publish-gate/) | Actions publication admission | only three intents; stale SHA, repeated draft, reused feedback and billing circuit block |
| [`merge-gate/`](merge-gate/) | merge authority | owner identity, admit freshness, host policy, and no-admit absence remain separate |
| [`install-codex-merge-rule/`](install-codex-merge-rule/) | narrow Codex execpolicy bootstrap | unsafe repository target is refused |
| [`link-canonical/`](link-canonical/) | canonical projection | diverged copy is preserved and refused |
| [`reference-causality/`](reference-causality/) | source/evidence causality | reference-only or stale evidence cannot promote |
| [`reference-causality-integration/`](reference-causality-integration/) | real-path causality wiring | eval target reaches the live implementation path |
| [`run-all.sh`](run-all.sh) | aggregate local harness | every discovered `verify.sh` must pass |

The machine-readable inventory is [`../evals.json`](../evals.json).

## Eval pattern

Each behavior family should include:

```text
good fixture
→ public checker/entrypoint
→ expected PASS/ALLOW state

hollow or mutation fixture
→ same public checker/entrypoint
→ expected FAIL/BLOCK state and stable reason
```

A test that only imports a helper may prove a helper, but not the public wiring.

## Evidence categories

### Positive control

Shows the admitted subject can reach the expected terminal state.

### Hollow control

Removes a required artifact, receipt, identity, check, or permission and proves the mechanism fails closed.

### Mutation control

Changes a load-bearing guard and proves the suite turns red. Mutation coverage is about assertions, not only execution coverage.

### Integration control

Reaches the actual public script path, file layout, and data contract used by consumers.

## Current eval map

| Eval | Positive | Negative |
|---|---|---|
| `DELIVERY-1` | complete local artifact/receipt/publication | absent artifact |
| `DELIVERY-2` | narrow repo-scoped Codex merge rule | unsafe target |
| `DELIVERY-3` | owner-admitted exact head and green preflight | forged owner, stale admit, blocking hook, no-admit absence |
| `DELIVERY-4` | identical copy converts to canonical link | diverged copy and self-link refused |
| `DELIVERY-5` | exact-HEAD local verification + admitted publication intent | stale receipt, repeated draft, old check SHA, consumed feedback, billing-open/stale recovery |
| evidence producers | admitted absolute `gh` identity, one workflow/run/job/check identity, raw-transport-derived observation | `PATH`/CLI fake provider executable, rerun/ambiguous check, tampered transport, shell strings, unsafe env, multiple PRs, malformed billing |
| reference causality | implementation-bound evidence | source citation or old evidence used as promotion proof |

## State semantics in tests

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
```

Examples:

- Draft PR job intentionally not requested: `SKIPPED_BY_POLICY`.
- Billing/spending prevented runner allocation: repository tests `NOT_EXERCISED`.
- Missing artifact: `FAIL` / `UNMATERIALIZED` in the delivery-line verifier.
- Missing live provider implementation: `NOT_IMPLEMENTED`.

Tests must assert the intended class rather than only a non-zero exit.

## Running tests

```bash
bash run-all.sh
```

Focused examples:

```bash
bash ci-publish-gate/verify.sh
bash evidence-producers/verify.sh
bash merge-gate/verify.sh
bash reference-causality-integration/verify.sh
```

All focused tests must be zero-network unless their directory explicitly declares a trusted integration lane. Fixtures must not contain live credentials or machine-specific paths.

## Adding a test family

1. Add the behavior claim to [`../evals.json`](../evals.json).
2. Create one directory with `verify.sh` and self-contained fixtures.
3. Reach the public entrypoint, not only an internal helper.
4. Add a good control.
5. Add at least one hollow or mutation control.
6. Assert the stable terminal state/reason.
7. Keep cleanup bounded and verify no residue.
8. Update [`../modules/state-machines.md`](../modules/state-machines.md) and [`../modules/traceability-index.md`](../modules/traceability-index.md).
9. Record the issue, PR parent/sibling relation, and terminal leaf.

## Forbidden shortcuts

- Network calls in ordinary fixture tests.
- Placeholder URLs or short SHAs.
- A negative command whose failure is hidden by shell control-flow semantics.
- Grepping unrelated output that can satisfy the assertion accidentally.
- Treating skipped, absent, or no-runner states as green execution.
- Using a source document or README as the only proof that executable wiring exists.
