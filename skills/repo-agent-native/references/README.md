# Reference contracts

`references/` contains reusable host-neutral contracts selected by the portable procedure. These documents explain stable interfaces; executable acceptance remains in `../scripts/`, `../tests/`, and the exact subject-bound receipts.

| File | Responsibility |
|---|---|
| `DOCUMENT_ROUTES.md` | repository instruction/context/ADR/nearest-README read order and absence behavior |
| `EVIDENCE_MODEL.md` | evidence levels, source authority, promotion, and contradiction rules |
| `HOST_COMPATIBILITY.md` | portable Agent Skills core versus Codex/Claude host projections |
| `OUTPUT_CONTRACT.md` | invariant report shape, hard assertions, and exit semantics |
| `TOOL_ROUTING.md` | capability-based optional-provider selection and deterministic fallback |
| `PORTABLE_CORE_MIGRATION.md` | semantic migration map from superseded PR #87 into the active #91/#93 contract-first architecture |
| `CI_ADMISSION.md` | owning exact-head Bun contract workflow requirements and evidence-state boundary for Phase 2 |

## Authority boundary

The migration and CI documents are implementation/handoff contracts, not runtime evidence. The executable authorities are the admitted scripts/tests plus an actually executed exact-head workflow receipt.

Provider deployments, repository paths, credentials, live health, consumer receipt locations, and physical Claude/Codex A/B results do not belong here.
