---
name: repo-agent-native
description: Extract source-anchored repository invariants, negative assumptions, implicit dependencies, and impact boundaries before planning or changing a brownfield codebase. Use when a task requires reliable codebase understanding, contract recovery, impact analysis, or source-grounded specs. Do not use as a general repository wiki, a runtime debugger, or an external product-claim verifier.
license: MIT
compatibility: Codex CLI, Claude Code, and Agent Skills-compatible coding agents with repository read/search access; optional shell or MCP capabilities may accelerate retrieval but are never evidence authorities.
metadata:
  version: "2.0.0"
  short-description: "Extract source-anchored repository invariants"
  procedure: "source-anchored-repository-analysis"
---

# repo-agent-native

Recover the smallest source-grounded model needed to change a repository safely. The Skill is a procedure, not a search product, memory store, graph database, or repository-specific runbook.

## Trigger

Use this Skill when the task asks to:

- extract business, state, message, or API invariants from an existing codebase;
- identify negative invariants: assumptions the source explicitly rejects or does not implement;
- recover implicit dependencies, routing keys, shared-state coupling, timeout chains, or silent-failure paths;
- estimate cross-module impact before a refactor;
- produce source-grounded architecture, data-flow, or security specifications;
- prepare a brownfield implementation plan whose claims must be traceable to source.

## Non-trigger

Do not use this Skill as the primary method for:

- a broad repository wiki or onboarding summary with no source-anchoring requirement;
- runtime-only debugging where the failure cannot be established from source and current execution evidence;
- checking external product, pricing, license, version, or provider claims;
- editing code before the task scope, ownership, and public contract are identified;
- treating remembered decisions, semantic matches, or graph edges as current repository truth.

## Inputs

The caller or repository binding supplies:

```text
subject_root          repository or bounded subtree
subject_identity      immutable commit/tree when available
question              contract, invariant, or impact question
output_root           repository-approved artifact location
scope                  included and excluded paths
required_routes       documents that must be read before source exploration
capability_binding    available retrieval/symbol/graph/memory capabilities
budgets               time, tool-call, token, output, and network limits
human_boundary        decisions the Agent may not admit
```

A missing required input is `ABSENT`; do not guess it from chat history or a machine-local path.

## Outputs

Produce a structured analysis artifact with:

```text
subject identity and scope
routes read and routes missing
invariants with evidence level and source references
negative invariants and absence-search boundary
implicit dependencies with known facts separated from inference
impact edges with verification state
provider observations and fallbacks used
unresolved questions and evidence needed
assertion results
Human Admit and rollback boundary
```

Use the repository binding for the exact output path. The shared procedure never fixes a consumer directory, branch, or issue number.

## Core laws

1. **Source bytes are the primary authority for source claims.** Read the relevant body before promoting a candidate to a fact.
2. **Candidates are not facts.** Text search, semantic retrieval, symbol indexes, graph edges, generated summaries, and memories only nominate places to inspect.
3. **Every confirmed source claim has a source reference.** Prefer repository-relative `path:line-range` plus immutable subject identity.
4. **Absence requires a declared search boundary.** An empty semantic or graph result never proves that behavior is absent.
5. **Observation and attribution are different.** Runtime evidence may establish that an event occurred; source and controlled experiments are needed to attribute cause.
6. **Memory is advisory.** A remembered preference, incident, or decision must be checked against current documents, source, tests, or receipts before use.
7. **No silent capability substitution.** Record provider health, evidence ceiling, and fallback whenever a preferred capability is unavailable or stale.
8. **No authority collapse.** Documentation, source, manifests, tests, runtime receipts, and Human Admit remain distinct authorities.
9. **No self-admission.** The Agent may produce a candidate analysis; it may not merge, promote, widen permissions, or rewrite durable law without the declared Human Admit.

## State machine

```text
S0 SCOPE
→ S1 ROUTE
→ S2 DISCOVER
→ S3 RETRIEVE
→ S4 VERIFY
→ S5 INFER
→ S6 WRITE
→ S7 ASSERT
→ S8 HANDOFF
```

Failure states are explicit:

```text
SUBJECT_ABSENT
SUBJECT_IDENTITY_MUTABLE
SCOPE_AMBIGUOUS
REQUIRED_ROUTE_ABSENT
CAPABILITY_UNHEALTHY
SOURCE_UNREADABLE
SOURCE_REFERENCE_MISSING
ABSENCE_BOUNDARY_UNDECLARED
EVIDENCE_CEILING_EXCEEDED
MEMORY_CONFLICT
IMPACT_EDGE_UNVERIFIED
OUTPUT_COLLISION
ASSERTION_FAILED
BUDGET_EXHAUSTED
HUMAN_ADMIT_REQUIRED
```

## S0 — Scope

1. Resolve the repository root or bounded subtree without following an untrusted symlink outside the admitted subject.
2. Capture an immutable commit or tree identity when the environment can provide one.
3. Name the question, included paths, excluded paths, generated/vendor boundaries, and output location.
4. List the public interface, module owner, or state transition that the task may change.
5. Stop with `SCOPE_AMBIGUOUS` when two plausible subjects would produce materially different answers.

## S1 — Route

Read the smallest authoritative document route before searching source. Apply the repository's routing contract; when present, the recommended route is:

```text
README.md
→ AGENTS.md or host entrypoint
→ ARCHITECTURE.md
→ CONTEXT.md or CONTEXT-MAP.md
→ docs/README.md
→ docs/agents/domain.md
→ relevant ADRs
→ nearest directory README.md
→ machine contract, tests, and current receipts
→ exact issue and PR
```

Read [DOCUMENT_ROUTES.md](references/DOCUMENT_ROUTES.md) when the repository exposes domain context, ADRs, nearest-README inheritance, or a multi-context map.

A route may be optional only when the repository contract says so. A task packet that requires a missing route produces `REQUIRED_ROUTE_ABSENT`.

## S2 — Discover

Begin with deterministic, zero-index discovery:

1. list files inside the admitted scope;
2. use exact text or regular-expression search for entrypoints, interfaces, state names, configuration keys, effects, exits, and tests;
3. inspect version control history only when lineage matters to the question;
4. identify generated, vendor, fixture, and evidence paths before treating matches as implementation.

Discovery creates a candidate ledger. Each candidate records:

```text
candidate id
query or trigger
candidate path/symbol
provider or command
provider subject/freshness when applicable
reason it may answer the question
next readback action
```

## S3 — Retrieve

Select optional modules only when their trigger matches:

| Need | Module | Evidence ceiling before readback |
|---|---|---|
| meaning-based code candidates | [grepai.md](modules/grepai.md) | candidate |
| symbol definitions, references, diagnostics, or safe edit planning | [serena.md](modules/serena.md) | symbol candidate |
| cross-module or cross-language dependency candidates | [code-graph-rag.md](modules/code-graph-rag.md) | graph candidate |
| prior decisions, preferences, incidents, or session continuity | [mem0.md](modules/mem0.md) | memory hint |

The zero-index path remains available even when every optional provider is absent:

```text
file listing + exact search + direct source read + version-control identity
```

Provider selection is capability-based. A consumer binding may name a concrete provider, version, command, transport, and policy; the shared body does not require one product.

## S4 — Verify

### Evidence levels

| Level | Meaning | Promotion rule |
|---|---|---|
| `A` | relevant source body read at the recorded subject | may confirm a source claim |
| `A-` | symbol/reference path established and relevant source bodies read back | may confirm only the traced relation |
| `B+` | semantic, graph, generated, or index candidate not fully read back | candidate only |
| `B` | repository documentation, manifest, interface declaration, or test intent | declaration only unless execution is observed |
| `C` | explicit inference from known facts | must remain labelled inference |
| `D` | unsupported assumption | must not enter the factual result |

For every proposed invariant:

1. read the relevant implementation body;
2. capture repository-relative source references;
3. distinguish declaration from mechanism and mechanism from execution;
4. identify the negative control or counterexample that could falsify the claim;
5. record the evidence ceiling when the claim cannot be confirmed.

### Negative invariants

A negative invariant must include:

```text
claim
search boundary
queries and paths inspected
counterexample sought
evidence level
confidence limitation
```

Do not write “does not exist” from one empty tool result.

## S5 — Infer

Load [extraction-methodology.md](modules/extraction-methodology.md) for implicit-dependency inference and optional-parameter branch exhaustion.

Inference begins only after known facts are separated from unknowns. For each implicit dependency record:

```text
callee or shared state
known source facts
inferred prerequisite
routing or temporal constraint
silent-failure or timeout chain
resolution state
next evidence required
```

Cross-module impact candidates from a graph or index remain `IMPACT_EDGE_UNVERIFIED` until source declarations, call sites, manifests, tests, or runtime evidence read back the edge.

For high-risk architecture work, load [codebase-mastery-methodology.md](modules/codebase-mastery-methodology.md). Use [specs-as-code-prompt.md](modules/specs-as-code-prompt.md) only as an output template; it does not grant new authority.

## S6 — Write

Write one claim per record. A recommended machine-readable artifact is:

```json
{
  "schema": "repo-agent-native/invariant-report/v2",
  "subject": {
    "repository": "owner/name-or-local-id",
    "observed_commit": "<40-hex-commit>",
    "observed_tree": null,
    "scope": ["repository-relative paths"],
    "task": "short task identity"
  },
  "routes": [],
  "tools": [],
  "facts": [],
  "negative_invariants": [],
  "implicit_dependencies": [],
  "open_questions": [],
  "named_exclusions": [],
  "state": "PASS"
}
```

A human-facing Markdown view may accompany the JSON, but it must preserve IDs, evidence levels, source references, unresolved states, and the exact subject identity.

Empty output is not success. When no invariant is confirmed, emit the attempted scope, candidate ledger, and a named failure state such as `SOURCE_UNREADABLE` or `BUDGET_EXHAUSTED`.

## S7 — Assert

A Skill does not execute code by itself. The host Agent invokes bundled scripts, repository commands, or admitted tools. Separate assertion classes:

| Assertion | Mechanism | Authority |
|---|---|---|
| structural Skill contract | bundled deterministic checker | hard gate for declared structure |
| repository-specific route/provider contract | consumer binding checker | hard gate for that consumer |
| source claim | source-reference verifier | hard gate for recorded source shape |
| runtime behavior | controlled test/canary and receipt | hard gate only for the executed subject |
| qualitative completeness | review checklist or judge | advisory unless independently calibrated |

Run the bundled assertions when changing this Skill. Commands use explicit inputs and produce subject-bound JSON receipts:

```bash
bun scripts/validate-skill.ts --skill-root . --json <skill-receipt.json>
bun scripts/assert-output.ts --repo <repo> --report <report.json> --receipt <output-receipt.json>
bun tests/selftest.ts
```

When invoked from another working directory, use the host-provided Skill directory variable or resolve the script relative to the loaded `SKILL.md`; do not assume a machine-local absolute path.

Exit `0` means the checker accepted its declared subject; `2` is an evaluated assertion failure, `64` is invalid/absent input, and `70` is an internal mechanism error. Never catch a failed assertion with `|| true`, rewrite `NOT_EXERCISED` as `PASS`, or keep retrying until a stochastic output happens to pass. Repair the same failure at most three times, preserve each error, then stop and question the abstraction.

## S8 — Handoff

Report:

```text
subject commit/tree and scope
routes read and routes absent
confirmed invariants and evidence levels
negative invariants and search boundaries
implicit dependencies and unresolved edges
providers used, health, evidence ceilings, and fallbacks
commands and assertions executed with exit states
output artifacts and digests when available
remaining ABSENT / NOT_IMPLEMENTED / NOT_EXERCISED
Human Admit and rollback subject
```

Physical A/B execution must compare `no_skill`, `current_skill`, `candidate_skill`, and `wrong_skill` in fresh workspaces with zero retries. A candidate is better only when every hard gate is no worse and the admitted aggregate metric improves. Static structure alone cannot establish model-output superiority.

## Module law

Modules provide domain instances or capability adapters. They may specialize triggers, inputs, examples, provider contracts, and fallbacks. They may not weaken the Core laws, raise an evidence ceiling, inject consumer secrets or paths, or turn an unavailable provider into a factual claim.

Read [modules/README.md](modules/README.md) before adding or changing a module.

Refactor preservation resources are audit-only unless their own trigger says otherwise:

- [modules/canonical-terms.md](modules/canonical-terms.md) defines domain terms that outputs must not silently rename;
- [modules/semantic-loss-ledger.md](modules/semantic-loss-ledger.md) maps every immutable baseline semantic range to its current durable home;
- [evals/baseline.json](evals/baseline.json) pins the exact pre-refactor Git commit, path, and blob for audit or rollback without copying consumer-bound legacy prose into the portable package.
