# repo-agent-native

`repo-agent-native` extracts source-anchored business invariants and implicit dependencies from an existing codebase before a brownfield change. The canonical `SKILL.md` is now a portable procedural core; optional retrieval products and domain modes remain trigger-selected modules rather than hidden prerequisites.

## Document authority

| Subject | Authority |
|---|---|
| Portable Agent workflow and laws | `SKILL.md` |
| Human/Agent navigation and current migration state | this `README.md` |
| Host compatibility | `references/HOST_COMPATIBILITY.md` |
| Repository document routing | `references/DOCUMENT_ROUTES.md` |
| Evidence levels and source-truth rules | `references/EVIDENCE_MODEL.md` |
| Output fields and deterministic assertions | `references/OUTPUT_CONTRACT.md` |
| Optional tool selection and fallback | `references/TOOL_ROUTING.md` |
| Phase-2 semantic migration map | `references/PORTABLE_CORE_MIGRATION.md` |
| Phase-2 owning CI admission contract | `references/CI_ADMISSION.md` |
| Phase-2 owning workflow | `../../.github/workflows/repo-agent-native-contract.yml` |
| Domain/tool instance triggers | `modules/README.md` and the selected module only |
| A/B cases and admission rule | `evals/evals.json` |
| Executable structural and output assertions | `scripts/validate-skill.ts` and `scripts/assert-output.ts` |
| Positive, mutation, and exit-code controls | `tests/selftest.ts` |
| Merge, provider activation, legal admission | Human Admit |

Markdown explains the contract. It does not replace source code, schemas, executable assertions, receipts, or the exact issue/PR acceptance subject.

## Mandatory read order

1. Repository `AGENTS.md`, `README.md`, and current integration state.
2. This README.
3. `SKILL.md`.
4. `references/DOCUMENT_ROUTES.md` and the target repository's routed documents.
5. `references/EVIDENCE_MODEL.md` and `references/OUTPUT_CONTRACT.md`.
6. `references/TOOL_ROUTING.md`.
7. `modules/README.md`, then only the module whose trigger matches.
8. `evals/evals.json`, fixture ground truth, and the exact issue/PR.

A missing route, source file, line range, tool health check, module trigger, or evidence subject is `ABSENT`; do not fill it from memory or prose.

## Procedural state machine

```text
SCOPE
→ ROUTE REPOSITORY DOCUMENTS
→ DISCOVER CANDIDATES
→ VERIFY OPTIONAL TOOL HEALTH
→ READ SOURCE BODY
→ EXTRACT POSITIVE AND NEGATIVE INVARIANTS
→ INFER IMPLICIT DEPENDENCIES
→ WRITE SOURCE-ANCHORED OUTPUT
→ ASSERT OUTPUT
→ AUDIT AND HAND OFF
```

Stable failure states include:

```text
TARGET_ABSENT
ROUTE_ABSENT
SOURCE_CHANGED
SOURCE_REF_INVALID
TOOL_UNHEALTHY_FALLBACK
TOOL_CONTRADICTION
MODULE_TRIGGER_AMBIGUOUS
UNSUPPORTED_CLAIM
OUTPUT_SCHEMA_FAIL
ASSERTION_FAIL
```

Optional-tool failure does not block the portable core when `git`, `rg`, direct reads, compiler diagnostics, and tests can complete the task. The fallback and resulting evidence level must be recorded.

## Procedure and module boundary

```text
SKILL.md
  source-anchored workflow, laws, typed evidence, fallback, Human boundary

references/
  detailed stable method/reference material loaded on demand

modules/
  optional tool/domain instances selected by explicit trigger

scripts/
  deterministic Phase-2 structural/output assertions; no network by default
```

Blind paired A/B execution is a Phase-3 concern tracked by issue #95; it is not implemented by the Phase-2 scripts merely because the cases and metrics are declared.

A module may specialize terminology, tool health checks, query shapes, or domain output. It may not override source-code authority, widen permissions/effects, store consumer paths or secrets, or promote memory/search/graph results directly to facts.

## Tool lanes

| Lane | Role | Truth boundary |
|---|---|---|
| `git` + `rg` + direct read | mandatory deterministic fallback | source candidate and source body |
| grepai | semantic candidate discovery and optional call hints | requires current index health and source read-back |
| Serena | symbol/reference/diagnostic/refactor operations | requires correct project/language health and source read-back |
| Code-Graph-RAG or admitted graph provider | cross-language graph/data-flow candidate generation | requires graph freshness and source read-back |
| mem0 or admitted memory provider | episodic/project-decision context | never source truth; requires provenance, freshness, privacy, and conflict handling |

No optional tool is mandatory for the procedural core.

## Evidence states

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
```

A tool being installed, a graph being queryable, or a memory being returned is not proof that a code fact is current. Every output fact needs at least one valid `source_ref`; claims about runtime behavior require the appropriate control/receipt.

## Executable checks

Run from this Skill directory:

```bash
bun scripts/validate-skill.ts --skill-root . --json <skill-receipt.json>
bun scripts/assert-output.ts --repo <repo> --report <report.json> --receipt <output-receipt.json>
bun tests/selftest.ts
```

The first two commands write subject-bound JSON receipts; the selftest uses disposable local fixtures and writes no durable evidence. Exit `0` means the declared subject passed, `2` means an evaluated hard assertion failed, `64` means usage or required input was invalid/absent, and `70` means the checker itself failed. See `scripts/README.md` and `tests/README.md` for the full boundary.

A receipt proves only what was executed against its recorded subject. It does not prove a provider is currently running, an index is current, a carrier loaded the Skill, a pull request is mergeable, or a Human admitted promotion. Those live states require separate observations.

## Migration stack

1. **Contract and eval admission** — admitted by PR #91. Added navigation, compatibility, evidence/output contracts, baseline identity, and fixtures.
2. **Portable core and assertions** — current PR #93 / issue #92. Rewrites `SKILL.md`; adds Bun + TypeScript validation/selftests; moves provider details behind triggers.
3. **Tool adapters and blind A/B** — issue #95. Adds bounded provider adapters and exact old-vs-new benchmark receipts.
4. **Bettor consumer migration/canaries** — immutable selected bundle/relative projections and separate Claude/Codex consumer receipts.
5. **Canonical release admission** — issue #88 after Phase 3 and consumer evidence, with rollback identity and Human Admit.

## Current evidence

```text
pre-refactor SKILL.md baseline       PRESENT with immutable commit/blob identity
contract/eval documentation          IMPLEMENTED on merged PR #91
portable-core rewrite                IMPLEMENTED on PR #93 branch
deterministic Bun assertions         IMPLEMENTED on PR #93 branch
positive/mutation controls           IMPLEMENTED on PR #93 branch
module-routing fixture contract      IMPLEMENTED on PR #93 branch
owning repo-agent-native CI workflow IMPLEMENTED on PR #93 branch
exact-head Bun CI execution          NOT_EXERCISED until the owning job completes
semantic model routing               NOT_EXERCISED; Phase 3 #95
blind A/B model runs                 NOT_EXERCISED; Phase 3 #95
Claude Code live carrier             NOT_EXERCISED
Codex CLI live carrier               NOT_EXERCISED
Bettor portable binding/canaries     NOT_IMPLEMENTED in this phase
canonical v2 release                 NOT_ADMITTED; final issue #88
```

Workflow presence proves only `IMPLEMENTED`. Exact-head contract evidence becomes `PASS` only when `repo-agent-native-contract.yml` executes the candidate head successfully.

## Change contract

A procedural change requires trigger/non-trigger coverage, source-anchor assertions, optional-tool fallback controls, hard-gate compatibility, A/B comparison, affected consumers, rollback identity, and Human Admit. A tool/domain module change requires a unique trigger, explicit assumptions, bounded context, positive and ambiguity/staleness/contradiction controls, and proof that the portable core still works without it.

## Traceability

```text
#89 PRD
→ #91 contract/eval admission             MERGED
→ #92 / #93 portable core + assertions    ACTIVE
→ #95 bounded adapters + blind paired A/B
→ Bettor Claude/Codex consumer canaries
→ #88 canonical release admission
→ Human Admit
```
