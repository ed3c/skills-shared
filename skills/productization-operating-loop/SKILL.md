---
name: productization-operating-loop
description: |
  Portable method for taking an opportunity from source discovery through
  differentiated design, feasibility, monetization and bounded implementation
  by composing methods that already exist, never restating them. Twelve lanes
  (SOURCE, MARKET, USER, MECHANISM, TECHNICAL, POLICY, RIGHTS, COMMERCIAL,
  RUNTIME, HUMAN_ADMIT, MERGE, RELEASE) are reported separately and never
  fused; a ten-rung evidence ladder refuses substituting a cheaper rung for a
  later one; a fourteen-state program transition with a four-way outcome
  disposition (PRESERVE/NARROW/ITERATE/KILL) refuses reporting only the high
  end of a ladder. A deterministic compiler composes one program plus four
  admitted lane artifacts into six byte-stable documents and refuses eight
  named ways a false promotion could enter one. Concrete markets, users,
  providers, forges, consumer repositories and live receipts are domain
  bindings, never part of this body.
---

# Productization Operating Loop

## Contract

This body owns the twelve-lane vocabulary, the ten-rung evidence ladder and
its substitution law, the fourteen-state program transition with its
four-way terminal disposition, the deterministic composition of a program
plus four lane artifacts into six documents, and the refusals that keep a
bounded measurement from being read as a market, a user, a payment or a
running system.

It does not own market research, user research, pricing, policy reading,
mechanism reverse engineering, session orchestration or delivery. Those are
*composed methods* — named in
[`references/composition-manifest.json`](references/composition-manifest.json)
by content digest and a 400-character-capped declared interface, never by a
pasted body. A method listed there is not thereby admitted as correct,
current or appropriate for a given subject; the manifest records only that
its interface was read at that digest.

The terms are closed in
[`references/core/controlled-vocabulary.md`](references/core/controlled-vocabulary.md);
the ladder and its substitution law are in
[`references/core/evidence-ladder.md`](references/core/evidence-ladder.md);
the machine half is
[`references/productization-program.schema.json`](references/productization-program.schema.json)
and the four Stage-1 lane contracts beside it; the deterministic composer is
[`scripts/compile_pol_composition.py`](scripts/compile_pol_composition.py);
the pasteable per-stage dispatch prompts are
[`prompts/README.md`](prompts/README.md).

## The twelve lanes and the ten rungs (pointer, not restatement)

```text
SOURCE MARKET USER MECHANISM TECHNICAL POLICY RIGHTS COMMERCIAL RUNTIME
HUMAN_ADMIT MERGE RELEASE
```

Twelve lanes, ten lane states (`PASS FAIL UNKNOWN BLOCKED ABSENT
NOT_IMPLEMENTED NOT_EXERCISED SKIPPED_BY_POLICY NOT_APPLICABLE
HUMAN_ADMIT_REQUIRED`), and a ten-rung ladder from `SOURCE_FOUND` to
`REPEATABLE_COMMERCIAL`. Read
[`references/core/controlled-vocabulary.md`](references/core/controlled-vocabulary.md)
before writing a lane; the fourth fact recorded for each lane there — what it
*never becomes* — is the one a paraphrase drops first.

## State machine

```text
REQUEST_BOUND
→ CONTROL_AND_AUTHORITY_BOUND
→ SOURCE_AND_POLICY_BOUND
→ MARKET_ARENA_BOUND
→ USER_SCENARIOS_BOUND
→ COMPARATOR_CASES_BOUND
→ DIFFERENTIATION_WEDGE_BOUND
→ CAPABILITY_AND_RIGHTS_BOUND
→ COMMERCIAL_FRICTION_BOUND
→ MVP_AND_STOP_LOSS_BOUND
→ SHADOW_CLOSURE_AUDITED
→ ISSUE_AND_SESSION_DAG_BOUND
→ BUILD_OR_EXPERIMENT_RUNNING
→ OUTCOME_READ_BACK
→ PRESERVE | NARROW | ITERATE | KILL
```

Fail-closed, at any state: `UNKNOWN`, `BLOCKED`, `NOT_EXERCISED`,
`REPLAN_REQUIRED`, `HUMAN_ADMIT_REQUIRED`. There is deliberately no state
meaning merged, released or in production — those are operations a person
performs, never a program-record value.

## Procedure

Each stage below names the program state it produces. The pasteable dispatch
form of each — exact subject, mandatory `AGENTS.md` route, start/completion
dependencies, lease, evidence lanes, oracles, negative controls, rollback,
stop states, outputs, next owner and Human operations — is in
[`prompts/README.md`](prompts/README.md); this section is the one-paragraph
law each dispatch is bound by, not a second copy of it.

1. **Control binder → `CONTROL_AND_AUTHORITY_BOUND`.** Freeze exact subject,
   evidence ceiling, writer/lease map, stop-loss and Human-owned operations
   before any interpretation. Binding who may write creates no authority to
   write anything in particular.
2. **Source / policy → `SOURCE_AND_POLICY_BOUND`.** Admit each external
   artifact bound to its content digest and read the governing published
   rule directly, at its exact revision. `SOURCE` never becomes `MARKET`,
   `USER` or `TECHNICAL`; `POLICY` never becomes `RIGHTS`.
3. **Market / comparator → `MARKET_ARENA_BOUND`, `COMPARATOR_CASES_BOUND`.**
   Enumerate the arena against named comparator cases. Market attention is
   not demand; a feature difference is not a switching wedge.
4. **User scenarios → `USER_SCENARIOS_BOUND`.** Construct named scenarios and
   their adoption cost. Pain is not willingness to switch; a scenario
   authored is a hypothesis, not a validation.
5. **Differentiation wedge → `DIFFERENTIATION_WEDGE_BOUND`.** Synthesize one
   stated reason to switch against a named comparator and a named switching
   cost. A wedge is the hypothesis `USER` and `COMMERCIAL` exist to test, not
   evidence from either.
6. **Technical / rights capability → `CAPABILITY_AND_RIGHTS_BOUND`.** Answer
   what can be built and what is permitted, separately; `RIGHTS`'s honest
   default is `UNKNOWN` and that is a finding, not a gap to fill.
7. **Commercial friction → `COMMERCIAL_FRICTION_BOUND`.** State the value
   ladder and the friction to buy. Interest is not payment; one payment is
   not a repeatable business.
8. **MVP / stop-loss → `MVP_AND_STOP_LOSS_BOUND`.** Scope the smallest thing
   that tests the wedge and the condition under which it stops. `KILL` is
   available from here, and a program that cannot reach it is not measuring
   anything.
9. **Shadow closure → `SHADOW_CLOSURE_AUDITED`.** An independent, read-only
   pass reviews the compiled closure matrix and its planted controls. Shadow
   reports findings; it does not admit them and does not repair what it
   found.
10. **Tech-lead session DAG → `ISSUE_AND_SESSION_DAG_BOUND`.** Decompose the
    work into atoms with one owner, one lease and one writer each, start and
    completion graphs separate. A dispatch queue is a plan for sessions, not
    execution of one.
11. **Molecular worker → `BUILD_OR_EXPERIMENT_RUNNING`.** A writer works one
    atom inside its own lease and its own Stack branch. Running is not
    finishing.
12. **Outcome foldback → `OUTCOME_READ_BACK` → `PRESERVE | NARROW | ITERATE |
    KILL`.** Read what happened from the thing that happened, not from the
    plan that predicted it, then decide. Reading the outcome and deciding
    what to do about it are separate acts; merging them is how a
    disappointing result becomes `ITERATE` by default.

## Hard laws

Thirteen fused-lane sentences this method exists to refuse (full text and
producer/consumer/never-becomes detail in
[`references/core/controlled-vocabulary.md`](references/core/controlled-vocabulary.md)):

```text
market attention        is not  demand
feature difference       is not  a switching wedge
pain                     is not  willingness to switch
a technical PASS         is not  user validation
user interest            is not  payment
one payment              is not  a repeatable business
policy visibility        is not  rights admission
an external projection   is not  machine authority
a prompt packet          is not  a running session
a bootstrap PASS         is not  agent, model or provider execution
a carrier's UI state     is not  source, work or method truth
a start dependency       is not  a completion dependency
a process dependency     is not  an ancestry edge
```

`references/productization-program.schema.json` enforces the ladder's
substitution law three ways — all ten rungs required, each rung above the
first pinning its predecessor to `REACHED`, one receipt kind per rung — and
enforces none of them for whether a receipt describes anything real; that gap
is what the Shadow stage exists to review.

## Stop conditions

Stop when a lane's fourth fact (what it never becomes) would be violated by
the sentence about to be written, when a rung is claimed without its own
receipt kind, when a wedge, MVP or commercial decision is stated without a
named comparator or a named switching cost, when a Human-owned operation
(rights admission, merge, release, credential or legal exposure) would be
manufactured by accumulation instead of decided by a person, or when
describing the work would put a private locator or a consumer identity into
this portable core. After three qualifying failures against the same
invariant or acceptance target, stop blind repair and open a fresh diagnosis
on a new isolated worktree.

## Evidence ceiling

```text
twelve-lane vocabulary + ladder + state machine   contract-level, schema-enforced
four Stage-1 lane contracts (market/user/commercial/policy)  LANDED, schema + controls replayed
deterministic composition compiler (program + 4 lanes → 6 artifacts)  LANDED, replayed via --selftest
independent evidence/Shadow plane over a composed program   LANDED (ancestor of this tree),
                                                             replayed by the same suite entry
                                                             point — run quoted in AGENTS.md's
                                                             Ancestry note
zero-context read route, stage prompts, trace law (this file, AGENTS.md, prompts/)  LANDED
an actual market read, user observed, mechanism reproduced, MVP built, session run,
payment taken or released product                            NOT_EXERCISED
merge, release, production, legal/rights admission            HUMAN_ADMIT_REQUIRED
```

This body defines how the method may speak and how its stages compose. It
does not establish that any concrete opportunity is attractive, that any user
would switch, that anyone would pay, or that any of this may be merged or
released. Those lanes are reported by this method; they are not cleared by
it.
