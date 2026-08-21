# Adapter modules

The Skill core is provider-neutral. Load a module only when its trigger matches and the repository admits the provider, projection, evidence, or delivery surface. File presence or installed binaries never activate a module by themselves.

| Module | Role | Authority ceiling |
|---|---|---|
| `deterministic-code-intelligence.md` | SCIP + SQLite exact-subject graph and Tree-sitter slicing | rebuildable evidence projection; no task-state or merge authority |
| `semantic-intent-anchor.md` | grepai semantic seed discovery and runtime exploration | candidate locations only; direct source readback required |
| `agent-executor.md` | Serena or another admitted Worker executor | bounded edits in one worktree/path lease |
| `vector-store.md` | LanceDB AST/example retrieval | optional candidate store; never source or absence truth |
| `stacked-delivery.md` | Git Town plus forge adapter | branch/Stack mechanics under repository policy; no merge authority |
| `tournament-mode.md` | Orca/ADE-style parallel alternatives | same locked contract, isolated branches, deterministic selection |
| `codex-sdk-controller.md` | bind one frozen Tech Lead task/attempt to the official Codex SDK | runtime result only; planner/DAG/admission/merge/release authority stays outside the adapter |
| `github-issue-dag-projection.md` | project validated completion-readiness edges to GitHub Issue Dependencies and read them back | durable collaboration projection only; GitHub metadata is not semantic DAG truth and unmanaged extra blockers are not auto-deleted |
| `herdr-runtime-observer.md` | optional workspace/pane/process/session/worktree observer | identity/state observation only; `DONE_CANDIDATE` is never implementation PASS and absence falls back to direct Codex SDK + git worktree |
| `problem-closure-ledger.md` | reconcile exact source claims with task/DAG/issue/session/evidence/Shadow closure | deterministic closure consistency only; issue/PR/UI state cannot promote local evidence to live/Human/release evidence |

For issues #375–#379, read [`../../../docs/traceability/CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md`](../../../docs/traceability/CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md) plus the matching execution packet under `../references/execution-packets/` before selecting any of the four control-plane modules.

Every module must state or preserve its trigger, non-trigger, purpose, assumptions, inputs, outputs/effects, evidence/freshness, fallback, core laws, and consumer-owned values. A module cannot move provider-specific authority into `SKILL.md`, cannot self-certify its own output, and cannot convert deterministic/static evidence into live evidence.
