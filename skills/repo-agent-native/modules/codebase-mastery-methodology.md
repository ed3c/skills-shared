# Codebase mastery methodology

## Trigger

Use for high-risk, family-wide, security-sensitive, or public-interface changes where a normal invariant pass is not enough and formal architecture/data-flow/security artifacts are justified.

## Non-trigger

Do not run by default for a local edit. Do not produce a second repository wiki or repeat existing authoritative architecture documents without a declared gap.

## Inputs

```text
confirmed invariant artifact
repository document route
public interfaces and module owners
source/test/runtime evidence available
spec output location from consumer binding
```

## Method

Apply a source-first funnel:

```text
question
→ authoritative documents and manifests
→ entrypoints/public interfaces
→ source bodies and tests
→ implicit-design probes
→ runtime evidence where required
→ specification artifact
```

Ask eight design probes:

1. **Seam** — where does ownership or public/private boundary change?
2. **Determinism** — which transitions are deterministic, stochastic, external, or human-admitted?
3. **Platform** — which OS, language, runtime, filesystem, network, or provider assumptions exist?
4. **Bounded loop** — what stops iteration, retry, recursion, queue growth, or background work?
5. **Trust** — which inputs, callers, artifacts, credentials, and receipts are trusted or untrusted?
6. **Ergonomics** — who calls the interface, with what packet, exit, artifact, and recovery path?
7. **Typed errors** — how are absence, failure, retryability, partial apply, and cleanup represented?
8. **Framework idiom** — which framework conventions are load-bearing and which are accidental implementation detail?

Each answer must cite source or remain explicitly inferred.

## Outputs

When the consumer requests specs-as-code, produce no more than the needed artifacts, commonly:

```text
architecture-map.md
  owners, seams, public interfaces, capabilities, trust boundaries

data-flow-and-api.md
  typed inputs/outputs/effects/exits, state transitions, dependency flow

security-and-bottlenecks.md
  attack surfaces, failure chains, limits, cleanup, observability, unresolved evidence
```

The repository binding decides whether these are plan-scoped or durable domain documents. Durable-law promotion requires Human Admit.

## Evidence ceiling

A static architecture map can establish declared/source structure. It cannot establish current performance, provider availability, production behavior, or security effectiveness without current execution evidence.

## Fallback

Return to the core invariant artifact and name the missing evidence. Do not fill a formal spec with generalized best practices or vendor claims that were not observed in the subject.

## Authoritative laws

The Core laws in [`../SKILL.md`](../SKILL.md) remain authoritative. This module deepens analysis but does not change evidence levels or promotion authority.
