# PR #271 → current-main control-plane reconciliation

Tracking: #300, #299. Source bundle: PR #271. Current architecture authority: #268 + current `main`.

The staged PR #271 is not a merge source. Its contracts are classified field-by-field so useful semantics can be retained without restoring pre-#268 Skill bodies or creating a second control-plane implementation.

| #271 surface | Disposition | Current-main rule |
|---|---|---|
| six canonical Skill identities and fixed capability set | already represented | Keep the six names in the canonical profile; internal Skill bodies follow #268 procedural-core/module boundaries. |
| `.agents/shared-skills.requirements.json` + `.agents/repository-control-plane.json` paths | superseded | Current main uses `.agents/control-plane/profile.json` and `.agents/control-plane/requirements.json` plus the generated immutable binding. Do not maintain two attachment layouts. |
| immutable binding via `shared_skills.py sync` | already represented | Keep central canonical bodies and generated exact binding; no consumer body copies. |
| split `repository_control_plane_profile.py` / consumer / monitor Python modules | historical evidence only | Current main intentionally keeps one small zero-network CLI. Split only if independent evolution later proves necessary; do not port structure for its own sake. |
| GitHub-specific `github-open-issues-snapshot` schema | superseded by provider-neutral core | Core packet is generic `repository`, `number`, `state`, `depends_on`, optional `required_phases`. GitHub/Forgejo/GitLab adapters remain provider/runtime-owned. |
| per-issue applicability (`REQUIRED`, `MONITOR`, `NOT_APPLICABLE_WITH_EVIDENCE`) | port | Preserve as portable procedural law. Binding a capability is not mandatory execution. |
| typed `required_receipts` and `execution_state` | port | Emit only receipts for `REQUIRED` phases; keep `execution_state=NOT_EXERCISED` until live evidence. |
| monitor-plan JSON Schema | port, redesigned | Use the provider-neutral `repository-control-plane-monitor-plan.v1.schema.json`; do not revive GitHub-specific source/query constants. |
| dependency cycle/duplicate controls | already represented | Current main owns generic deterministic DAG validation. |
| missing dependency closure and closed-blocker fixtures | already represented | #297/main fail closed when a dependency identity is absent; included closed blockers satisfy the edge without a wave. |
| shadow-copy refusal | already represented | Consumer-local canonical bodies remain forbidden; thin forwarder/surface semantics stay governed by shared-skills infrastructure. |
| mutable runtime-ref / runtime install claims | runtime-owned elsewhere | Git Town user-scoped installation and receipts are runtime-env #36; Forgejo fresh-host lifecycle is runtime-env #38. |
| migration/rollback narrative | retain as guidance, not duplicate implementation | Consumer detach/rollback must not delete canonical Skills, uninstall user tools, stop shared Forgejo or fabricate runtime PASS. |
| GitHub polling/query behavior | runtime/provider adapter | Core monitor remains zero-network. `runtime-env#37` or another admitted adapter obtains provider snapshots. |
| live Stack/dual-forge evidence | runtime/live-canary owned | #234/#256; static control-plane CI cannot promote these lanes. |
| automatic merge/conflict/visibility authority | explicitly rejected | Current profile and Shadow monitor keep these false/Human-owned. |

## Result

The only #271 semantics that still require current-main bytes are:

```text
applicability-aware phase dispositions
provider-neutral typed monitor-plan output
mutation controls proving no fake Stack/Forge requirement and no authority widening
```

All other #271-only implementation structure is either already represented, superseded by the generic current-main model, runtime-owned elsewhere, or retained only as historical evidence.

After the current-main-compatible applicability/schema slice passes exact-head deterministic gates, PR #271 should be closed as superseded rather than merged. Closing it does not imply runtime PASS, merge/promotion of any consumer repository, or deletion of its historical evidence.
