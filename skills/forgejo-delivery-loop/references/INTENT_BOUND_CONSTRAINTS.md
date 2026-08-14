# forgejo-delivery-loop Intent-Bound Constraints

This adapter maps the existing Forgejo routing, preflight, idempotency, outbox
and receipt behavior to stable meta-intents. It reuses `scripts/route.ts`,
`cases.json` and the existing contracts; it does not introduce a second delivery
engine.

## Authority-widening defect this adapter closes

Registration found a hard contradiction between two files that both claimed to
own merge authority:

```text
SKILL.md   merge 永遠人 admit; the loop advances only to an open pull request
route.ts   operation=merge + request_state=admitted
           → forgejo/execute-merge, mutation_allowed=true
cases.json 007-admitted-merge asserted that widening as expected behavior
```

`request_state: "admitted"` means *the typed request* was admitted. It has never
meant that a human admitted the merge. Routing merge through the shared
`execute-*` tail read one signal as the other, and the case file froze the
result into the contract, so the router's own tests agreed with the widening.

Merge is now taken out before that tail and routed to
`forgejo/merge-human-admit-required` with `mutation_allowed: false` under every
request state. `007` is retained as a negative control rather than deleted, so a
future re-widening fails an existing assertion instead of quietly passing.

## Intent map

| Intent | Proof obligation | Deciding lane |
|---|---|---|
| `MI-FJ-IDENTITY` | a route binds the exact platform, repository and line | existing router platform/線 controls |
| `MI-FJ-PREFLIGHT` | no external mutation precedes a read-only precondition check | existing router request-state controls |
| `MI-FJ-IDEMPOTENT` | one admitted request produces at most one side effect | idempotency marker plus outbox receipt |
| `MI-FJ-EVIDENCE` | routing state is not read back as live Forgejo state | exact readback receipt |
| `MI-FJ-HUMAN` | merge, permission widening and publication stay Human-owned | router merge control plus Human admit |

## Existing evaluator registration

```text
scripts/route.ts selftest()
  cases.json 001-009b  routed positive arms
  cases.json 007       merge authority negative control
  cases.json 010-018   not-applicable platform arms
  arm-balance guard    >= 5 cases per trigger/polarity arm
```

The router owns deterministic routing only. It cannot decide whether a live
Forgejo session exists, whether a remote side effect actually landed, or whether
a semantic conflict was resolved correctly. Those lanes stay `NOT_EXERCISED` or
`HUMAN_ADMIT_REQUIRED`.

## Repair loop

```text
mechanical routing break
→ affected intent and case ID
→ repair the route, not the case expectation
→ re-run the router selftest and the merge-authority sweep

authority or semantic ambiguity
→ BLOCK
→ HUMAN_ADMIT_REQUIRED
```

A repair may not delete a negative control, relax `mutation_allowed`, or edit a
case expectation so that a widened route passes.

## Evidence boundary

```text
deterministic routing contract     IMPLEMENTED
merge authority negative control   IMPLEMENTED
intent/constraint closure          IMPLEMENTED by repository-wide checker
live Forgejo session               NOT_EXERCISED
external mutation / readback       NOT_EXERCISED
publication recovery               NOT_EXERCISED
semantic conflict, merge, release  HUMAN_ADMIT_REQUIRED
```

Offline routing tests prove what the router decides. They prove nothing about a
live Forgejo instance, and a green router is not evidence that any external
operation occurred.
