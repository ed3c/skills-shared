# AGENTS.md — spatial-loop-systems-engineering

This directory owns the portable Constraint-First + Shadow Architecture method and the Intent–Case–Proof Graph (ICPG) contract. Read this file before changing any file under this Skill.

## Read order

1. [`integration/README.md`](integration/README.md) — current #407 closeout/admission state and remaining Local Handoff.
2. [`README.md`](README.md) — portable topology, State Machine, DAG, data flow and evidence ceiling.
3. [`SKILL.md`](SKILL.md) — universal procedure and hard laws.
4. [`references/intent-case-proof-graph.md`](references/intent-case-proof-graph.md) — intent/use-case/edge-case/semantic-preservation contract.
5. [`references/architecture-watch-loop.md`](references/architecture-watch-loop.md) — Shadow Architecture monitor.
6. [`references/spec-packet-template.md`](references/spec-packet-template.md) and machine contracts.
7. [`scripts/check_case_graph.py`](scripts/check_case_graph.py), [`scripts/check_system_contract.py`](scripts/check_system_contract.py), tests and `evals.json`.
8. GitHub issues #407, #408, #409, #410 and #411 plus PR #412 and current exact-head workflows.
9. [`integration/AGENTS.md`](integration/AGENTS.md) before close/merge/handoff work.

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

Current source PR / implementation branch:

```text
PR #412
agent/spatial-intent-case-proof-graph-v1
```

The exact head is mutable; read it from GitHub. PR #513 is a historical temporary current-main refresh carrier only and is not an implementation atom.

Do not manufacture one serial Stack merely to mirror issue numbering. #408 is the contract/core leaf. #409 is a true child when it consumes that contract. #410 may be sibling/convergence by path ownership. #411 is live evidence and is not a Git child unless its harness code consumes unmerged parent bytes.

## Current closeout law

```text
#408  STATIC_CLOSE_CANDIDATE after exact bytes land on main
#409  STATIC_CLOSE_CANDIDATE after main admission; live scope remains #411
#410  STATIC_CLOSE_CANDIDATE after main admission
#411  KEEP_OPEN until an exact independent live Shadow receipt exists
#407  KEEP_OPEN while #411 remains a declared blocking program lane
```

Candidate CI, a temporary branch merge, a compatibility-only PASS, or a Builder self-report cannot satisfy main/live admission. If repository provenance cannot be repaired by the current connector without weakening policy or fabricating identity, use the asserted Tech Lead Local Handoff Queue instead of bypassing the gate.

2026-08-22 state note: the `STATIC_CLOSE_CANDIDATE` condition for #408/#409/#410 is met — bytes admitted on main `5341885f`, receipt `data/handoff/spatial-407/publication-provenance-receipt.json`; closes stay human-owned. #407 was auto-closed by GitHub on 2026-08-21 via a commit-reference close, contrary to the `KEEP_OPEN` law above, and was reopened in the same reconciliation wave; it closes only after #411.

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