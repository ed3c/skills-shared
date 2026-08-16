# Tech Lead Task Decomposition

This reference shifts the orchestrator from a single-thread supervisor into a multi-branch Tech Lead. The Tech Lead owns decomposition, contracts, branch topology, writer leases, verification design, blindspot queries, and convergence admission. Workers own one packet and one branch; they do not redesign the whole program while executing it.

## Role separation

```text
User / product intent
        │
        ▼
Tech Lead compiler
  goal graph
  architecture constraints
  contract dependencies
  path leases
  branch/PR topology
  blindspot queries
  evals + negative controls
        │
        ├── Worker A → isolated worktree / branch / PR
        ├── Worker B → isolated worktree / branch / PR
        ├── Worker C → isolated worktree / branch / PR
        └── convergence packet after admitted dependencies

Git Town
  synchronizes the declared branch graph

Human / trusted operator
  semantic conflict resolution, merge, legal acceptance, promotion, rollback
```

The Tech Lead does not spawn arbitrary Agents or execute provider commands through this reference. `scripts/plan_tech_lead_stack.py` compiles a plan into deterministic Worker packets. A consumer runtime decides how to allocate actual Workers after validating the packets.

## Decomposition algorithm

1. Bind one immutable repository commit/tree and the repository's current architecture/Git/eval policy.
2. Convert the request into one goal and a finite set of architecture constraints. Each constraint names its owner tasks and deterministic verification.
3. Identify contracts before files: schemas, interfaces, data formats, state transitions, provider boundaries, and acceptance oracles.
4. Build the dependency DAG from consumed and provided contracts. Do not infer dependency from lexical branch names.
5. Assign each task one writer path lease. Split or serialize any overlap; never let two active Workers own the same path.
6. Choose topology:
   - path-disjoint and no unmerged contract dependency → sibling branches;
   - child consumes an explicit contract from its parent → true child branch;
   - shared index/acceptance after two or more admitted inputs → convergence task;
   - one small isolated change → one branch, no artificial stack.
7. Pre-register required evals and a negative/mutation control capable of turning each important assertion red.
8. Pre-register blindspot queries. Every query includes a discovery/semantic/structural lane and source read-back. LanceDB may be requested only as a projection over another lane.
9. Compile Worker packets, validate with the existing stack contract, then allocate Workers up to the consumer's admitted concurrency limit.
10. Re-plan only through a new plan subject/digest. A Worker cannot silently widen its packet.

## Architecture constraint shape

```json
{
  "id": "sqlite-is-authority",
  "statement": "SQLite owns the durable observation ledger; LanceDB is rebuildable projection only.",
  "enforced_by": ["blindspot-contract", "consumer-binding"],
  "verification": [
    "projection rows reference direct non-vector ledger observations",
    "deleting the projection does not change admission results"
  ]
}
```

A prose constraint without an owner and verification is advisory, not an architecture gate.

## Worker packet shape

The compiler emits the fields already required by `SYSTEM_PROMPT.md` plus:

```text
provided_contracts / required_contracts
architecture_constraints assigned to this Worker
blindspot_queries and readback requirement
parallel_safe_siblings derived from the path/dependency graph
exact subject commit/tree and plan digest
```

Workers may:

- read the admitted subject and required dependencies;
- change only allowed paths;
- run named evals and controls;
- emit source/test/provider receipts;
- propose a PR with the declared parent branch.

Workers may not:

- widen path leases or architecture constraints;
- invent a new parent/branch graph;
- consume sibling unmerged bytes without a new dependency;
- self-admit provider output;
- resolve semantic conflicts unattended;
- merge, publish production, change permissions, or expose secrets.

## Blindspot query planning

A task packet asks questions, not tool invocations:

```json
{
  "id": "auth-boundary",
  "intent": "Find all code paths that admit an authenticated principal before payout execution.",
  "lanes": ["grepai", "scip", "tree-sitter", "serena", "source-readback", "test"],
  "readback_required": true,
  "negative_control": "remove one known authorization edge and require the coverage assertion to fail"
}
```

Recommended lane selection:

- unknown terminology/location → grepai Intent Anchor;
- declaration/reference/implementation impact → SCIP;
- AST shape/slicing/error-node coverage → Tree-sitter;
- symbol-aware diagnostics, edits, or bounded runtime MCP exploration → Serena;
- repeated similarity recall → LanceDB projection linked to SQLite observation IDs;
- every accepted source claim → source-readback;
- behavioral claim → targeted test/runtime observation.

## Parallel scheduling

A scheduler may run tasks together only when:

```text
no dependency path between them
AND no path-lease overlap
AND no shared mutable external resource without an explicit lease
AND concurrency/budget policy admits both
```

Parallelism is a resource decision, not proof of independence. A task that writes an aggregate index, registry, generated lock, migration state, or shared database is usually a convergence owner.

## Prompt envelope

Use this as the high-level Agent instruction after filling the repository-owned plan:

```text
You are the repository Tech Lead compiler, not a single-thread supervisor.

Bind the exact repository commit/tree and read repository policy first. Convert the goal into architecture constraints, contracts, a task DAG, disjoint path leases, required evals, mutation controls, blindspot queries, and a Git Town branch graph. Use sibling branches for independent path-disjoint work. Use a child only when it consumes an explicit unmerged contract from its parent. Create convergence work only after all required inputs are admitted.

For every Worker emit one machine-readable packet with exact subject, goal/non-goals, parent/head branch, allowed/excluded paths, provided/required contracts, assigned architecture constraints, blindspot queries, evals, negative controls, evidence boundary, cleanup, rollback subject, and Human-owned operations. Workers cannot widen their packet, self-admit provider output, resolve semantic conflicts unattended, merge, or promote production.

Treat grepai as fuzzy Intent Anchor and bounded runtime MCP exploration. Treat SCIP as exact only for emitted relations on the pinned indexed subject. Treat Tree-sitter as structural coverage. Treat Serena as the symbol-aware executor. Persist observations/admissions in SQLite. Treat LanceDB as a disposable projection. Require current source read-back and targeted tests before admission.

Compile and verify the plan before any branch, worktree, Agent, provider, or remote mutation. Missing evidence is ABSENT or NOT_EXERCISED, never PASS.
```

## Evidence boundary

A successful plan compile proves the JSON contract, DAG, path-lease checks, true-child rule, blindspot-query shape, packet generation, and deterministic digests for the supplied fixture. It does not prove Git Town ran, a Worker existed, a provider index was healthy, a branch/PR was created, CI passed, or Human Admit occurred.
