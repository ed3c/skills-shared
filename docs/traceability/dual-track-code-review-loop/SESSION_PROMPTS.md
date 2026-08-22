# Dual-Track Code Review Loop — Session prompt routing

The substantive common envelope and the nine zero-context stage prompts
(P0 through P8) are authored and owned in
[`skills/dual-track-code-review-loop/references/prompts/README.md`](../../../skills/dual-track-code-review-loop/references/prompts/README.md).
This file is a routing pointer, not a second copy — a copy here would drift
independently of the Skill's own lease the first time either one is edited.

## Mandatory AGENTS multi-hop route

Every Session dispatched against this Skill resolves through the same route,
regardless of which stage prompt it carries:

```text
consumer root AGENTS
→ immutable skills-shared binding
→ dual-track-code-review-loop AGENTS.md
→ README.md
→ SKILL.md
→ applicable module/contract/schema/adapter
→ exact consumer Issue/PR/receipt
→ private capability resolver only when authorized
```

Public tracked files on this route — including this one — know only opaque
binding IDs and resolver-variable names. They never echo a private document,
Sheet, folder or source URL. A prompt packet or dispatch request is
`LAUNCH_REQUESTED`, never `SESSION_OBSERVED`; only an actual returned Session
receipt is observation evidence.

## Private projection transaction

Where a stage's output is projected into a private tracking surface (a
Google Doc, Sheet, or CodexDoc), the transaction shape is fixed and one-way
from GitHub's perspective:

```text
private intent delta
→ redacted technical promotion request
→ GitHub Issue/contract
→ exact technical implementation/receipt
→ private Google Doc/Sheet projection request
→ revision/read-back/digest receipt
```

Projection success is not GitHub task completion, and GitHub technical state
is not private strategic truth. Neither direction substitutes for the other;
a revision digest on the private side proves only that the private side was
written and read back, and a merged PR proves only that GitHub's own state
advanced.

## Stage index (see the Skill file for the full text of each)

```text
P0  control/authority binder                      #517 (OPEN), #518 (CLOSED)
P1  source/claim/rights auditor
P2  contract/schema compiler
P3  deterministic fact-plane Worker                #519 (OPEN), #547 (OPEN), #549 (OPEN)
P4  semantic-context Worker                        #521 (OPEN), #550 (OPEN)
P5  bounded execution controller                   #523 (single-repo, CLOSED) | #524 (cross-repo, OPEN)
P6  independent Shadow auditor                     #525 (OPEN)
P7  convergence/bootstrap controller               #526 (CLOSED), #527 (OPEN)
P8  live-canary/Local-Handoff controller            #528 (OPEN)
```

The `(OPEN|CLOSED)` tags are the live GitHub states re-queried per issue on
2026-08-22; re-query gh before trusting them, exactly as `ISSUE_DAG.json`'s
authority note requires.

P5 compiles two mode-specific variants under one stage contract
(`SINGLE_REPO_REFACTOR` and `CROSS_REPO_EXPAND_CONTRACT`); it is not a tenth
State Machine stage. Read the Skill's own `references/prompts/README.md` for
every packet's exact subject, non-goals, leases, dependencies, controls,
commands, outputs, rollback and stop conditions before dispatching a Session.
