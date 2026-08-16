---
name: gemini-conversation-research
description: |
  Generalized conversation-research procedure for turning an existing dialogue or a guided question sequence into a source-bound knowledge map, classifying real gaps, dispatching only unresolved gaps to optional research capabilities, measuring coverage, and handing off evidence without treating any provider or browser runtime as universal authority.
---

# Conversation Research Procedure

<!-- PORTABLE_CORE_START -->

## Contract

Use this Skill when the task is to extract, structure, challenge, extend, and verify knowledge from an existing conversation or a guided dialogue. The portable procedure owns analysis, gap control, coverage, evidence state, and bounded iteration. Concrete providers, browser carriers, research engines, storage targets, and consumer paths are selected only through `modules/domain-profile.md`.

## State machine

```text
SUBJECT_BOUND
→ SOURCE_CAPTURED
→ STRUCTURE_EXTRACTED
→ LOCAL_GAPS_PROBED
→ GAP_CLASSIFIED
→ OPTIONAL_RESEARCH_DISPATCHED
→ EVIDENCE_HARVESTED
→ COVERAGE_ASSERTED
→ {ITERATE | HANDOFF | STOP}
```

A source that cannot be captured exactly enough for the requested claim remains blocked; a missing optional research capability does not invalidate already-grounded knowledge.

## Hard laws

- **CORE-LAW-001 — exact subject first.** Bind the conversation/guided-dialogue subject and source identity before analysis or external research.
- **CORE-LAW-002 — procedure is not provider state.** Provider, browser, storage, repository, and runtime mechanics belong to the selected domain module or consumer binding, never the portable core.
- **CORE-LAW-003 — evidence outranks prose.** Direct source capture and deterministic/readback assertions outrank model summaries; missing or unexecuted evidence cannot become `PASS`.
- **CORE-LAW-004 — modules cannot widen authority.** A module may specialize capture or research execution but may not override core laws, weaken evidence state, or widen filesystem/network/secret/merge authority.
- **CORE-LAW-005 — bounded convergence.** Every iteration must close named gaps, preserve unresolved gaps, bind terminal evidence state, and stop or hand off when further progress is unsupported or uneconomic.

## Procedure

1. **Bind subject.** Freeze the input conversation, guided context, scope, privacy boundary, and required outputs.
2. **Capture source.** Preserve the source or a content-addressed projection without silently summarizing away evidence needed later.
3. **Extract structure.** Produce topics, claims, assumptions, decision points, questions, and confidence/evidence references.
4. **Probe locally first.** Use the existing dialogue/context to resolve cheap gaps before invoking an optional research capability.
5. **Classify gaps.** Separate already-grounded facts, inferential gaps, external-fact gaps, and unknowable/blocked gaps.
6. **Dispatch minimally.** Send only unresolved research gaps to an admitted capability selected by `modules/domain-profile.md`.
7. **Harvest evidence.** Preserve returned evidence, provenance, and weaker states separately from verified source truth.
8. **Assert coverage.** Recompute the requested knowledge dimensions and leave every uncovered critical/high gap explicit.
9. **Iterate boundedly.** Repeat only while the gap set shrinks under the declared budget; otherwise stop or hand off.

## Module selection

Load `modules/domain-profile.md` only when a concrete provider, browser carrier, deep-research engine, knowledge store, or consumer repository must be bound. Domain selection never changes the state machine or the five core laws.

## Executable assertion

Run:

```bash
python3 scripts/check_skill_core_boundaries.py --skill gemini-conversation-research
```

A zero exit proves only the structural procedural-core/domain boundary for current repository bytes.

## Evidence states

Use distinct states: `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED`. Static structure cannot promote a browser/provider/research/storage lane to runtime `PASS`.

## Stop and handoff

Stop when requested coverage is reached, required evidence is unavailable, privacy/authority blocks the next transition, the gap set no longer shrinks, or the iteration budget is exhausted. Handoff must include exact subject, remaining gaps, evidence states, module/runtime identities when used, and the next admissible action.

<!-- PORTABLE_CORE_END -->

## Domain specialization

Provider-specific execution lives in [modules/domain-profile.md](modules/domain-profile.md). Existing detailed conversation-analysis modules remain optional specializations and may extend, but never replace, this procedure.
