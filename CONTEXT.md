# CONTEXT.md — current cross-repository handoff

`skills-shared` is the **Instruction / Method Plane** in a four-repository modular system:

```text
skills-shared
  portable procedures, Skill contracts, eval/evolution truth
        |
        v
runtime-env
  secret-free variables/modules/profiles/workloads/policies
        |
        v
bettor-arena
  module composition, proof kernel, stateless MCP, project bootstrap, acceptance
        |
        v
agent-shield-monorepo
  domain product modules and reference-consumer canaries
```

The arrows describe contract consumption, not mutable checkout imports. Local symlinks are development projections; immutable releases, bindings, locks, digests, and receipts are reproducible identities.

## Current routing task

The canonical same-name routes and assertions are defined in [`docs/architecture/DOCUMENT_ROUTING.md`](docs/architecture/DOCUMENT_ROUTING.md). Repository-specific bindings belong in each repository's same-name documents and nearest directory READMEs.

## Current candidate leaf

Issue `#128` owns the independent terminal leaf for
`spatial-loop-systems-engineering`; Draft PR `#136` is its publication subject.
The candidate adds a portable pre-implementation
system contract, a copyable System / Spec Prompt, a trigger-loaded Linux isolation
module, a deterministic contract checker, positive/hollow/mutation controls, and
a declared, executable Skill Suites CI arrival.

This leaf does not implement or certify a sandbox. Live root, KVM, cgroup,
seccomp, hardware-performance, chaos, exploit, and sandbox-escape execution
remain `NOT_EXERCISED`; security acceptance, production promotion, permission
widening, merge, and rollback remain Human/trusted-operator boundaries. Exact
branch, PR head, and workflow state are read from GitHub metadata.

## Controlled-language convergence state

CTL 01–06B are merged here and CTL 08 (`#133`) has recorded what is admitted: the
merged subjects with their trees, the immutable selected bundle
(`b3d47948…`, CTL 06B) and its distinct rollback subject (`47cbb259…`, CTL 06), the
routes, and the preconditions that are still unmet. The record is in
[`docs/architecture/CONTROLLED_TECHNICAL_LANGUAGE_HARNESS.md`](docs/architecture/CONTROLLED_TECHNICAL_LANGUAGE_HARNESS.md).

CTL 08 is not admitted. Consumer projection digests for Claude and Codex are
`NOT_IMPLEMENTED` and the paired physical carrier canaries are `NOT_EXERCISED`;
both belong to `ed3c/bettor-arena#83` and its open leaf `#108`, and a convergence
leaf may not repair them.

## Current evidence boundary

- Procedural/domain documentation separation: documented in this branch.
- A mechanical cross-repository route checker: `NOT_IMPLEMENTED` unless a separate issue/PR provides it.
- GitHub/Forgejo equivalence, live providers, browser/device sessions, model runs, and production promotion: environment-owned and not implied here.

For the mutable Skill Eval/Evolution status, read [`docs/AGENT_INTEGRATION_STATE.md`](docs/AGENT_INTEGRATION_STATE.md).

## Host measurements (not portable law)

- On 2026-08-14, local Codex CLI `0.146.0` was observed to accept
  `codex app <workspace-path>`. This is a dated host measurement; the permanent
  interface claim remains anchored to the official CLI documentation.
- The local `agy models` inventory was observed to contain the alias
  `gemini-3.7-flash-high`. Google documents the underlying
  `gemini-3.7-flash` model and its `high` thinking level; the hyphenated agy alias
  is local adapter state, not a Google model ID. It is a cross-model review lane,
  not external-claim authority. See the official
  [Gemini 3.7 Flash guide](https://ai.google.dev/gemini-api/docs/latest-model?hl=en).
