# Four-repository modular integration

## Ownership planes

| Repository | Plane | Owns | Must not own |
|---|---|---|---|
| `skills-shared` | Instruction / Method | portable procedures, generic contracts, Skill eval/evolution truth | consumer branches, secrets, product providers |
| `runtime-env` | Runtime Contract | secret-free variables, modules, profiles, workloads, policies, requirements/bindings | secret values, arbitrary shell, product semantics |
| `bettor-arena` | Integration / Acceptance | module composition, proof/control/mutation, stateless MCP, project bootstrap, external-release acceptance | domain product implementation, hidden live checkout dependencies |
| `agent-shield-monorepo` | Domain Product / Reference Consumer | product modules, provider adapters, product state machines, consumer canaries | canonical shared Skill bodies, generic runtime catalog |

## Contract flow

```text
skills-shared immutable Skill release
        |
        v
consumer Skill requirements / binding
        |
runtime-env requirements → resolved secret-free runtime binding
        |                         |
        +------------+------------+
                     v
bettor-arena composition + module/Skill/runtime locks
                     |
                     v
immutable bettor CLI/MCP/bootstrap release
                     |
                     v
agent-shield-monorepo remote-consumer or embedded-module initialization
                     |
                     v
Claude/Codex/provider/origin/product canary receipts
                     |
                     v
bettor external-release acceptance + Human promotion
```

## Development versus release channels

```text
local Skill symlink / editable checkout
  = development projection

immutable commit/tree/release manifest + binding/lock
  = reproducible identity

CLI / stateless MCP
  = public consumption surface
```

Forgejo may be a local authoring origin and GitHub a cloud distribution origin, but equivalence requires an exact commit, tree, or release-manifest receipt. No repository falls back silently to mutable `main`.

## Source-proposal boundary

The attached architecture document proposes E2B/Firecracker, OpenShell/tmux, Mutagen, mobile automation, wallet/security, costs, licenses, and repair. These are candidate domain/provider modules, not shared-method or current-state facts. Each requires independent verification, implementation, evals, canaries, and Human Admit.
