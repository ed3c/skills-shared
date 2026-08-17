# Document Routing Contract v1

This contract gives Claude Code, Codex CLI, and human maintainers the same multi-hop path through modular repositories. It is a navigation contract, not a replacement for manifests, schemas, scripts, receipts, or Git history.

## Standard route interface

| ID | Path | Responsibility |
|---|---|---|
| `DR-R0` | `README.md` | first entry, project role, concise current boundary |
| `DR-R1` | `AGENTS.md` | mandatory read order, laws, completion report |
| `DR-R1C` | `CLAUDE.md` | thin Claude host projection to `AGENTS.md` |
| `DR-R2C` | `CONTEXT.md` | mutable current handoff; no stable laws |
| `DR-R2A` | `ARCHITECTURE.md` | stable ownership, planes, invariants |
| `DR-R3` | `docs/INDEX.md` | complete local route map |
| `DR-R4D` | `docs/architecture/DOCUMENT_ROUTING.md` | local binding of this route contract |
| `DR-R4S` | `docs/architecture/STATE_MACHINES.md` | owner/input/output/transition/terminal/evidence map |
| `DR-R4X` | `docs/integration/CROSS_REPO_INTEGRATION.md` | inter-repository roles and contract flow |
| `DR-R4T` | `docs/traceability/TRACEABILITY_INDEX.md` | source → decision → issue → PR → eval → receipt |
| `DR-R5` | `<governed-directory>/README.md` | nearest owner and local data-flow contract |
| `DR-R6` | machine authority | manifest/schema/script/verifier/receipt reached from README |

## Repository closure route interface

A repository-wide completion review binds six routes. Two of them are the standard routes above; a consumer binding names its own paths for the rest.

| ID | Generic route | Responsibility |
|---|---|---|
| `DR-C1` | current integration status | what is landed, admitted, open and blocked right now, reconciled against the tree |
| `DR-C2` | real-problem closure matrix | one row per real problem: closure state, evidence kind, lane, exact receipt |
| `DR-C3` | Issue dual-dependency DAG | one Issue graph with separate start and completion edge classes |
| `DR-C4` | Molecular Stack PR index | atoms, parents, path leases, Gates, heads and missing atoms |
| `DR-R5` | nearest directory README | the owner who reconciles that directory next time |
| `DR-R6` | machine authority / exact receipt | the schema, verifier or receipt that decides, on its exact subject |

Portable contracts: [`../../skills/agentic-tech-lead-orchestration/references/REPOSITORY_CLOSURE_RECONCILIATION.md`](../../skills/agentic-tech-lead-orchestration/references/REPOSITORY_CLOSURE_RECONCILIATION.md) for `DR-C1`–`DR-C3`, [`../../skills/git-town-stacked-pr-worker/references/MOLECULAR_STACK_INDEX.md`](../../skills/git-town-stacked-pr-worker/references/MOLECULAR_STACK_INDEX.md) for `DR-C4`.

A repository may keep a more detailed canonical document at another path. The standard route may be a thin forwarder, but it must summarize the local owner and direct destination; it must not send the reader to another unexplained index.

## Multi-hop procedure

```text
classify task
→ root README / AGENTS
→ current CONTEXT + stable ARCHITECTURE
→ docs/INDEX
→ nearest directory README
→ machine authority
→ current evidence / traceability
```

The normal target is at most two intentional hops from the nearest README to the machine authority and evidence. Cross-repository facts are never inferred from a sibling checkout.

## Assertions

| ID | Assertion |
|---|---|
| `DR-01` | Root routes exist or an explicit binding names why a route is absent. |
| `DR-02` | Relative Markdown links resolve inside the repository. |
| `DR-03` | Every governed directory has a nearest README or named inheritance. |
| `DR-04` | A README names owner, purpose, inputs, outputs, state machine, evidence, allowed and forbidden changes. |
| `DR-05` | Markdown does not duplicate a machine API/schema/registry/receipt/verifier authority. |
| `DR-06` | No machine-local path, credential, browser/device session, or secret value enters portable docs. |
| `DR-07` | `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, and `SKIPPED_BY_POLICY` remain distinct. |
| `DR-08` | Target architecture and current state are separate routes. |
| `DR-09` | `SKILL.md` contains procedural generalization; `modules/` contains on-demand domain instances. |
| `DR-10` | Cross-repository roles and immutable binding/release flow agree across all participants. |
| `DR-11` | If Git Town is admitted, docs distinguish sibling, true child, terminal leaf, convergence leaf, and Human operations. |
| `DR-12` | Source proposals do not become current implementation or live evidence without verification and receipts. |
| `DR-13` | Route status is reconciled with the actual tree inventory, not with a prior diagram. |
| `DR-14` | An existing path is not `PLANNED` and an absent path is not implemented. |
| `DR-15` | Source-reported, synthetic, live-substrate, and business-outcome evidence remain distinct states. |
| `DR-16` | Open Draft, admitted, merged, CI-passed, released, and production remain distinct states. |
| `DR-17` | Start dependencies and completion dependencies are separate edge classes. |
| `DR-18` | Cloud, local, private, and Human lanes cannot satisfy one another. |
| `DR-19` | Every convergence has one explicit owner and exact parents. |

## Knowledge-continuity rule

Every route must leave an in-place summary before linking away. A reader may choose to follow the link for detail, but must not need the link merely to understand why the route exists. This extends the `knowledge-continuity` rule that two-hop-to-evidence chains and knowledge outsourcing are defects.

## Skill loading rule

The procedural core stays in `SKILL.md`. Generic contracts live in `references/`. Domain examples live in `modules/` and are loaded only when task/repository/domain triggers match. Consumer-specific facts stay in consumer bindings and READMEs.

## Evidence boundary

A documentation route can be statically reviewed. It cannot prove a host tool, Git Town binary, GitHub/Forgejo equivalence, provider session, browser/device, model run, cloud sandbox, license closure, or production release.
