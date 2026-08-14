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
`spatial-loop-systems-engineering`. The candidate adds a portable pre-implementation
system contract, a copyable System / Spec Prompt, a trigger-loaded Linux isolation
module, a deterministic contract checker, positive/hollow/mutation controls, and
an actual Skill Suites CI arrival.

This leaf does not implement or certify a sandbox. Live root, KVM, cgroup,
seccomp, hardware-performance, chaos, exploit, and sandbox-escape execution
remain `NOT_EXERCISED`; security acceptance, production promotion, permission
widening, merge, and rollback remain Human/trusted-operator boundaries. Exact
branch, PR head, and workflow state are read from GitHub metadata.

## Current evidence boundary

- Procedural/domain documentation separation: documented in this branch.
- A mechanical cross-repository route checker: `NOT_IMPLEMENTED` unless a separate issue/PR provides it.
- GitHub/Forgejo equivalence, live providers, browser/device sessions, model runs, and production promotion: environment-owned and not implied here.

For the mutable Skill Eval/Evolution status, read [`docs/AGENT_INTEGRATION_STATE.md`](docs/AGENT_INTEGRATION_STATE.md).
