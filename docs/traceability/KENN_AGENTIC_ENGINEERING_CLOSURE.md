# Kenn Agentic Engineering closure audit

Date: 2026-08-18

This audit maps the real problems described in Kenn Software's human-led Agentic Engineering workflow to current `skills-shared` mechanisms. It is a source-to-repository closure map, not a claim that Kenn's private production results have been reproduced.

## Shadow Architect verdict

```text
article/source problem
→ shared method owner
→ consumer/runtime owner
→ exact evidence lane
→ closure state
```

A method being documented or a provider being installable does not close a live/runtime problem.

| Real problem | Existing owner | Current closure | Open owner |
|---|---|---|---|
| no-human autonomous loops drift and accumulate slop | Tech Lead + procedural Shadow + Human authority | METHOD_IMPLEMENTED | live consumer evidence remains separate |
| design/taste delegated to Agents | `human-led-agentic-engineering` | METHOD_IMPLEMENTED on this Stack | #392 executable/adoption evidence |
| second opinion is not independent | independent Shadow #232 + Design Adversary split | independent Shadow canary completed; design-specific method added | #392 |
| specs/plans do not encode exact dependencies | `agentic-tech-lead-orchestration` | METHOD_IMPLEMENTED + deterministic contracts | live task families remain subject-scoped |
| parallel Agents collide | Tech Lead leases + Git Town molecular model | METHOD_IMPLEMENTED | #234 real Git Town/dual-forge canary remains open |
| Agent self-report is treated as success | procedural Shadow + deterministic receipts | METHOD_IMPLEMENTED | consumer/runtime evidence remains subject-scoped |
| every commit needs adversarial review | new `ReviewProviderPort` contract | PARTIAL | #393 |
| large branches need whole-branch bug bash/global review | global-objective gate + provider port | PARTIAL | #393 |
| ephemeral specs pollute durable architecture | living-context persistence route | METHOD_IMPLEMENTED | consumer-specific adoption #189 |
| intent is scattered across chat/Markdown | typed queues exist; general IntentLedgerPort missing | PARTIAL | #394 |
| session/token accountability is absent | Shadow evidence exists; normalized observability port missing | PARTIAL | #394 |
| high-throughput delivery needs isolated workspaces/Stack PRs | Git Town worker + dual-forge loop | METHOD_IMPLEMENTED, LIVE DELIVERY PARTIAL | #234 and bettor #189 |
| merge/release must remain accountable to humans | shared Human Admit laws | METHOD_IMPLEMENTED | live Human admission is always external evidence |

## License-safe provider matrix

```text
PERMISSIVE / may be integrated as replaceable adapters
  roborev     MIT
  Kata        MIT
  AgentsView  MIT
  kwt         Apache-2.0

RESTRICTED / external boundary by default
  Kenn Forge  Elastic-2.0
  Ghosthub    AGPL-3.0
```

No restricted provider is required for correctness. Provider absence must select a fallback or stop according to the capability plan; it must not widen authority.

## Canonical workflow after internalization

```text
REQUEST_BOUND
→ HUMAN_DESIGN_ACTIVE
→ independent DESIGN_ADVERSARY_COMPLETE
→ HUMAN_DESIGN_ADMITTED
→ Tech Lead system/capability/task contracts
→ disjoint leased Workers/worktrees
→ COMMIT_CREATED
→ provider review evidence
→ independent/native/domain reconciliation
→ branch-wide/global-objective verification
→ living architecture/context persistence
→ molecular Stack PR delivery
→ HUMAN_ADMIT_REQUIRED
```

## Molecular Stack PR plan

This program uses process and Git dependency separately.

```text
skills-shared

S1 kenn-ae/design-control-plane
   issue: #392
   class: ROOT / TERMINAL METHOD SLICE
   owns: `skills/human-led-agentic-engineering/**`
   provides: Human Design Gate, Design Adversary, provider boundaries, schema/checker

S2 kenn-ae/shared-index-trace
   issue: #392/#393/#394 traceability
   class: TRUE_CHILD / CONVERGENCE-INDEX SLICE
   parent: S1 because it references S1 method bytes
   owns: shared traceability/index documentation only
   provides: closure map and downstream consumer handoff

External evidence/process dependencies:
   #232 independent Shadow canary               HISTORICAL VERIFIED EVIDENCE
   #234 real Git Town + dual-forge canary       PROCESS_DEPENDENCY / OPEN
   #393 commit + branch review provider         PROCESS_DEPENDENCY / OPEN
   #394 intent + observability provider ports   PROCESS_DEPENDENCY / OPEN

bettor-arena

B1 issue #189 consumer binding
   class: independent cross-repository consumer root
   consumes: admitted shared method release/commit, not mutable sibling paths

B2 review / intent / observability provider leaves
   class: SIBLING when path-disjoint

B3 consumer convergence
   class: CONVERGENCE
   sole owner: Bettor shared indexes, aggregate docs and exact consumer closure receipt
```

Cross-repository process dependency is not Git ancestry. Bettor must bind an immutable shared subject before claiming adoption.

## Exit criteria for full article-problem closure

The Kenn-derived program may be called phase-complete only when all of these are separately evidenced:

```text
METHOD_IMPLEMENTED
CONSUMER_MECHANISM_IMPLEMENTED
DETERMINISTIC_EVIDENCE_VERIFIED
LIVE_OR_PHYSICAL_EVIDENCE_VERIFIED where claimed
HUMAN_ADMITTED where required
RELEASED only if an owning release authority actually releases
```

Current phase is **method integration in progress**. #232 is completed evidence, while #234, #392, #393, #394 and Bettor #189 keep later claims open.
