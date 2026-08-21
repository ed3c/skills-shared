# Dual-Track Code Review Loop — traceability index

This directory is the zero-context navigation and Issue/PR traceability
surface for `dual-track-code-review-loop` (`#517` parent, this convergence
`#526`). It indexes the Skill; it does not contain the Skill's contract,
procedure or prompt bodies, which live under
[`skills/dual-track-code-review-loop/`](../../../skills/dual-track-code-review-loop/).

## Directory → owner

```text
docs/traceability/dual-track-code-review-loop/
├── AGENTS.md
│   └── read order, authority boundary, lease law, Shadow L3 blocks (this convergence, #526)
├── README.md
│   └── this file: directory map, DAG, evidence ceiling, current handoff
├── implementation-preflight.json
│   └── historical H0-002 C0-contract admission receipt (#517/#518), superseded
│       by the committed suite for anything the committed suite also covers
├── SESSION_PROMPTS.md
│   └── routing pointer to skills/dual-track-code-review-loop/references/prompts/README.md;
│       does not repeat the prompt bodies
├── ISSUE_DAG.json
│   └── machine-readable DAG over #517-#528 and #547/#549/#550, exact state per issue
├── MOLECULAR_STACK_INDEX.md
│   └── pointer to the Molecular Stack entry in git-town-stacked-pr-worker
└── LOCAL_HANDOFF_EXECUTION_QUEUE.json
    └── remaining open lanes ahead of #528 Local Handoff, in dependency order
```

## State Machine (this convergence)

```text
DOCS_AND_ROUTES_STALE (N-2: directory map predates 16 interface schemas and adapters/)
→ GROUND_TRUTH_VERIFIED_AGAINST_TREE
→ DIRECTORY_MAP_AND_EVIDENCE_CEILING_REPAIRED
→ SESSION_PROMPT_CATALOGUE_COMPILED (P0-P8)
→ TRACEABILITY_PROJECTIONS_WRITTEN (ISSUE_DAG, Molecular Stack, Local Handoff queue)
→ VALIDATORS_GREEN_ON_OWN_EXIT_CODE
→ DTCR_DOCS_PROMPTS_TRACE_READY
```

`DTCR_DOCS_PROMPTS_TRACE_READY` is the only terminal this convergence may
claim. It does not prove a Worker Session ran, bootstrap succeeded, a
consumer closed, or merge/release occurred.

## DAG (issue-level, see `ISSUE_DAG.json` for the machine copy)

```text
#517 DTCR (parent)
 ├─ #518 C0 contract ── admitted (implementation-preflight.json)
 ├─ #519 D1 deterministic fact-plane contracts ── schemas landed; two adapters landed
 │    ├─ adapters/tree-sitter/     LANDED, live receipt
 │    ├─ adapters/sqlite-ledger/   LANDED, planted mutations
 │    ├─ #547 D1-SCIP adapter      BLOCKED_ON_PROVIDER
 │    └─ #549 D1-BUF adapter       BLOCKED_ON_PROVIDER
 ├─ #521 M1 semantic-context plane
 │    └─ #550 M1-C semantic adapter   BLOCKED
 ├─ #522 X1 synthesis/closure compiler   CLOSED (landed and closed via PR #563)
 ├─ #523 R1 single-repo refactor protocol   OPEN (landed in-tree: refactor/ + four contracts, suite-counted; current issue state on GitHub)
 ├─ #524 R2 cross-repo expand & contract     OPEN
 ├─ #525 E1 independent Shadow / mutations / closure denominator   OPEN
 ├─ #526 D2 this convergence (README/AGENTS/prompts/routing/traceability)
 ├─ #527 B1 bootstrap profile for new repositories   OPEN
 └─ #528 L1 live consumer canary / Local Handoff / final admission   OPEN
```

Every edge above is a start/completion dependency, not Git ancestry, unless a
concrete branch actually consumed another branch's unmerged bytes.

## Evidence ceiling

```text
directory map / State Machine / DAG accuracy    VERIFIED_AGAINST_TREE_AT_HEAD
prompt catalogue (P0-P8) existence and routing   PRESENT (this convergence)
schema/contract/vocabulary/refusal-control state  UNCHANGED — see Skill README
adapter landing state (tree-sitter, sqlite-ledger) REPORTED_FROM_COMMITTED_SUITE
open sibling lane state (#525/#547/#549/#550) REPORTED_AS_OPEN, NOT PROMOTED
Molecular Stack index projection                 POINTER_ONLY, see referenced file
private CodexDoc/Google projection routing        OPAQUE_BINDING_ONLY, no private URL
registry admission                                ABSENT
merge, release, production, visibility            HUMAN_ADMIT_REQUIRED
```

## Current handoff

This convergence repairs the Skill's own README/AGENTS/SKILL directory map and
evidence ceiling (previously stale by two landings: the 16 D1/M1 interface
schemas and the two adapters), compiles the P0-P8 prompt catalogue, and writes
this directory's traceability projections. It does not implement `#522`,
`#525`, `#547`, `#549`, `#550`, `#527` or `#528` — those remain open, and their
own Workers own their own evidence. The next owner after this convergence is
whichever of those lanes is picked up next, plus `#525`'s independent Shadow
pass over the Skill contract and adapters this convergence only describes.
