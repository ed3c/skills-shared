# repo-agent-native

`repo-agent-native` extracts source-anchored business invariants and implicit dependencies from an existing codebase before a brownfield change. The canonical `SKILL.md` is a portable procedural core; optional retrieval products and domain modes remain trigger-selected modules rather than hidden prerequisites.

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
| Phase-3 A/B method and evidence boundary | `references/A_B_TESTING.md` |
| Domain/tool instance triggers | `modules/README.md` and the selected module only |
| A/B cases, weights, and admission rule | `evals/evals.json` and `evals/README.md` |
| Executable structural, output, source-predicate, and A/B assertions | `scripts/` |
| Positive, mutation, exit-code, and A/B controls | `tests/selftest.ts` and `tests/ab-selftest.ts` |
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
  deterministic assertions and bounded A/B runner; no network by default
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

A tool being installed, a graph being queryable, or a memory being returned is not proof that a code fact is current. Every output fact needs at least one valid `source_ref`; claims about runtime behavior require the appropriate control or receipt.

## Executable checks

Run from this Skill directory:

```bash
bun scripts/validate-skill.ts --skill-root . --json <skill-receipt.json>
bun scripts/assert-output.ts --repo <repo> --report <report.json> --receipt <output-receipt.json>
bun tests/selftest.ts
bun tests/ab-selftest.ts
bun scripts/run-ab.ts --carrier <codex|claude> --condition <condition> \
  --case <case> --output <fresh-dir> [--repetitions 1-3] [--execute]
```

The structural and output commands write subject-bound JSON receipts. The selftests use disposable local fixtures and write no durable evidence. Exit `0` means the declared subject passed, `2` means an evaluated hard assertion failed, `64` means usage or required input was invalid or absent, and `70` means the checker itself failed.

The A/B admission score is computed from independently re-observed structured predicates and a bounded procedure contract. Lexical aliases are diagnostic only. `no_skill` installs no Skill and receives no optional-provider or procedural knowledge beyond the common task, subject, and schema adapter.

A receipt proves only what was executed against its recorded subject. It does not prove a provider is currently running, an index is current, a carrier loaded the Skill, a pull request is mergeable, or a Human admitted promotion.

## Stack and exact-subject binding

```text
main
→ #91 contract/eval admission                  MERGED
→ #93 portable core + owning exact-head CI     PARENT
→ #96 replayable A/B evidence                  CURRENT CHILD
→ Bettor consumer canaries
→ #88 canonical release admission
→ Human Admit
```

The current child was mechanically replayed on parent commit `12615a0efd9a763e2272c81c379453b740ee5757`. The previous child head remains available at rollback branch `rollback/repo-agent-native-v2-ab-cdcf8b5`.

Parent run `31776452443` executed `Repo Agent Native Contract` successfully at exact parent head `12615a0efd9a763e2272c81c379453b740ee5757`. This parent receipt proves the Phase-2 structural and output contract only. It does not prove the Phase-3 child, physical model A/B, provider behavior, consumer integration, or release admission.

Any parent-head, child-head, evaluator, fixture, or scorer change invalidates older child evidence. Re-run all owning checks against the new exact subject before admission.

## Current evidence

```text
pre-refactor SKILL.md baseline       PRESENT with immutable commit/blob identity
contract/eval documentation          IMPLEMENTED on merged PR #91
portable-core rewrite                IMPLEMENTED on parent PR #93
Phase-2 owning workflow              IMPLEMENTED on parent PR #93
Phase-2 exact-parent contract run    PASS at 12615a0e / run 31776452443
deterministic Bun assertions         IMPLEMENTED
positive/mutation controls           IMPLEMENTED
blind A/B runner and scorer          IMPLEMENTED on child PR #96
structured source predicates         IMPLEMENTED for the retry fixture
offline source-mutation sensitivity  IMPLEMENTED for attempts/delay/sink
child exact-head hosted checks        NOT_EXERCISED after parent replay
Claude Code physical carrier         NOT_EXERCISED by current evaluator
Codex CLI physical carrier           NOT_EXERCISED by current evaluator
cross-harness generalization matrix  NOT_EXERCISED
Bettor portable binding/canaries     NOT_IMPLEMENTED in this phase
canonical v2 release                 NOT_ADMITTED; final issue #88
```

## Migration phases

1. **Contract and eval admission** — merged PR #91.
2. **Portable core and assertions** — parent PR #93 / issue #92.
3. **Tool adapters and blind A/B** — child PR #96 / issue #95.
4. **Bettor consumer migration and canaries** — immutable selected bundle and separate Claude/Codex receipts.
5. **Canonical release admission** — issue #88 after Phase 3 and consumer evidence, with rollback identity and Human Admit.

## Change contract

A procedural change requires trigger and non-trigger coverage, source-anchor assertions, optional-tool fallback controls, hard-gate compatibility, A/B comparison, affected consumers, rollback identity, and Human Admit. A tool or domain module change requires a unique trigger, explicit assumptions, bounded context, positive and ambiguity/staleness/contradiction controls, and proof that the portable core still works without it.
