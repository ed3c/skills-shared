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
  deterministic assertions and A/B runner; no network by default
```

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

1. **Contract and eval admission** — admitted by the parent PR. Added navigation, compatibility, evidence/output contracts, baseline identity, and fixtures.
2. **Portable core and assertions** — current child. Rewrites `SKILL.md`; adds Bun + TypeScript validation/selftests; moves provider details behind triggers.
3. **Tool adapters and blind A/B** — bounded adapters and old-vs-new benchmark receipts.
4. **Bettor consumer migration** — immutable selected bundle/relative projections and Claude/Codex consumer canaries.

The exact PR stack and acceptance criteria are tracked by issue #89.

## Current evidence

```text
pre-refactor SKILL.md baseline       PRESENT with immutable commit/blob identity
contract/eval documentation          IMPLEMENTED on parent commit
portable-core rewrite                IMPLEMENTED on this feature branch
deterministic Bun assertions         IMPLEMENTED on this feature branch
positive/mutation controls           IMPLEMENTED on this feature branch
blind A/B model runs                 NOT_EXERCISED
Claude Code live carrier             NOT_EXERCISED
Codex CLI live carrier               NOT_EXERCISED
Bettor portable binding              NOT_IMPLEMENTED in this phase
```

## Change contract

A procedural change requires trigger/non-trigger coverage, source-anchor assertions, optional-tool fallback controls, hard-gate compatibility, A/B comparison, affected consumers, rollback identity, and Human Admit. A tool/domain module change requires a unique trigger, explicit assumptions, bounded context, positive and ambiguity/staleness/contradiction controls, and proof that the portable core still works without it.

## Traceability

```text
issue #89
→ contract/eval PR
→ portable-core child PR
→ tool/A-B child PR
→ immutable Skill release
→ Bettor consumer migration
→ Claude/Codex consumer receipts
→ Human Admit
```
