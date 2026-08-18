# Dual-Agent offload: portable method contract

Owner of this directory: the two schemas here and
[`../../tests/dual-agent-offload-contract/verify.py`](../../tests/dual-agent-offload-contract/verify.py),
which is the only executable authority over their semantics.

## What this is

A local agent and a remote agent doing one piece of work is two independent
execution lanes with two independent evidence lanes. This directory freezes the
smallest portable vocabulary that keeps them apart, so every later
implementation lane inherits the same words instead of inventing its own.

```text
LOCAL_INTENT_BOUND
→ DATA_CLASSIFIED
→ AUTHORITY_AND_EFFECTS_DECLARED
→ REQUIRED_RUNTIME_CONTRACTS_DECLARED
→ OFFLOAD_HANDOFF_FROZEN
```

- `method-contract.v1.schema.json` — the portable method: data classes,
  side-effect classes, evidence lanes, the authority map, the failure
  distinctions that must stay separable, and the logical runtime contracts an
  implementation plane must satisfy.
- `handoff-requirements.v1.schema.json` — one exact subject bound to one frozen
  method contract, with start-readiness and completion-readiness in separate
  arrays.
- `example-method-contract.json` — positive fixtures `P1` (public read-only
  cloud monitoring), `P2` (local-only analysis with zero egress) and `P3`
  (reversible write under Human admission, effect ledger and compensation).
- `example-handoff-requirements.json` — positive fixture `P4`: a cross-plane
  handoff whose runtime digests are all unresolved, so its verdict is
  `BLOCKED_BY_RUNTIME_CONTRACT` and not `PASS`.

## What this is not

This is the Instruction / Method Plane. It declares that five logical runtime
contracts must exist and what they must mean:

```text
runtime-env/dual-agent/offload-job/v1
runtime-env/dual-agent/capability-grant/v1
runtime-env/dual-agent/effect-intent/v1
runtime-env/dual-agent/artifact-manifest/v1
runtime-env/dual-agent/execution-receipt/v1
```

It does not define their wire shapes. Those belong to the Runtime Contract
Plane, and two repositories defining one interface makes drift certain rather
than possible. `verify.py` enforces that in two places: every declared contract
must name the Runtime Contract Plane as its owner, and no file in this
directory may claim one of those five names as its own `$id` or
`schema_version`.

Nothing here executes. Transport, scheduler, worker, provider, browser
fallback, external effect, artifact, user outcome, merge, promotion and release
remain `NOT_IMPLEMENTED` or `NOT_EXERCISED`, and a portable packet that claims
`PASS` on any lane is refused.

## Hard laws the checker enforces

1. Local and cloud are independent execution and evidence lanes; a lane is
   closed by its own observation or not at all.
2. Transport acknowledgement is not workflow, task, Gate, effect, artifact,
   user or release success.
3. At-least-once delivery is assumed, so an observable write needs both an
   idempotency key and an effect ledger, plus a declared compensation path.
4. `LOCAL_ONLY` material, secret values, sessions and host paths never enter a
   remote packet or a portable receipt.
5. A Worker executes and observes. Canonical task state, Gate verdicts and
   every Human admission have exactly one other owner each.
6. An interface capability and a browser fallback are separate evidence
   classes.
7. Shared document, vector and memory projections are advisory, never
   transaction authority.
8. Provider and model names are adapter choices; naming one in the portable
   core is refused.
9. Start-readiness never closes a completion edge.
10. A method contract cannot claim that a required runtime wire schema exists
    or passes.

## Controls

Sixteen pre-registered controls `M01`–`M16` are registered in
[`../../cases.json`](../../cases.json) and executed by `verify.py`. Each one
mutates a document that stays schema-valid, and the checker asserts that
schema-validity before accepting the kill — otherwise a parser complaint would
stand in for the law, and the law could be deleted without anything turning
red.

Run it:

```sh
bash skills/agentic-tech-lead-orchestration/tests/dual-agent-offload-contract/verify.sh
```
