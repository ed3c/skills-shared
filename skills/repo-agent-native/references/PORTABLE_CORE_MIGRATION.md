# repo-agent-native Portable Core Migration Map

> This document records how the Phase-2 portable core was derived and how the active module surface evolves. It is an implementation map, not runtime authority, and it does not activate a provider by itself.

## Source candidates and authority

Historical PR #87 contains a useful but superseded portable-core candidate at exact head `9d1106dfe48b9f72654375ca691f847ec830343e`. The contract-first stack superseded it. Do not merge or cherry-pick #87 wholesale.

The semantic-port rule is:

```text
historical procedure ideas
+ current evidence/output/routing contracts
+ trigger-selected capability modules
→ canonical portable SKILL.md + executable assertions
```

Authority during any port:

1. Current `main` and the exact implementation issue/PR.
2. `references/EVIDENCE_MODEL.md`.
3. `references/OUTPUT_CONTRACT.md`.
4. `references/TOOL_ROUTING.md`.
5. `references/DOCUMENT_ROUTES.md` and host compatibility.
6. Current modules and executable routing fixtures.
7. Historical wording only as a candidate.

When historical text conflicts with a current contract, the current contract wins.

## Procedure sections retained semantically

| Historical concept | Current destination | Current constraint |
|---|---|---|
| `SCOPE` | core state machine | exact subject/scope identity |
| `ROUTE` | core + document routes | repository documents, not machine memory |
| `DISCOVER` | core | Tier-0 exact discovery remains available |
| `RETRIEVE` | core dispatch | provider detail stays in trigger-selected modules |
| `VERIFY` | core + evidence model | source read-back and evidence ceilings |
| `INFER` | core + extraction method | inference remains separate from direct fact |
| `WRITE` | core + output contract | subject-bound invariant report |
| `ASSERT` | core + deterministic scripts | verifier owns hard assertions |
| `HANDOFF` | core | explicit non-success states and Human Admit |
| negative boundary | core/evidence reference | one empty search never proves absence |
| candidate != fact | core law | applies to search, index, AST, projection and memory |
| bounded repair | core | retry count is explicit; no retry-until-pass |

## Active module surface

The active capability modules are:

```text
modules/grepai.md
modules/serena.md
modules/scip.md
modules/tree-sitter.md
modules/sqlite-code-index.md
modules/compiler-truth-context-funnel.md
modules/mem0.md
```

`code-graph-rag` was removed from the active required/routing set in issue #246. Historical references remain interpretable through `CODE_GRAPH_RAG_RETIREMENT.md`, but they do not activate a provider or create a compatibility requirement.

Stable host-neutral routing, evidence and output law belongs under `references/` rather than duplicate generic provider layers.

## Current context route

```text
core receives a fuzzy brownfield question
→ optional semantic search produces candidate seeds
→ current source read-back anchors them
→ SCIP / Serena / native LSP add subject-bound semantic candidates
→ Tree-sitter emits exact-byte ranges and skeletons
→ SQLite stores a rebuildable normalized projection
→ compiler-truth context funnel applies traversal/context budgets
→ core verifies, writes and asserts
```

The same source-authority law applies at every stage. SCIP coverage may be partial; Tree-sitter does not infer cross-file types; SQLite integrity is not semantic truth; composition never raises evidence.

## Historical executable contract

Do not revive `scripts/check_repo_agent_native.py` as canonical. The current implementation uses Bun + TypeScript while preserving these semantic checks:

- portable frontmatter allowlist;
- `name` matches directory;
- concise non-empty description;
- progressive-disclosure line budget;
- required core sections/state machine;
- repository-relative links stay inside the Skill root;
- no machine-local or consumer-specific durable state;
- required module contract completeness;
- routing fixtures are executable and mutation-sensitive;
- planted hollow mutations fail.

Historical consumer/provider state must not be copied into the portable package: branches, remotes, credentials, sessions, mutable provider health, dated receipts, local symlinks, or live carrier success claims remain consumer/runtime evidence.

## Core-to-module boundary

The portable core mentions capability slots and dispatch laws, not product manuals.

A module may specialize:

- trigger and non-trigger;
- producer/project/index/grammar/schema health;
- query/parse shape and budget;
- provider-specific failure vocabulary;
- deterministic fallback.

A module may not specialize:

- source-truth authority;
- evidence promotion;
- output hard-gate semantics;
- Human Admit;
- permission widening.

## Executable surfaces

```text
bun scripts/validate-skill.ts --skill-root <path> --json <receipt>
bun scripts/assert-output.ts --repo <repo> --report <report.json> --receipt <receipt.json>
bun tests/selftest.ts
```

`validate-skill.ts` verifies portable structure, module boundaries, active module inventory and routing controls without calling a network provider. `assert-output.ts` verifies exact subject/source references and evidence promotion. `selftest.ts` runs positive and planted mutations in disposable local fixtures.

Minimum module/routing mutation kills now include:

- missing SCIP, Tree-sitter, SQLite or composed-funnel module;
- unknown or retired routing target;
- stale SCIP subject;
- partial language coverage represented as completeness;
- Tree-sitter parse failure outside tolerance;
- SQLite subject mismatch;
- funnel promotion without source read-back;
- ambiguous primary route or attempted law override.

## Current Definition of Done

The compiler-truth migration leaf may leave Draft only when:

- Code-Graph-RAG is absent from required modules and positive routing;
- all active module contracts are complete;
- routing fixtures include positive and failure controls for the new lanes;
- the portable core still validates without any optional provider running;
- deterministic structural checks pass against the exact branch head;
- live grepai/Serena/SCIP/Tree-sitter/SQLite execution remains explicitly `NOT_EXERCISED` until consumer receipts exist;
- Human Admit retains provider activation, semantic conflict resolution, merge and release.
