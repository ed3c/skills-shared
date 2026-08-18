---
name: product-reverse-engineering-loop
description: |
  Portable procedure for turning evidence-bound product signals into a falsifiable product dossier, a classified mechanism and capability graph, a problem-closure matrix and bounded implementation packets. Every claim carries the grade its evidence supports and every requirement closes only through an oracle in its own lane. Concrete products, capture tools, providers, forges, repositories and live receipts are domain modules and consumer bindings, never part of this body.
---

# Product Reverse Engineering Loop

<!-- PORTABLE_CORE_START -->

## Contract

The core owns the intake grading table, the nine-state transition law, mechanism
classification, capability and rights graph construction, MVP scoping with a
stop loss, problem-closure derivation, executable handoff compilation, and the
prompt-surface contract every stage runs under. Concrete capture tools, product
surfaces, providers, schedulers, forges and repository topology live in
[`modules/domain-profile.md`](modules/domain-profile.md).

Two deterministic mechanisms carry the law:

1. `scripts/check_prel_contract.py` validates any artifact against its schema in
   `references/` and then against the controlled closure vocabulary, emitting one
   named refusal code per violation;
2. `scripts/compile_prel.py` compiles dossier, closure matrix and handoff as pure
   functions of their input bytes, so `--check` byte-compares a committed
   projection instead of trusting that somebody regenerated it.

Structural core/domain separation is a third assertion and substitutes for
neither:

```bash
python3 scripts/check_skill_core_boundaries.py --skill product-reverse-engineering-loop
```

A Markdown route proves reachability. It does not prove a product was observed,
a mechanism reproduces, a user cared, or anyone paid.

## State machine

```text
INPUT_BOUND
→ VERIFIED_BASE_BUILT
→ PRODUCT_JOB_AND_PAIN_BOUND
→ WORKFLOW_AND_MAGIC_MOMENT_BOUND
→ MECHANISM_HYPOTHESES_CLASSIFIED
→ CAPABILITY_AND_RIGHTS_GRAPH_BOUND
→ MVP_AND_STOP_LOSS_BOUND
→ CLOSURE_CONTRACT_BOUND
→ EXECUTABLE_HANDOFF
```

Fail-closed terminals:

```text
BLOCKED_UNGRADED_INPUT
BLOCKED_NO_JOB_HYPOTHESIS
BLOCKED_NO_OBSERVABLE_ORACLE
BLOCKED_RIGHTS_UNADMITTED
BLOCKED_LANE_SUBSTITUTION
BLOCKED_OVERLAPPING_LEASE
BLOCKED_STALE_SUBJECT
```

A terminal is a state, not a failure to report. Every blocked row leaves the
loop as a named remaining item with a named owner.

## Hard laws

- **CORE-LAW-001 — grade before interpretation.** Every input carries a signal
  kind, and the kind alone fixes its grade. A vendor's description of its own
  system is `CLAIMED`, a report is `REPORTED`, and only a recorded observation or
  a completed payment is `OBSERVED`. No stage may raise a grade by arguing about
  the content, and no artifact may carry an observation block for a kind that
  observed nothing.
- **CORE-LAW-002 — a feature list is not a product hypothesis.** Workflow,
  mechanism and capability content may not be bound while job or pain is
  `ABSENT`. Attention is not demand: how loudly a category is discussed measures
  discussion, and a product hypothesis is a claim about who leaves what they
  already use.
- **CORE-LAW-003 — a mechanism without an oracle is not a design input.** A
  mechanism hypothesis is `OBSERVABLE_MECHANISM` only when a procedure exists
  that would show it false. Everything else is recorded as
  `VENDOR_CLAIMED_MECHANISM` or `UNOBSERVABLE_MECHANISM`, stays out of MVP scope,
  and is never deleted — an excluded mechanism that vanishes returns as a
  rediscovery.
- **CORE-LAW-004 — lanes do not substitute.** Deterministic, behavioral, user,
  paid and Human-admit evidence are independent. A requirement closes only
  through an oracle in its own lane. A green suite proves a mechanism reproduces
  and proves nothing about whether anyone wants it; a technical `PASS` offered as
  user or paid validation is refused, because it is the cheapest evidence to
  produce and therefore the one most often reported as progress.
- **CORE-LAW-005 — handoff is executable state, not prose.** Unfinished work
  leaves as packets binding entry condition, exact subject digest, disjoint path
  lease, verification lane, exit condition and successors. Conversation prose,
  a plan someone remembers, or a description of a subject instead of its digest
  is refused.
- **CORE-LAW-006 — edges must be real and writers disjoint.** An edge between
  packets exists only where the successor consumes an artifact the predecessor
  actually produces; path-disjoint work stays sibling work. Two active writers
  may not hold overlapping leases, and a node with more than one incoming
  contract is a convergence with exactly one declared owner.
- **CORE-LAW-007 — prompts reserve authority, they do not grant it.** No surface
  may confer merge, permission, secret or production authority, and every surface
  names the operations it must escalate instead of performing. No surface
  requests private reasoning: asking for reasoning nobody may inspect removes the
  one artifact that could falsify the conclusion.
- **CORE-LAW-008 — the portable core carries no consumer topology.** Consumer
  branches, issues, remotes, machine paths and credentials appear only inside an
  explicitly typed consumer binding. A shared body that names a consumer's
  topology has stopped being shared.

## Procedure

1. **INPUT_BOUND.** Bind the objective, the scope, the refusal codes and the
   evidence ceiling before reading a single signal. A control list written after
   the evidence describes the evidence rather than constraining it. Record which
   lanes this run may speak in and which are owned elsewhere.
2. **VERIFIED_BASE_BUILT.** Bind the signal set against
   `references/product-signal.schema.json` and validate it:

   ```bash
   python3 scripts/check_prel_contract.py --artifact <product-signal.json>
   ```

   The compatibility binding names the producer and the exact fields consumed; a
   field the contract does not define is refused rather than ignored, so a
   producer that drifted is visible here instead of three stages later.
3. **PRODUCT_JOB_AND_PAIN_BOUND.** Compile the dossier and read what the grading
   table actually supported:

   ```bash
   python3 scripts/compile_prel.py --stage dossier --input <product-signal.json> --out <dossier.json>
   ```

   A slot with no admissible signal comes out `ABSENT` and stays `ABSENT`. Fill
   it by collecting a signal, never by writing a sentence.
4. **WORKFLOW_AND_MAGIC_MOMENT_BOUND.** The magic moment is the first point at
   which the observed workflow produces value without manual re-entry. It is
   bound from an observation of a first-value path or it is `ABSENT`.
5. **MECHANISM_HYPOTHESES_CLASSIFIED.** Every mechanism is classified under
   `CORE-LAW-003`. For each `OBSERVABLE_MECHANISM`, record the oracle, its lane,
   and what result would refute it. An oracle whose refutation condition cannot
   be stated is not an oracle.
6. **CAPABILITY_AND_RIGHTS_GRAPH_BOUND.** Capability edges come only from
   declared dependencies in the signal set; an edge nobody declared is invention
   with a diagram around it. Usage and licensing rights are recorded as
   `HUMAN_ADMIT_REQUIRED` — no procedure admits a right.
7. **MVP_AND_STOP_LOSS_BOUND.** Scope contains observable mechanisms plus the
   magic moment, and nothing else. Bind the stop loss as a condition and an
   action before implementation, because a stop loss written after the first
   overrun is a rationalization. An empty scope is refused: there is no small
   version of nothing.
8. **CLOSURE_CONTRACT_BOUND.** Compile the closure matrix and validate it:

   ```bash
   python3 scripts/compile_prel.py --stage closure --input <dossier.json> --out <closure.json>
   python3 scripts/check_prel_contract.py --artifact <closure.json> --input <dossier.json>
   ```

   Compiling an oracle is not running one, so no row arrives closed. A row closes
   only when a consumer records an executed oracle in the row's own lane.
9. **EXECUTABLE_HANDOFF.** Compile the packets, then validate every subject the
   handoff names against current bytes:

   ```bash
   python3 scripts/compile_prel.py --stage handoff --input <closure.json> --out <handoff.json>
   python3 scripts/check_prel_contract.py --artifact <handoff.json> --resolve-subjects <artifact-dir>
   ```

   Packets compiled from one matrix are siblings. Serialize two of them only by
   naming the artifact one consumes from the other, and expect the checker to
   refuse an edge that consumes nothing.

At every stage, run the prompt surfaces from a packet validated against
`references/prompt-packet.schema.json`. The catalogue in
`references/prompt-catalogue.md` explains what each surface exists to refuse;
the packet is the authority.

## Stop conditions

Stop and return the item to its owner when:

- a slot needed by the next state is `ABSENT` and no further signal is available;
- the only oracle for a requirement speaks a different lane;
- a subject digest no longer matches the artifact it names;
- a right is unadmitted and the work would exercise it;
- the same invariant has failed three times — that is a diagnosis problem, and a
  fourth attempt at the same repair buys nothing;
- the next action would need merge, permission, secret or production authority.

## Evidence ceiling

```text
portable procedure and deterministic contracts   PASS by the suite in tests/
mechanism reproduction on a real product         NOT_EXERCISED, consumer-owned
user or paid validation                          NOT_EXERCISED, consumer-owned
product-market fit                               ABSENT, and never a lane this body can enter
live provider or runtime execution               NOT_EXERCISED, consumer-owned
merge, release, promotion, rights                HUMAN_ADMIT_REQUIRED
```

A green suite proves these contracts hold against current repository bytes. It
proves nothing about any product, any user, any market, or any live run.

<!-- PORTABLE_CORE_END -->

## Local verification

```bash
bash tests/run-all.sh
```
