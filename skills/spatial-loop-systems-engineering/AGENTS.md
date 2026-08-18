# AGENTS.md — spatial-loop-systems-engineering

This directory owns the portable Constraint-First + Shadow Architecture method and the Intent–Case–Proof Graph (ICPG) contract. Read this file before changing any file under this Skill.

## Read order

1. [`README.md`](README.md) — current topology, State Machine, DAG, data flow and evidence ceiling.
2. [`SKILL.md`](SKILL.md) — universal procedure and hard laws.
3. [`references/intent-case-proof-graph.md`](references/intent-case-proof-graph.md) — intent/use-case/edge-case/semantic-preservation contract.
4. [`references/architecture-watch-loop.md`](references/architecture-watch-loop.md) — Shadow Architecture monitor.
5. [`references/spec-packet-template.md`](references/spec-packet-template.md) and machine contracts.
6. [`scripts/check_case_graph.py`](scripts/check_case_graph.py), [`scripts/check_system_contract.py`](scripts/check_system_contract.py), tests and `evals.json`.
7. GitHub issues #407, #408, #409, #410 and #411 for the current closure program.

## Case-coverage law

A short prompt is not permission to reduce semantic obligations. For copy/migrate/port/replace/sync/merge/refactor/rewrite work, enumerate every applicable semantic axis and preserve every material source behavior through an explicit disposition.

```text
Prompt / source behavior
→ Intent Atom
→ Semantic Axis
→ Use/Edge Case
→ State Path / Invariant
→ Implementation Owner
→ Oracle / Negative Control
→ Exact-Subject Evidence
```

Runtime state machines may cycle. The provenance graph above must be acyclic.

Every material source behavior ends in exactly one of:

```text
PRESERVE_EXACT
PRESERVE_OBSERVABLE
ADAPT_WITH_COMPATIBILITY
INTENTIONAL_CHANGE
DEFER_EXPLICIT
DROP_EXPLICIT
UNKNOWN_BLOCKING
```

Never use `UNMAPPED`, implicit drop, assumed-irrelevant, or model preference as a terminal disposition. `INTENTIONAL_CHANGE`, `DEFER_EXPLICIT`, `DROP_EXPLICIT`, or an explicit scope reduction require a decision record from an admitted authority/source. `UNKNOWN_BLOCKING` blocks material transition.

## Shadow Architect monitor

The Builder owns implementation mutation. Shadow Architect is read-only with respect to implementation strategy and watches both architecture and case/semantic deltas.

Additional delta classes:

```text
INTENT_INTERPRETATION_DELTA
SCOPE_REDUCTION_DELTA
USE_CASE_DELTA
EDGE_CASE_DELTA
SEMANTIC_PARITY_DELTA
CASE_COVERAGE_DELTA
CASE_ORACLE_DELTA
SOURCE_BEHAVIOR_DISPOSITION_DELTA
```

At every material delta ask:

```text
Which intent/source behavior made this path necessary?
Which case covers it?
Which semantic axis changed?
Which oracle can detect its loss?
Did the change silently narrow scope?
```

`FIRST_GREEN` and `BEFORE_PR_OR_PUBLICATION` must reconcile the current bytes against the case graph. A green compatibility test does not close a semantic-copy obligation.

## Tech Lead handoff

When `agentic-tech-lead-orchestration` is used, task decomposition consumes the admitted case graph rather than only the natural-language prompt.

```text
ICPG
→ architecture invariants / case obligations
→ task contracts
→ true dependency DAG
→ disjoint Worker leases
→ terminal molecular implementation leaves
→ independent oracles
→ convergence owner
→ global objective + case coverage reconciliation
```

Every required case has one implementation owner or one explicit convergence owner. Case dependency is not automatically Git ancestry. A Git Town child exists only when it consumes unmerged parent bytes/contracts.

## Molecular Stack for #407

```text
#407  program / global objective
├─ #408  C/K/E  case schema + semantic checker + migration mutation controls
├─ #409  K/E    Shadow case-delta monitor integration (true child of #408 contract)
├─ #410  D/K    Tech Lead DAG + Git Town molecular traceability (consumes #408 contract; #409 only where monitor bytes are required)
└─ #411  X      live continuous Shadow runtime canary; external/live evidence lane
```

Current implementation branch:

```text
agent/spatial-intent-case-proof-graph-v1
```

Do not manufacture one serial Stack merely to mirror issue numbering. #408 is the contract/core leaf. #409 is a true child when it consumes that contract. #410 may be sibling/convergence by path ownership. #411 is live evidence and is not a Git child unless its harness code consumes unmerged parent bytes.

## Completion gate

Before calling this program closed, report separately:

```text
Intent Coverage
Source Behavior Disposition Coverage
Required Case Coverage
Implementation Binding Coverage
Oracle Coverage
Executed Evidence Coverage
Unknown Blocking Count
```

The deterministic checker can establish exact-byte contract closure only. Live continuous Shadow execution remains `NOT_EXERCISED` until #411 produces an exact-subject receipt. Production/security/Human acceptance remains outside Agent authority.
