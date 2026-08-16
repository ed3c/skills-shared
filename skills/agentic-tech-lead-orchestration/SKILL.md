---
name: agentic-tech-lead-orchestration
description: |
  Convert a large coding request into a contract-first DAG, isolated Worktree
  branches, differential Worker prompts, deterministic context slices, bounded
  self-healing, and reviewable Git Town Stacked PRs. Use when one Agent would
  otherwise supervise a long mutable thread or when several Agents must work in
  parallel without inventing incompatible architecture. grepai is only an
  intent anchor, SCIP is the exact-symbol candidate graph when its subject and
  coverage are admitted, Tree-sitter is the structural slicer, Serena is an
  optional execution provider, LanceDB is optional retrieval storage, and
  code-graph-rag is not an active dependency.
license: MIT
compatibility: Agent Skills-compatible coding agents with Git repository access; optional providers require explicit identity, freshness, scope, and policy admission.
metadata:
  version: "1.0.0"
  procedure: "contract-first-agentic-tech-lead"
  default_mode: "STACK"
---

# Agentic Tech Lead Orchestration

Move from a single-threaded supervisor loop to a bounded Tech Lead control plane:

```text
one mutable Agent thread
→ contract-first decomposition
→ dependency-aware branches
→ isolated Worker execution
→ deterministic verification
→ reviewable Stack or tournament selection
```

This Skill owns the portable procedure. It does not install providers, create credentials, decide repository policy, activate Forgejo/GitHub publication, resolve semantic conflicts without proof, merge, or promote a generated change.

## Trigger

Use when at least one condition is true:

- the request crosses more than one architectural layer or public contract;
- independent subproblems can run in parallel Worktrees;
- several models should compete on one contract;
- a large change should become atomic Stacked PRs;
- context must be derived from an exact symbol graph and AST slices;
- a Worker needs bounded repair rather than repeated free-form prompting.

## Non-trigger

Do not use for a local deterministic edit whose contract, blast radius, and tests are already known. Do not fan out merely to increase Agent count. Do not use this Skill to bypass repository routing, path leases, provider admission, Human review, or a current serial acceptance queue.

## Inputs

Require one task contract containing:

```text
immutable base subject
objective and non-goals
public contracts and locked interfaces
DAG nodes and dependencies
write/read-only/forbidden paths
architecture and dependency rules
acceptance commands and non-modifiable assertions
branch mode and differential focus
provider evidence and freshness
retry/token/time budgets
publication and Human-owned boundaries
```

Missing required fields are `ABSENT`, not defaults inferred from model memory.

## Outputs

Produce:

- a validated task contract and evidence state;
- a dependency DAG with `parallel`, `serial`, or `tournament` edges;
- one prompt packet per Worker;
- Worktree/branch/Stack topology;
- context manifest with source and provider provenance;
- verification and repair receipts;
- selection or cherry-pick rationale;
- unresolved conflicts, blindspots, rollback subject, and Human Admit boundary.

## Core laws

1. **Architecture authority stays above Workers.** The Tech Lead or admitted planner fixes public contracts, boundaries, dependency policy, and acceptance oracles before implementation freedom is delegated.
2. **Workers receive bounded freedom.** A Worker may choose local implementation details inside its lease; it may not widen public types, dependencies, shared state, permissions, or publication authority.
3. **Search is not truth.** grepai, vector search, memory, symbol search, and graph traversal produce candidates. Accepted facts require current-source readback or stronger exact-subject evidence.
4. **Compiler truth is conditional.** SCIP is exact only for the recorded indexer, commit/tree, language/build coverage, and supported constructs. Stale, partial, generated, macro-heavy, dynamic, or unsupported regions remain `UNKNOWN`.
5. **Tree-sitter owns structure, not global type truth.** Use it for AST/CST boundaries, skeletonization, snippets, syntax checks, and conflict-node extraction.
6. **No double graph.** Do not build or consult code-graph-rag in the active path when SCIP + SQLite owns Def/Ref and call edges. Retained historical artifacts are migration-only.
7. **One writer lease per path.** Parallel branches must be path-disjoint or explicitly ordered by a true dependency edge.
8. **Tests are immutable oracles.** Workers may add tests inside their lease; they may not weaken supplied assertions, linters, type checks, security gates, or mutation controls.
9. **Repair is bounded.** At most three materially different attempts per stable failure signature; then stop, preserve evidence, and revise the task split or abstraction.
10. **A green branch is not a merged system.** Restack, publication, merge, promotion, provider activation, semantic-conflict admission, and rollback remain repository/Human governed.

## Evidence states

Every task-local **context grade** is exactly one of:

```text
EXACT      subject, provider identity, coverage, freshness and readback passed
DEGRADED   useful candidates exist, but exact graph/coverage/readback is incomplete
BLOCKED    a required exact precondition is absent, stale, contradictory or unsafe
```

These grades do not replace repository/run evidence states. Receipts and completion reports still use `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, or `SKIPPED_BY_POLICY`.

`DEGRADED` may support exploration and a draft patch. It may not authorize automatic cross-module impact claims, semantic conflict resolution, remote publication, or promotion.

## State machine

```text
T0 ROUTE
→ T1 CONTRACT
→ T2 ANCHOR
→ T3 EXPAND
→ T4 SLICE
→ T5 DECOMPOSE
→ T6 DISPATCH
→ T7 VERIFY/REPAIR
→ T8 REVIEW/SELECT
→ T9 STACK/RESTACK
→ T10 HANDOFF
```

Stop states:

```text
ROUTE_ABSENT
SUBJECT_MUTABLE
CONTRACT_AMBIGUOUS
INTERFACE_LOCK_ABSENT
PATH_LEASE_OVERLAP
INDEX_SUBJECT_MISMATCH
INDEX_COVERAGE_UNKNOWN
CONTEXT_PROVENANCE_MISSING
DAG_CYCLE
UNDECLARED_DEPENDENCY
ASSERTION_MUTATION
REPAIR_BUDGET_EXHAUSTED
SEMANTIC_CONFLICT_UNPROVEN
PUBLICATION_NOT_ADMITTED
HUMAN_ADMIT_REQUIRED
```

## T0 — Route

Read the repository's governing documents, current issue/task packet, active acceptance queue, module ownership, Git/forge policy, and nearest README before designing branches. Repository policy can narrow this Skill and can block a branch that would otherwise be valid.

## T1 — Contract first

Freeze the shared design surface before fan-out:

- function/type/API/schema signatures;
- state-management and dependency choices;
- migrations and compatibility rules;
- allowed, read-only, and forbidden paths;
- acceptance tests and negative controls;
- branch role and expected artifact.

Represent interface locks as path plus digest or exact subject reference. A Worker request to change a lock becomes a planner escalation, not a local edit.

## T2 — Resolve intent anchors

Use deterministic exact search when names are known. When the request is conceptual, grepai may propose a small ranked seed set.

```text
natural-language intent
→ grepai candidate seeds
→ current-source readback
→ exact symbol identifiers
```

grepai is an Intent Anchor and optional Serena runtime exploration tool. It is not the call graph, absence oracle, or architecture authority.

## T3 — Expand deterministic impact

For each accepted seed:

1. query the admitted SCIP index for Def/Ref, type, inheritance, call, and implementation relations;
2. persist normalized nodes/edges and index-subject metadata in SQLite;
3. traverse bounded upstream dependencies and downstream callers;
4. attach related tests and manifests;
5. mark unsupported, generated, dynamic, or uncovered areas explicitly.

Use the `EXACT` label only when index commit/tree, indexer identity, build policy, language coverage, and source readback match. The graph is a rebuildable projection, never canonical task state.

## T4 — Slice context

Use Tree-sitter to assemble a context manifest:

```text
target implementation      → full source
immediate dependencies     → imports, types, signatures, docs; bodies omitted
downstream callers         → enclosing call-site nodes and bounded context
related tests              → full assertions or assertion slices
semantic examples          → optional grepai/LanceDB candidates with provenance
```

LanceDB may store AST chunks and embeddings, but its rows remain retrieval candidates. SQLite owns deterministic metadata, graph edges, subjects, and coverage.

## T5 — Decompose the DAG

Create the smallest reviewable nodes that preserve semantic cohesion. Classify every edge:

```text
parallel     no byte or contract dependency; path-disjoint
serial       child consumes an admitted parent contract or implementation
tournament   several Workers implement the same locked contract independently
review       critic observes a branch but does not write its paths
```

Reject a decomposition that creates a cycle, duplicate path writer, hidden shared-file edit, or a node with no independent acceptance oracle.

## T6 — Dispatch prompt packets

Every Worker receives the same contract envelope and one differential focus. Use [fanout-prompt.md](references/fanout-prompt.md).

Recommended tournament focuses:

```text
A  architecture/readability/module boundaries
B  minimal diff/performance/compatibility
C  defensive behavior/edge cases/security
```

Do not broadcast unrestricted repository context. Each prompt packet carries exact subject, context provenance, path lease, read-only locks, test commands, budgets, and stop states.

## T7 — Verify and bounded repair

Inside each isolated Worktree run repository-approved gates in deterministic order, for example:

```text
format/syntax
→ type/compile
→ lint/static/security
→ unit/integration
→ mutation or negative control
→ artifact/residue checks
```

On failure, provide the Worker only the failure signature, relevant diff, locked contract, and allowed paths. Do not send an unbounded transcript. Stop after three materially different repairs of one stable signature.

## T8 — Review or select

For Stack mode, review each node against its own contract before downstream restack. For tournament mode:

1. reject boundary violations and assertion mutations;
2. compare deterministic test and control receipts;
3. compare public-contract compatibility and diff size;
4. choose one base implementation;
5. cherry-pick only independently proven, path-compatible improvements.

Do not splice incompatible architectures merely because each branch contains useful code.

## T9 — Stack and restack

Use Git Town through the repository's admitted adapter and closed command set. A typical topology is:

```text
main
└─ contract/schema
   └─ core implementation
      └─ adapter/API/UI
         └─ integration/E2E
```

Independent path-disjoint work is a sibling, not an artificial child. A child PR targets its parent branch. Restack may be automated only within repository policy and only while semantic conflicts remain absent.

For conflicts:

```text
Git BASE/OURS/THEIRS
→ Tree-sitter node classification
→ deterministic union for safe unordered declarations where allowed
→ bounded semantic candidate for conflicting bodies
→ syntax/type/tests/negative controls
→ Human or repository-owned admission
```

An LLM-produced merge is never self-validating.

## T10 — Handoff

Report exact branches/commits, Stack edges, provider/index subjects, context manifests, changed paths, executed gates and exits, retries, selection rationale, conflicts, residual blindspots, cleanup, rollback identity, and Human-owned next actions.

## Blindspots that must remain visible

- generated code, macros, reflection, dynamic dispatch, runtime registration, and dependency injection;
- incomplete SCIP language/build coverage or an index built for another tree;
- Tree-sitter grammars that parse but do not resolve names or types;
- tests that exist but do not cover the changed behavior;
- two Workers writing different files that still mutate one shared invariant;
- Worktree locks, leaked daemons, ports, caches, databases, and credentials;
- SQLite/LanceDB schema drift and embedding-model drift;
- cross-repository contracts and forge divergence;
- unsafe force-push, stale review bases, and hidden downstream breakage;
- token/time retries that convert uncertainty into cost without new evidence.

## Module law

The portable Skill owns procedure, states, contracts, and evidence ceilings. Modules are provider or delivery adapters selected by trigger. They may add executable invocation details, but may not:

- place product-specific configuration in the core procedure;
- make any optional provider mandatory;
- raise `DEGRADED` to `EXACT`;
- widen path, network, secret, merge, or publication authority;
- store consumer remotes, paths, credentials, mutable indexes, or live receipts;
- replace repository-owned Git/forge policy.

Read [modules/README.md](modules/README.md) and load only the adapters required by the task.

## Executable assertion

Validate a task packet before dispatch:

```bash
python3 scripts/assert_task_contract.py \
  --contract <task-contract.json> \
  --receipt <receipt.json>
```

Exit contract:

```text
0   every implemented hard assertion passed
2   packet was evaluable and one or more hard assertions failed
64  usage/schema/required input invalid or absent
70  assertion mechanism error
```

The receipt proves only the declared packet and implemented assertions. It does not prove provider installation, live indexing, Worker execution, Git Town activation, Forgejo/GitHub state, mergeability, or Human Admit.
