# ARCHITECTURE.md — skills-shared

## Role

`skills-shared` is the canonical Instruction / Method Plane. It owns portable Skill behavior and the truth-gated evaluation/evolution contracts for those Skills. It does not own product implementations, runtime secrets, consumer branch graphs, or live provider receipts.

## Planes

```text
Canonical Skill Plane
  registry.json + skills/<name>/SKILL.md

Method Support Plane
  references/ + modules/ + scripts/ + tests/ + evals.json

Skill Eval / Evolution Plane
  evals/ + mutations/ + deterministic verifiers + capability/release ledgers

Document Routing Plane
  root routes + docs/INDEX.md + nearest README contracts
```

## Skill structure invariant

```text
SKILL.md      procedural workflow/method/laws
references/   reusable generic contracts/templates
modules/      domain instances loaded on demand
scripts/      executable mechanisms
tests/        falsifiable controls
evals.json    machine eval inventory
README.md     navigation and local ownership
```

A `modules/` example may explain how a method applies to a domain, but it cannot silently become universal passive context. A consumer binding may select a module; the core Skill stays portable.

## Cross-repository contract

- `skills-shared` publishes instructions and method contracts.
- `runtime-env` publishes secret-free runtime contracts.
- `bettor-arena` resolves selected Skill/runtime/module closures and executes acceptance Harnesses.
- `agent-shield-monorepo` consumes immutable releases as a domain reference consumer.

See [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md).

## Evidence invariant

Documentation, source proposals, registry presence, and package metadata are claims. Capability truth requires the owning verifier, exact subject, negative controls, and receipts. `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, and `SKIPPED_BY_POLICY` remain distinct.
