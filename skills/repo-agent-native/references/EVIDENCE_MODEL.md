# Evidence Model

## Core law

Every code fact written by `repo-agent-native` must include a valid source anchor. Search, graph, LSP, and memory systems can discover or explain candidates; they cannot replace source read-back or the appropriate runtime control.

## Evidence levels

| Level | Meaning | Minimum requirement |
|---|---|---|
| `A` | direct implementation evidence | current source body read at recorded path/range and source identity |
| `A-` | structured static evidence | compiler/LSP/AST relation plus source read-back at declaration/call site |
| `B+` | indexed candidate evidence | semantic or graph hit with index/graph identity; not a final fact until read-back |
| `B` | declared contract or official repository document | machine contract, schema, README, ADR, or test declaration; implementation still checked |
| `C` | explicit inference | premises and counterfactual stated; never presented as direct fact |
| `D` | unsupported hypothesis | excluded from accepted output; may appear only in an open-questions section |

A result may be downgraded when the index, graph, memory, route, source identity, or line range is stale or incomplete.

## Source reference

Each accepted fact records:

```text
repository identity
observed commit/tree when available
repository-relative path
start line and end line
content/blob digest when available
symbol or structural subject when available
verification lane
```

A line range outside the current file, a missing path, an owner-checkout path used for an immutable bundle, or a source digest mismatch fails the assertion.

## Fact classes

```text
message invariant
state invariant
API contract invariant
effect invariant
negative invariant
implicit dependency
failure/timeout chain
open question
```

## Negative invariants

A negative invariant is not established by one failed search. It requires a declared bounded scope and at least two independent retrieval/read strategies when practical.

Example:

```text
claim: the selected public port does not accept an arbitrary output path
scope: loopctl contract + adapter + schemas
lanes: contract read + source search + negative fixture
state: PASS only when the bounded scope is complete
```

When absence cannot be proven, write `NOT_EXERCISED`, `ABSENT`, or an open question instead of a negative fact.

## Tool authority

```text
mem0 memory                context candidate only
semantic search            candidate discovery
knowledge graph            relationship candidate
LSP/AST/compiler            structured static evidence
source body                 implementation evidence
tests/public-port control   behavioral evidence
production receipt          environment-specific evidence
```

Tool agreement does not create truth when all tools share the same stale source. Tool contradiction requires source read-back and an explicit warning.

## Evidence states

```text
PASS               current subject satisfied its owning assertion
FAIL               current subject was exercised and rejected
ABSENT             required subject/input does not exist
NOT_IMPLEMENTED    required mechanism does not exist
NOT_EXERCISED      mechanism exists but current subject was not run
SKIPPED_BY_POLICY  admitted policy intentionally omitted execution
```

## Memory boundary

Memory may store user preferences, project decisions, prior incidents, and task summaries only when namespace, provenance, timestamp, privacy class, and conflict behavior are explicit. Memory never stores secrets or silently overrides repository documents, source code, current issue/PR state, or receipts.

A recalled decision must be checked against current `ARCHITECTURE.md`, ADRs, current-state documents, and source before affecting accepted output.
