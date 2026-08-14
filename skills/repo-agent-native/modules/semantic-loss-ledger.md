# repo-agent-native semantic loss ledger

Baseline is the immutable `d277e56870c0cc18455c9dd5e572a43ca08b444b:skills/repo-agent-native/SKILL.md` blob `8ec121bab2159353a257848d7292250eb78a1e76`, pinned by [`../evals/baseline.json`](../evals/baseline.json). Git is the byte authority; this portable package does not duplicate the old consumer-bound prose.

This ledger classifies every non-overlapping semantic range of the 326-line baseline. A classification describes the current active home; the verbatim archive exists for every row and does not make archived wording executable.

## Classification meanings

| Classification | Meaning |
|---|---|
| `ACTIVE_IN_SKILL` | The portable workflow still depends on this semantic unit and the active `SKILL.md` owns it. |
| `PRESERVED_IN_MODULE` | The semantic unit remains available through a named, trigger-selected module. |
| `LEGACY_ARCHIVED` | The wording describes obsolete/historical consumer state and remains recoverable from the pinned Git blob. |
| `CANONICAL_OWNER_WITH_LEGACY_COPY` | A consumer binding or another owner now owns the value; this Skill keeps only the portable interface while Git preserves history. |

## Complete baseline coverage

| Baseline lines | Old semantic unit | Classification | Current durable home | Check |
|---:|---|---|---|---|
| 1–20 | Frontmatter identity, trigger vocabulary, exclusions, fixed consumer output and provider claims | `ACTIVE_IN_SKILL` | `../SKILL.md` frontmatter, Trigger, Non-trigger; consumer-only fragments separated below | structural checker validates portable metadata and sections |
| 21–37 | Extraction core, source-as-authority, source references, no-KG-sink framing and retarget pointer | `ACTIVE_IN_SKILL` | `../SKILL.md` Core laws; `../references/EVIDENCE_MODEL.md` | source-reference and portability mutations must fail |
| 38–50 | When-to-use cases for brownfield invariants, implicit dependencies and optional deep analysis | `ACTIVE_IN_SKILL` | `../SKILL.md` Trigger | trigger corpus and behavior cases |
| 51–62 | Not-for boundaries: wiki, runtime debugger, external verification | `ACTIVE_IN_SKILL` | `../SKILL.md` Non-trigger | non-trigger corpus |
| 63–73 | Evidence levels A/A-/B+/B/C/D and source-readback promotion law | `ACTIVE_IN_SKILL` | `../SKILL.md` S4; `../references/EVIDENCE_MODEL.md` | output verifier rejects unsupported promotion |
| 74–91 | Dated consumer-specific GrepAI/Serena/MCP health, exact local configuration and provider limitations | `LEGACY_ARCHIVED` | pinned baseline Git blob; current live state belongs to consumer binding | portable checker rejects consumer paths/live provider claims |
| 92–106 | Nine-stage deterministic workflow, subject identity, source refs, negative invariants and output intent | `ACTIVE_IN_SKILL` | `../SKILL.md` State machine, Inputs, Outputs | required-section and output-shape checks |
| 107–119 | S0 scope, target existence, commit identity, seed concepts and output-location resolution | `ACTIVE_IN_SKILL` | `../SKILL.md` S0 Scope | structural checker + subject fields in output verifier |
| 120–131 | S1 semantic/symbol/full-text discovery, fallback and symbol/file chunking | `ACTIVE_IN_SKILL` | `../SKILL.md` S2/S3; `grepai.md`; `serena.md` | degraded-provider case and readback assertions |
| 132–157 | Message/state/API/OPBE/outgoing-call scans and bounded absence proof | `PRESERVED_IN_MODULE` | `extraction-methodology.md` | module trigger contract + source-anchored behavior case |
| 158–164 | Five-step broken-box implicit-dependency inference | `PRESERVED_IN_MODULE` | `extraction-methodology.md` | implicit-dependency fields and verifier coverage |
| 165–199 | Skill-bettor-specific `docs/plans` Markdown sink and KG-to-plan design rationale | `CANONICAL_OWNER_WITH_LEGACY_COPY` | consumer binding chooses `output_root`; `../references/OUTPUT_CONTRACT.md` owns portable fields; exact wording in archive | checker forbids fixed consumer output paths |
| 200–208 | S4 advisory audit, historical absence of a machine gate and SURFACE metrics | `LEGACY_ARCHIVED` | obsolete limitation remains in the pinned Git blob; current `../SKILL.md` S7 and bundled checker are executable | checker selftest proves planted negatives turn red |
| 209–211 | Per-target behavior/source/evidence/verification SSOT table | `ACTIVE_IN_SKILL` | `../SKILL.md` S6 structured records | output verifier requires subject and source refs |
| 212–218 | Feedback, convergence, commit-drift detection and human graduation | `ACTIVE_IN_SKILL` | `../SKILL.md` S8 Handoff and Human Admit | exact-subject and handoff assertions |
| 219–225 | Empty-output fail-loud contract | `ACTIVE_IN_SKILL` | `../SKILL.md` S6 | output verifier rejects unsupported/empty factual success |
| 226–250 | Codebase Design Mastery, eight probes, specs-as-code, external-gap and no-second-command rules | `PRESERVED_IN_MODULE` | `codebase-mastery-methodology.md`; `specs-as-code-prompt.md` | module trigger/non-trigger and link closure |
| 251–281 | Former consumer's `sdlc-plan-composer` S-1 delegate inputs/outputs and integration gap | `CANONICAL_OWNER_WITH_LEGACY_COPY` | `sdlc-plan-composer` plus consumer binding own the integration; shared Skill owns generic Inputs/Outputs | portable checker rejects named consumer coupling |
| 282–311 | Former consumer's family-vs-plan output routing and lineage rationale | `CANONICAL_OWNER_WITH_LEGACY_COPY` | consumer binding owns routing; `../references/OUTPUT_CONTRACT.md` owns portable shape | output root is caller supplied, never hard-coded |
| 312–326 | Extraction, mastery, specs prompt and retarget-map module index | `PRESERVED_IN_MODULE` | current module files, `modules/README.md`, and this ledger | relative-link closure and module contract checker |

The ranges cover lines 1 through 326 exactly once. No `deleted`, `retired`, or unclassified terminal state is allowed.
