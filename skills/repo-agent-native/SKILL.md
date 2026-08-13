---
name: repo-agent-native
description: Extract source-anchored repository invariants, negative assumptions, implicit dependencies, and impact boundaries before planning or changing a brownfield codebase. Use for reliable contract recovery, impact analysis, or source-grounded specs. Do not use as a general wiki, runtime debugger, or external product-claim verifier.
license: MIT
compatibility: Codex CLI, Claude Code, and Agent Skills-compatible coding agents with repository read/search access; optional capabilities may accelerate retrieval but are never evidence authorities.
metadata:
  version: "2.0.0"
  procedure: "source-anchored-repository-analysis"
---

# repo-agent-native

Recover the smallest source-grounded model needed to change a repository safely. This is a host-neutral procedure, not a provider configuration, memory store, graph database, repository wiki, or consumer runbook.

## Trigger

Use for brownfield work that must recover source-backed invariants, rejected assumptions, implicit dependencies, routing/state contracts, or cross-module impact before planning or editing.

## Non-trigger

Do not use as the primary workflow for broad onboarding, runtime-only debugging, external product claims, or implementation whose scope and public contract are already established. Never treat remembered decisions, retrieval hits, symbol results, or graph edges as current source truth.

## Inputs

Require a bounded subject, immutable identity when available, question, included/excluded scope, repository-approved output location, required document routes, capability/budget policy, and Human Admit boundary. Missing required input is `ABSENT`; do not infer it from chat history or a machine-local path.

## Outputs

Produce a subject-bound analysis containing confirmed claims with source references, bounded negative claims, known facts separated from inference, verified/unverified impact edges, routes and capabilities observed, unresolved evidence, assertion results, and the Human Admit/rollback boundary. Follow [OUTPUT_CONTRACT.md](references/OUTPUT_CONTRACT.md); the caller owns the concrete output path.

## Core laws

1. Read relevant current source before promoting a candidate to a fact.
2. Search, semantic, symbol, graph, generated, and memory results are candidates until required readback.
3. Every confirmed source claim carries a repository-relative source reference and subject identity.
4. Absence requires a declared search boundary and counterexample sought.
5. Keep declaration, mechanism, observed execution, attribution, and Human Admit distinct.
6. Record capability identity, health/freshness, evidence ceiling, and deterministic fallback; never substitute silently.
7. The Agent may propose analysis, edits, and evidence; it may not self-admit durable law, permission widening, publication, or merge.

## State machine

```text
S0 SCOPE → S1 ROUTE → S2 DISCOVER → S3 RETRIEVE → S4 VERIFY
→ S5 INFER → S6 WRITE → S7 ASSERT → S8 HANDOFF
```

Stop states are data, not prose: `SUBJECT_ABSENT`, `SUBJECT_IDENTITY_MUTABLE`, `SCOPE_AMBIGUOUS`, `REQUIRED_ROUTE_ABSENT`, `CAPABILITY_UNHEALTHY`, `SOURCE_UNREADABLE`, `SOURCE_REFERENCE_MISSING`, `ABSENCE_BOUNDARY_UNDECLARED`, `EVIDENCE_CEILING_EXCEEDED`, `MEMORY_CONFLICT`, `IMPACT_EDGE_UNVERIFIED`, `OUTPUT_COLLISION`, `ASSERTION_FAILED`, `BUDGET_EXHAUSTED`, and `HUMAN_ADMIT_REQUIRED`.

## S0 — Scope

- Resolve one admitted repository/subtree without escaping through an untrusted symlink.
- Record immutable commit/tree when available, question, scope/exclusions, output contract, and affected public boundary.
- Stop on materially different plausible subjects; do not select one silently.

## S1 — Route

- Apply the repository's own document inheritance before searching source.
- Read only the smallest route needed for the task; record required routes that are absent.
- Load [DOCUMENT_ROUTES.md](references/DOCUMENT_ROUTES.md) for repository instructions, context maps, ADRs, nearest-README inheritance, or multi-hop routing. These documents guide discovery but are not Skill discovery formats.

## S2 — Discover

- Start with repository-owned deterministic discovery: tracked files, exact/regex search, direct reads, and version-control identity.
- Identify implementation, tests, manifests, generated/vendor boundaries, effects, exits, configuration keys, and public interfaces.
- Record each candidate's origin, subject/freshness, why it matters, and next readback action.

## S3 — Retrieve

- Read [modules/README.md](modules/README.md), then load only modules whose triggers match the needed capability.
- Verify provider/project identity, health, freshness, scope, privacy/effect boundary, and fallback before use.
- Keep the zero-index route available when every optional provider is absent; provider presence never raises evidence by itself.

## S4 — Verify

- Apply [EVIDENCE_MODEL.md](references/EVIDENCE_MODEL.md) to every proposed claim.
- Read implementation bodies, capture source references, and name a falsifier or negative control.
- Downgrade conflicts, stale candidates, or relations not reproducible from the recorded subject.
- Never infer absence from one empty retrieval result.

## S5 — Infer

- Load [extraction-methodology.md](modules/extraction-methodology.md) only for implicit dependencies, optional-parameter branch exhaustion, failure chains, or bounded negative claims.
- Keep known facts and inferred prerequisites in separate fields; inference never silently becomes a confirmed invariant.
- Verify impact edges through current source, interfaces, manifests, tests, or subject-bound execution; otherwise emit `IMPACT_EDGE_UNVERIFIED`.
- Load deeper analysis/output modules only when their explicit trigger matches.

## S6 — Write

- Emit one claim per stable ID with evidence level, source references, verification, and unresolved state.
- Preserve subject, scope, routes, exclusions, provider observations, and fallback in the artifact.
- Empty factual output is not success: return the candidate ledger plus a named stop state.
- Never hard-code a consumer directory, branch, issue, provider endpoint, credential, session, or mutable receipt.

## S7 — Assert

- The host executes code; the Skill describes how. Use explicit executable/arguments, bounded inputs/effects, timeout, and subject-bound receipts—never raw model-generated shell strings.
- Treat deterministic structure/source/test assertions as hard only for their declared subject. Keep qualitative review advisory unless independently calibrated.
- Follow [scripts/README.md](scripts/README.md) and [OUTPUT_CONTRACT.md](references/OUTPUT_CONTRACT.md); preserve exit `0` accepted, `2` assertion failure, `64` invalid/absent input, and `70` mechanism error.
- On failure, repair and rerun the same assertion at most three times. Preserve errors, then stop and question the abstraction.

## S8 — Handoff

Report exact subject/scope, routes, claims and levels, absence boundaries, unresolved inferences/edges, capabilities and fallbacks, executed commands/exits/receipts, artifact identities, remaining evidence states, Human Admit, and rollback subject.

Do not claim model-output superiority from structure or one successful sample. Physical comparisons follow the preregistered contract in [evals/README.md](evals/README.md) and require hard-gate non-regression plus aggregate improvement.

## Module law

Modules are trigger-selected capability or domain instances. They may specialize inputs, examples, provider contracts, and fallbacks, but may not weaken Core laws, raise evidence ceilings, widen effects, or inject consumer state. Stable host-neutral contracts belong in `references/`; deterministic mechanisms in `scripts/` and `tests/`; consumer bindings and live state stay outside this package.

For placement/change rules read [modules/README.md](modules/README.md). Audit-only preservation lives in [canonical-terms.md](modules/canonical-terms.md), [semantic-loss-ledger.md](modules/semantic-loss-ledger.md), and the immutable [baseline.json](evals/baseline.json).
