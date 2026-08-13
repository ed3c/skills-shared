# `forgejo-delivery-loop`

`forgejo-delivery-loop` is the portable procedure for binding a materialized micro-loop repository to a **local Forgejo** tracking surface while keeping evidence, routing, mutation, credentials, and Human merge authority separate. Its core procedure lives in [`SKILL.md`](SKILL.md); generic contracts live in [`references/`](references/README.md); operational/domain detail lives in [`modules/`](modules/README.md); deterministic route logic lives in [`scripts/`](scripts/README.md). Consumer-specific line/repository/milestone/issue mappings live in each consumer's `.skill-bindings/forgejo-delivery-loop/registry.json`.

## Read order

1. [`SKILL.md`](SKILL.md) — portable procedure and stop conditions.
2. This README — directory map, state machines, data flow, and evidence boundary.
3. [`references/README.md`](references/README.md) — generic typed request/receipt/outbox contracts.
4. [`modules/README.md`](modules/README.md) — on-demand delivery and Forgejo-operation instances.
5. [`scripts/README.md`](scripts/README.md) and [`cases.json`](cases.json) — deterministic routing and controls.
6. Consumer `.skill-bindings/forgejo-delivery-loop/registry.json` — repo-specific line identities.
7. Exact consumer issue/PR/milestone, local runtime contract, and receipt.

## Directory map

```text
skills/forgejo-delivery-loop/
├── README.md
├── SKILL.md                    procedural method and laws
├── cases.json                  deterministic route cases
├── references/
│   ├── README.md
│   └── contracts.md            generic request/receipt/outbox contracts
├── modules/
│   ├── README.md
│   ├── delivery-mechanism.md   delivery-line and four-layer tracking instance
│   └── forgejo-operations.md   localhost operation/outbox/recovery instance
└── scripts/
    ├── README.md
    └── route.ts                Bun/TypeScript deterministic route selector
```

## Procedural core versus domain instances

```text
SKILL.md
  how to classify, bind, verify, route, stop, and hand off

references/
  reusable generic contract vocabulary

modules/
  detailed Forgejo delivery/operation instances loaded when the task requires them

consumer binding
  exact repository, milestone, issue, artifact, receipt, and local endpoint facts
```

The core does not own a consumer's repository names, issue numbers, local credential, Chrome session, milestone, worktree path, or live receipt.

## State-machine ownership

### Delivery line

Owner: consumer registry + consumer receipt gate, governed by the procedure here.

```text
LINE_UNREGISTERED
→ LINE_REGISTERED
→ ARTIFACT_MATERIALIZED
→ DELIVERY_RECEIPT_VALID
→ FORGEJO_SUBJECTS_BOUND
→ TRACKING_SYNCED
```

Terminals include `UNMATERIALIZED`, missing/invalid receipt, repository identity drift, stale issue/PR/milestone subject, and sync failure. A zero-network receipt check proves shape and identity binding; it does not prove current Forgejo state.

### Deterministic operation routing

Owner: [`scripts/route.ts`](scripts/route.ts) + [`cases.json`](cases.json).

```text
ROUTE_INPUT
→ TARGET/ORIGIN/SCALE/PRECONDITION VALIDATED
→ ACTOR + MODE SELECTED
→ MUTATION_ALLOWED OR FAIL_CLOSED
→ TYPED ROUTE RESULT
```

The Agent does not maintain a parallel routing policy in prose or prompt memory.

### Local Forgejo mutation/outbox

Owner: consumer operator and the contracts explained in `modules/forgejo-operations.md`.

```text
READ_ONLY_PREFLIGHT
→ TYPED_REQUEST
→ IDEMPOTENCY_CHECK
→ REPO_LOCAL_OPERATOR
→ RECEIPT
    ├── success → APPLIED
    └── unavailable/failure → OUTBOX_PRESERVED
→ RECOVERY_REPLAY
```

A local credential helper may supply a credential in memory. Secret values never enter argv, stdout, Git, portable receipts, or this shared Skill. Only admitted `localhost:3000` routes are in scope; external Forgejo, GitHub, and GitLab use separate Skills.

### Merge authority

```text
PR_READY
→ HUMAN REVIEW/ADMIT
→ EXACT SUBJECT RECHECK
→ MERGE BY AUTHORIZED OPERATOR
```

This Skill prepares tracking and evidence. It does not auto-merge, broaden permissions, force-push, rewrite remotes, or resolve semantic conflicts.

## End-to-end data flow

```text
micro-loop implementation
→ materialized repository artifact
→ implementation receipt
→ consumer Forgejo registry line
→ zero-network receipt gate
→ deterministic route selector
→ read-only Forgejo observation
→ typed mutation request when admitted
→ repo-local operator
→ issue/PR/milestone update + receipt
→ Human review/merge
→ new drift/finding becomes a new issue
```

A delivery receipt and a live Forgejo observation are independent arrivals. Neither proxies the other.

## Prompt/context placement

```text
fixed, human-admitted law
  → procedural SKILL.md or consumer normative module

iteration-generated context
  → typed exchange packet / run artifact

emergent finding
  → packet + issue + backlog
  → later fold-in review before any law promotion
```

Emergent content must not be written directly into normative procedure.

## Four-repository integration

```text
skills-shared forgejo-delivery-loop procedure
→ runtime-env Forgejo variable/module/profile/workload/policy contract
→ bettor `.skill-bindings/forgejo-delivery-loop/registry.json`
  + origin/credential canaries
→ Agent Shield or another consumer's repo-local operator and receipts
→ bettor acceptance / Human promotion when applicable
```

A shared procedure, runtime declaration, or consumer registry does not prove a current authenticated Forgejo session or GitHub/Forgejo equivalence.

## Evidence states

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
```

Package/config presence, an authenticated browser in another session, a stale receipt, or another origin cannot produce PASS.

## Change rules

- Change generic procedure in `SKILL.md` only through eval-first governance.
- Change generic contract vocabulary in `references/`.
- Change detailed domain/operation examples in `modules/` without turning them into global passive context.
- Change deterministic routing with `cases.json` and `route.ts` together; run the selftest.
- Keep consumer-specific identities and live evidence in consumer bindings and receipts.
- Never broaden the localhost-only boundary or credential handling to solve one repository incident.
