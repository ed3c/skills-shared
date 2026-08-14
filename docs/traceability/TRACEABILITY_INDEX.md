# Traceability index — document routing

## Trace model

```text
source / incident
→ repository decision
→ parent issue
→ molecular issue
→ sibling or true-child PR
→ eval / negative control
→ immutable subject
→ receipt / current evidence state
→ Human Admit
```

## Four-repository documentation stack

| Plane | Issue | PR publication subject | Stack class | State | Merged commit |
|---|---|---|---|---|---|
| Parent integration contract | `ed3c/bettor-arena#35` | n/a | parent | open | n/a |
| Instruction / Method | `ed3c/skills-shared#84` | `ed3c/skills-shared#85` | independent sibling | Merged | `e3b327ad49c088f1962c33167ecd5ac9d28125fb` |
| Runtime Contract | `ed3c/runtime-env#29` | `ed3c/runtime-env#30` | independent sibling | Merged | `4a333ccf106ef60bc6942b922b7f5efffb3876f5` |
| Domain Product / Consumer | `ed3c/agent-shield-monorepo#77` | `ed3c/agent-shield-monorepo#78` | independent terminal sibling | Merged | `1af04c1ef5cb68eab198987feba008c93d3ec22f` |
| Integration / Acceptance | `ed3c/bettor-arena#36` | `ed3c/bettor-arena#37` | independent sibling | Merged | `1f94d3d77992a1396959a15b2ada7836c07bf300` |
| Exact merged index and cold-start audit | `ed3c/bettor-arena#38` | n/a | convergence leaf | Closed | n/a |

All four siblings have merged and the convergence owner `bettor-arena#38` is closed, so this stack is no longer pending work. The parent contract issue `bettor-arena#35` remains open and is the only live item on this plane.

The exact candidate head of an *open* PR is read from GitHub PR metadata rather than embedded in the same branch: self-embedding a commit SHA would make the document stale in the commit that updates it. Merged commits above are immutable and therefore safe to record.

The four implementation branches were siblings because each edited only its repository's documentation and consumed merged inputs. A serial stack would have added false dependencies.

## Intent-Bound Constraint stack

| Leaf | Issue | PR | Merged commit | Merged tree | Owning workflow at the admitted head |
|---|---|---|---|---|---|
| IBC 01 contract + closure evaluator | `#98` | `#104` | `fe660a990e9c66d364afd6519579048276ac7980` | `ea5e0a23ffc57b35039e8ffaf085f65d2bf3aa08` | `Skill Eval Contract` SUCCESS |
| IBC 02 Git Town Stack binding | `#99` | `#105` | `0f18b483d6f31cbfd59c887ef146833fa2186f77` | `1891f98129daacf3fa75401a69254eea00a49419` | **none — zero runs at that head** |
| IBC 03 knowledge-continuity adapter | `#100` | `#106` | `6d0c54f63cfa8aa7224d395095efe0cc5cf9b7e2` | `261b6aed0c7a92ab17a03b1a7595cc17736e290e` | **none — zero runs at that head** |
| IBC 04 forgejo-delivery-loop adapter | `#101` | `#111` | `9d937458178f0315220710f4cc356a4d6549e977` | `f6bed242309c9f9904d12f0a14b4eb0a2b4b37e0` | `Forgejo Delivery Loop Contract` SUCCESS |
| IBC 05 pinned live Git Town canary | `#102` | `#107` | `c8f4813b402095ed1d72060dcb81f1ac0edfc838` | `60b6425b568293b644057b6028b2955686b93586` | `Git Town Stacked PR Worker / live-canary` SUCCESS |

IBC 02 and IBC 03 merged with **no workflow run at their head commits at all**. That is an absence of evidence, not a pass, and it is recorded here rather than smoothed over. Its consequences and the repairs that followed are in [`../AGENT_INTEGRATION_STATE.md`](../AGENT_INTEGRATION_STATE.md).

## Spatial-loop systems engineering leaf

| Source | Issue | PR publication subject | Stack class | Publication state | Owning controls |
|---|---|---|---|---|---|
| User-supplied system-engineering proposal | `#128` | `#136` | independent terminal leaf | Open Draft; read exact live state from GitHub | local `tests/run-all.sh` PASS; GitHub jobs remain policy-gated while Draft |

The leaf binds the generalized method to `spatial-loop-system-contract/v1`, its deterministic checker, positive/hollow/mutation controls, the trigger-loaded Linux isolation module, and the Skill Suites arrival. The exact open-PR head and workflow state are read from GitHub rather than self-embedded here.

Live root, KVM, cgroup, seccomp, network-namespace, hardware-performance, chaos, exploit, and sandbox-escape execution remain `NOT_EXERCISED`. Destructive privileged testing, security acceptance, production promotion, permission widening, merge, and rollback remain Human/trusted-operator boundaries.

## Method lineage

- `knowledge-continuity` supplies the rule that every hop leaves an in-place summary and evidence is not hidden behind unexplained redirects.
- `github-delivery-loop` supplies issue/PR/receipt and publication-state separation.
- `forgejo-delivery-loop` supplies local authoring, deterministic routing/outbox/recovery, and receipt separation.
- `git-town-stacked-pr-worker` supplies sibling/true-child/terminal/convergence branch semantics and Human boundaries.
- `spatial-loop-systems-engineering` supplies exact-subject state-space, capability, invariant, teardown, performance, and implementation-gate contracts for substrate-bound work.

## Evidence boundary

PR presence and exact GitHub head metadata prove publication identity only. Documentation completion does not imply route-checker execution, fresh Claude/Codex cold-start, GitHub/Forgejo equivalence, live provider canaries, capability unlock, release promotion, or production readiness.
