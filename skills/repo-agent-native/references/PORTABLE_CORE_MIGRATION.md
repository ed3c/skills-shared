# repo-agent-native v2 Portable Core Migration Map

> This document is an implementation map for Phase 2 (#92 / PR #93). It does not become runtime authority and does not activate the candidate `SKILL.md` by itself.

## Source candidates

Historical PR #87 contains a useful but superseded portable-core candidate at exact head `9d1106dfe48b9f72654375ca691f847ec830343e`. The active contract-first stack is #89 -> merged PR #91 -> active PR #93. Do not merge or cherry-pick #87 wholesale.

The migration rule is semantic porting:

```text
#87 procedure ideas
    +
#91 current contracts/references/evals
    +
#93 provider modules and routing controls
    ->
new canonical Phase-2 SKILL.md + Bun assertions
```

## Authority order during the port

1. Current `main` and PR #91 contracts.
2. `references/EVIDENCE_MODEL.md`.
3. `references/OUTPUT_CONTRACT.md`.
4. `references/TOOL_ROUTING.md`.
5. `references/DOCUMENT_ROUTES.md` and host compatibility contract.
6. Current #93 modules and module-routing fixtures.
7. Historical #87 text only as candidate wording/structure.

When #87 conflicts with a current contract, the current contract wins.

## Procedure sections to retain semantically

The following #87 concepts are still aligned and should be ported, not copied blindly:

| Historical concept | Phase-2 destination | Required current constraint |
|---|---|---|
| `SCOPE` | core State Machine | subject/scope identity must follow current output contract |
| `ROUTE` | core + `DOCUMENT_ROUTES.md` | repository routes are declared/current, not machine memory |
| `DISCOVER` | core | Tier-0 exact discovery remains mandatory fallback |
| `RETRIEVE` | core dispatch only | provider detail moves to trigger-selected modules |
| `VERIFY` | core + evidence model | source read-back/evidence ceiling vocabulary is current contract |
| `INFER` | core + extraction reference | inference must remain separate from direct fact |
| `WRITE` | core + output contract | emit `repo-agent-native/invariant-report/v2` compatible subject |
| `ASSERT` | core + Bun scripts | deterministic verifier owns hard structural/output assertions |
| `HANDOFF` | core | retain `ABSENT/NOT_IMPLEMENTED/NOT_EXERCISED` and Human Admit |
| negative invariant boundary | core/evidence reference | one failed search never proves absence |
| candidate != fact | core law | applies equally to semantic/symbol/graph/memory lanes |
| no authority collapse | core law | docs/source/tests/runtime/Human remain distinct |
| bounded repair | core | retry count comes from task packet; no retry-until-pass |

## Historical content that must not be copied as-is

### Old module names

The #87 candidate links generic files such as:

```text
modules/document-routing.md
modules/semantic-retrieval.md
modules/symbol-operations.md
modules/code-graph-impact.md
modules/project-memory.md
```

The active #91/#93 architecture uses stable references plus provider/domain modules. Do not create duplicate generic provider layers just to satisfy the historical links.

Current provider module identities are:

```text
modules/grepai.md
modules/serena.md
modules/code-graph-rag.md
modules/mem0.md
```

Stable host-neutral routing/evidence/output law belongs under `references/`.

### Historical executable contract

Do not revive `scripts/check_repo_agent_native.py` as the Phase-2 canonical mechanism. Its assertion semantics are useful inputs, but #92 explicitly chooses Bun + TypeScript for the implementation child.

Port these semantic checks:

- portable frontmatter allowlist;
- `name` matches directory;
- concise non-empty description;
- progressive-disclosure size budget;
- required core sections/state machine;
- repository-relative links cannot escape the Skill root;
- no absolute machine paths or consumer-specific durable state in portable surfaces;
- module contract completeness;
- eval/verifier paths must exist and stay inside repository;
- planted hollow mutations must fail.

Do not preserve Python-specific implementation or its old path inventory as authority.

### Historical consumer/provider state

Never copy:

- Bettor branch/path/remotes;
- current provider health claims;
- credentials or session identities;
- mutable `main` as execution identity;
- dated receipts;
- machine-local symlinks;
- live Claude/Codex success claims.

These remain consumer/runtime/evidence-plane facts.

## Core-to-module boundary

The new `SKILL.md` should mention capability slots and dispatch laws, not product manuals.

```text
core asks for semantic discovery
  -> evaluate module trigger/health
  -> grepai module may execute
  -> result remains candidate
  -> current source read-back
  -> accept/downgrade/fallback
```

The same shape applies to Serena, graph, and memory modules.

A module may specialize:

- trigger/non-trigger;
- provider/project/index/graph/namespace health;
- query shape and budget;
- provider-specific failure vocabulary;
- deterministic fallback.

A module may not specialize:

- source-truth authority;
- evidence promotion law;
- output hard-gate semantics;
- Human Admit;
- permission widening.

## Target portable core State Machine

The Phase-2 core should converge on this host-neutral state machine:

```text
S0 SCOPE
-> S1 ROUTE
-> S2 DISCOVER
-> S3 SELECT CAPABILITY/MODULE
-> S4 READ CURRENT SOURCE
-> S5 VERIFY / CLASSIFY EVIDENCE
-> S6 INFER DEPENDENCIES
-> S7 WRITE CONTRACT OUTPUT
-> S8 ASSERT
-> S9 HANDOFF
```

Named failures should include at least:

```text
SUBJECT_ABSENT
SUBJECT_IDENTITY_MUTABLE
SCOPE_AMBIGUOUS
REQUIRED_ROUTE_ABSENT
MODULE_TRIGGER_AMBIGUOUS
CAPABILITY_UNHEALTHY
SOURCE_UNREADABLE
SOURCE_CHANGED
SOURCE_REFERENCE_INVALID
ABSENCE_BOUNDARY_UNDECLARED
EVIDENCE_CEILING_EXCEEDED
MEMORY_CONFLICT
ASSERTION_FAILED
BUDGET_EXHAUSTED
HUMAN_ADMIT_REQUIRED
```

Provider-specific states remain in modules and are mapped to the nearest core failure without erasing the detailed receipt.

## Bun assertion migration contract

Phase 2 requires these executable surfaces:

```text
bun scripts/validate-skill.ts --skill-root <path> --json <receipt>
bun scripts/assert-output.ts --repo <repo> --report <report.json> --receipt <receipt.json>
bun tests/selftest.ts
```

### `validate-skill.ts`

Must verify portable structure and module boundaries. It must not call network providers.

Minimum mutation kills:

- unknown/Claude-only canonical frontmatter;
- over-budget core;
- broken/escaping relative link;
- absolute host path;
- consumer-specific branch/path/session material;
- missing required module contract field;
- module law override;
- missing eval/fixture/verifier subject;
- ambiguous module-routing fixture represented as PASS.

### `assert-output.ts`

Must implement `references/OUTPUT_CONTRACT.md` against an exact repository subject.

Minimum positive controls:

- valid repository-relative source ref;
- valid line range;
- optional digest match;
- accepted `A` fact with source-read verification lane;
- output/receipt bound to the same source subject.

Minimum hollow controls:

- missing/absolute/escaping ref;
- out-of-range line;
- digest mismatch;
- `D` fact promoted to accepted fact;
- semantic/graph/memory candidate promoted without source read-back;
- stale source subject;
- secret/machine/session-shaped value in durable output.

### `selftest.ts`

Must run positive + hollow/mutation fixtures deterministically and without network. A load-bearing mutation that survives is a test failure.

## Module-routing fixture consumption

PR #93 adds `evals/fixtures/module-routing-cases.json`. The selftest/router must consume it mechanically; do not leave it as documentation-only data.

Expected classes:

```text
MODULE
a specific provider module selected

CORE_ONLY
portable Tier-0 path is sufficient

FALLBACK_CORE
requested provider is stale/wrong/incomplete/conflicted; core continues with named fallback

BLOCK
ambiguous primary module or attempted law override
```

## Phase-2 Definition of Done

PR #93 may leave Draft only when all are true:

- canonical `SKILL.md` is rewritten under the current contracts and below the admitted budget;
- no historical consumer/runtime state leaks into the core;
- four provider modules remain optional and trigger-selected;
- module-routing fixture is executable and mutation-sensitive;
- Bun structural validator exists and kills its hollow controls;
- Bun output verifier exists and validates exact source refs/subject identity;
- deterministic selftest is zero-network and bounded;
- owning exact-head workflow actually executes and is green;
- physical Claude/Codex/provider A/B remains explicitly `NOT_EXERCISED` and is deferred to #95.

After Phase 2 lands, Phase 3 #95 consumes these contracts. Final canonical release is #88 after paired A/B and Bettor canaries.
