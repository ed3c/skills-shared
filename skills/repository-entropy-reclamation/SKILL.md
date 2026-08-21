---
name: repository-entropy-reclamation
description: |
  Evidence-first, cross-language procedure for finding, proving, ranking, and safely removing accidental repository complexity. Use for simplification, dead or duplicated surfaces, mirrored state, speculative abstractions, forwarding-only layers, obsolete compatibility paths, hand-rolled infrastructure, support residue, or abandoned features. Static tools nominate candidates; exact-subject consumer, ownership, history, compatibility, independent Shadow, and verification evidence decide whether a cut is admissible. Language tools, framework registries, product policies, note systems, commands, and live receipts are domain adapters.
---

# Repository Entropy Reclamation

<!-- PORTABLE_CORE_START -->

## Contract

Repository entropy is a fact, state, route, API, layer, package, policy, compatibility branch, test artifact, or lifecycle mechanism the repository must keep coherent without a current load-bearing reason. Optimize for fewer truths, contracts, states, owners, and concepts—not maximum deleted lines.

A scanner, compiler warning, dependency report, search count, or model opinion produces a candidate. Only exact-subject evidence about consumers, dynamic reachability, persistence, trust, ownership, history, compatibility, and decisive verification can admit a change. Finding no safe cut is valid.

## Modes

```text
AUDIT  inspect, classify, prove/reject, rank, report; no mutation
APPLY  select admitted candidates; change one ownership boundary; verify and preserve rollback
```

A reachable capability, public API, persisted format, dynamic entrypoint, or compatibility path is a product decision, not automatic cleanup. Route it to `HUMAN_ADMIT_REQUIRED` unless the exact contract already authorizes the change.

## State Machine

```text
REQUEST_BOUND
→ EXACT_SUBJECT_AND_INSTRUCTIONS_BOUND
→ CONTRACT_BOUNDARIES_CLASSIFIED
→ ENTROPY_SURVEYED
→ CANDIDATES_PROVED_OR_REJECTED
→ INDEPENDENT_SHADOW_REVIEWED
    ├── HOLD / REJECT / HUMAN_ADMIT_REQUIRED
    └── IMPLEMENTATION_ELIGIBLE
→ ONE_OWNERSHIP_BOUNDARY_APPLIED_END_TO_END
→ DECISIVE_CHECK
→ BROAD_GATES
→ RESIDUE_SEARCH
→ GLOBAL_OBJECTIVE
→ IMPLEMENTATION_VERIFIED
→ STACK_OR_LOCAL_HANDOFF
```

`AUDIT_COMPLETE` may terminate after Shadow review. Prose, model agreement, line-count reduction, or an unrelated green test cannot promote a lower state.

## Hard laws

- **ENTROPY-LAW-001 — exact contract before deletion.** Read repository instructions and bind the exact commit/tree. Classify public, persisted, generated, dynamic, compatibility, trust, accessibility, data-loss, quiescence, lifecycle, and internal boundaries.
- **ENTROPY-LAW-002 — scanners nominate; evidence decides.** Tools cannot prove external, string-routed, generated, reflected, serialized, plugin, migration, queue, worker, process, or wire reachability is absent.
- **ENTROPY-LAW-003 — protect load-bearing boundaries.** Never auto-remove authorization, trust validation, accessibility foundations, data-loss prevention, durable compatibility, or cleanup required for resource quiescence.
- **ENTROPY-LAW-004 — reduce truths, not lines.** Remove more concepts, contracts, states, or dependencies than replacement concepts and migration glue add. Moving the same obligation behind a wrapper fails.
- **ENTROPY-LAW-005 — prove consumers and ownership.** Classify every hit as production, non-production, or ambiguous; inspect callers/callees, lifecycle owners, history, and decisions; state the capability effect.
- **ENTROPY-LAW-006 — one ownership boundary per cut.** Remove obsolete declarations, implementations, branches, exports, config, state, dedicated-only tests/docs/examples/generated entries, and dependencies end to end. Preserve tests of surviving observable behavior.
- **ENTROPY-LAW-007 — no-safe-cut is valid.** An empty proven set is stronger than a long speculative list.
- **ENTROPY-LAW-008 — adapters cannot weaken the core.** Domain adapters may add constraints/evidence and reduce effects/authority; never the reverse.
- **ENTROPY-LAW-009 — Shadow is independent and read-only.** It checks applicability, contradictions, global objective, missing consumers/owners, evidence ceiling, denominator, residue, and rollback; it never writes the target.
- **ENTROPY-LAW-010 — delivery edges are causal.** A child consumes named unmerged parent bytes; path-disjoint work remains sibling work; one convergence owner updates shared indexes/evidence.
- **ENTROPY-LAW-011 — evidence lanes do not substitute.** Static, hermetic, cloud, local, private, live/physical, and Human evidence stay separate. A fixture, draft PR, workflow definition, or model statement cannot create a later-lane `PASS`.
- **ENTROPY-LAW-012 — tests/notes are evidence, not untouchable truth.** Keep artifacts that define current contracts or prevent known mistakes; coalesce artifacts that describe only removed mechanics after preserving unique rationale and links.

## Procedure

### 1. Bind subject and instructions

Read nearest `AGENTS.md`, README, architecture/decision records, contribution/test rules, manifests, generated/vendored boundaries, migrations, public packages, and issue/PR. Bind repository, commit, tree, dirty state, allowed effects, rollback, and Human decisions. A branch name or chat description is not an exact subject.

### 2. Establish boundaries

Classify applicable kinds:

```text
PUBLIC_API  PERSISTED_FORMAT  GENERATED_SURFACE  DYNAMIC_ENTRYPOINT
COMPATIBILITY_PATH  TRUST_BOUNDARY  ACCESSIBILITY  DATA_LOSS_GUARD
RESOURCE_QUIESCENCE  LIFECYCLE_OWNER  INTERNAL
```

For each, name owner, paths/symbols/keys, mutation policy, evidence, and smallest observation exposing breakage.

### 3. Survey broadly

Start with central/high-churn production surfaces, not only unused symbols. Candidate classes:

```text
UNCONSUMED_SURFACE  MIRRORED_FACT  SPECULATIVE_GENERALITY
EXTRA_ROUTE_OR_LAYER  LIFECYCLE_DUPLICATION  MISPLACED_DEFENSE
HAND_ROLLED_INFRASTRUCTURE  SUPPORT_ONLY_RESIDUE  ADDED_THEN_ABANDONED
```

Use repository-native search, compiler/linter output, dependency manifests, history, and admitted analyzers. Domain adapters add evidence but preserve the generic record.

### 4. Prove or reject

For each exact symbol, artifact, key, event, wire string, package, or behavior:

1. Search symbols, paths, package/config keys, alternate syntax, event/wire strings, and generated names.
2. Classify hits as `production`, `non_production`, or `ambiguous`.
3. Read call/dispatch paths; inspect reflection, registries, DI, plugins, routes, loaders, serialization, persistence, workers/processes, codegen, and exports.
4. Read history/decisions; record original rationale, whether it survives, and new counterevidence.
5. Map state flags, cancellation, readiness, disposal, queues, and terminal outcomes to lifecycle owners.
6. State `NONE_OBSERVABLE`, `INTENTIONAL_CHANGE`, or `UNKNOWN` capability effect.
7. Estimate removed concepts/contracts/states/dependencies minus replacement concepts/glue.
8. Name the smallest check that must fail if the cut is wrong.

Reject, keep, or escalate when a production/ambiguous consumer exists; dynamic/persisted/compatibility reachability is unproved; rationale still applies; capability changes; churn relocates complexity; dependency replacement adds comparable burden; or confidence is weak/out of scope.

Use `references/entropy-audit.schema.json` plus `scripts/assert_entropy_audit.py`.

### 5. Independent Shadow

Before mutation, compose with `procedural-shadow-runtime` using a public exact-subject packet: subject, boundaries, survey coverage, candidate evidence, capability effects, verification plan, Tech Lead DAG proposal, rollback, and Human boundaries. Shadow returns findings plus `ELIGIBLE_FOR_IMPLEMENTATION`, `HOLD`, `REJECT`, or `HUMAN_ADMIT_REQUIRED`.

### 6. Tech Lead and molecular DAG

Compose admitted cuts with `agentic-tech-lead-orchestration`:

```text
contract freeze → ownership-boundary task → independent controls
→ true DAG/disjoint leases → one convergence owner
→ global-objective assertion → delivery or Local Handoff Queue
```

For publication, compose with `git-town-stacked-pr-worker`:

```text
C contract/schema  K deterministic core  A domain adapter
E Eval/mutation controls  X explicit convergence/E2E  D docs/receipt/handoff
```

Do not serialize path-disjoint atoms. `X` names every parent artifact it consumes.

### 7. Apply one cut

Remove the obsolete contract through declarations, callers, implementations, branches, state, exports, config, dedicated-only tests/docs/examples/generated artifacts, and dependencies. Collapse mirrored state onto the load-bearing representation; do not add a synchronization wrapper. Prefer deletion, then platform/standard library, then an installed dependency. Add a dependency only when obligations removed exceed wrapper, migration, test, documentation, and supply-chain cost.

Preserve unrelated work; never weaken a meaningful check to force deletion.

### 8. Verify and reconcile

After each non-trivial cut:

1. rerun the decisive check;
2. search deleted symbols/strings/paths and stale docs;
3. run relevant type, lint, unit, integration, build, codegen, smoke, persistence, migration, protocol, and quiescence gates;
4. rerun the nominating analyzer;
5. compare public, persisted, dynamic, wire, user-visible, and cleanup behavior;
6. inspect full diff for scope expansion;
7. assert frozen global objective and exact evidence ceiling.

On failure, classify load-bearing candidate, incomplete implementation, or red baseline. Revert/repair the current cut; retain failed attempts in the denominator.

## Domain ports

```text
repository instructions/exact subject
production/non-production/ambiguous corpus classifier
dynamic entrypoint resolver
public/persisted/compatibility policy
trust/accessibility/data-loss/quiescence policy
history/decision provider
language/framework analyzer set
verification carrier
proposal/note destination
consumer receipt store
```

Load `modules/domain-profile.md` only when concrete values are selected. An adapter cannot turn `NOT_EXERCISED` into `PASS`, install itself because a tool exists, or copy mutable consumer state into this core.

## Executable gate

```bash
python3 skills/repository-entropy-reclamation/scripts/assert_entropy_audit.py --audit <audit.json>
python3 skills/repository-entropy-reclamation/scripts/assert_entropy_audit.py --selftest
```

```text
0 pass declared schema/semantic verdict
2 evaluable packet violated a law
64 malformed usage/file/JSON/input
70 validator/schema unavailable or invalid
```

Exit `0` validates the packet; it does not execute commands, delete code, publish, merge, release, or create Human approval.

## Stop and handoff

Stop on dirty/mutable subject, missing instructions, unclassified boundary, production/ambiguous consumer, unproved dynamic/persisted/compatibility reachability, protected boundary, unknown capability effect, weak history/ownership, non-negative conceptual replacement, missing decisive check, Shadow dissent, overlapping leases, false Stack edge, failed global objective, stale receipt, unavailable runtime, semantic conflict, or Human-owned product/merge/release/rollback.

When the next receipt requires another runtime, compile an `agentic-tech-lead-orchestration` Local Handoff Queue with exact subject, runtime/command lane, input/output receipts, cleanup, exit condition, next item, rollback, and Human authority. Queue validation is not execution.

## Source lineage

This procedure generalizes evidence-first simplification ideas from two MIT-licensed upstream sources while removing repository-specific assumptions. Exact pins, mappings, exclusions, and license boundary are in [`references/UPSTREAM_LINEAGE.md`](references/UPSTREAM_LINEAGE.md). No upstream source tree is vendored.

<!-- PORTABLE_CORE_END -->
