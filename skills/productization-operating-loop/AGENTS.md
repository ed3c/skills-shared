# AGENTS.md — productization operating contract

Read this file before dispatching a stage prompt, before recording a program's
lane or rung state, and before using this method's output to justify a
market, user, commercial, rights, merge or release claim.

## Mandatory read order

1. repository root `AGENTS.md`, `README.md`, `CONTEXT.md` and architecture
   routes;
2. this `AGENTS.md`;
3. this directory's [`README.md`](README.md);
4. [`SKILL.md`](SKILL.md);
5. [`references/core/controlled-vocabulary.md`](references/core/controlled-vocabulary.md)
   and [`references/core/evidence-ladder.md`](references/core/evidence-ladder.md);
6. [`references/productization-program.schema.json`](references/productization-program.schema.json)
   and [`references/composition-manifest.json`](references/composition-manifest.json);
7. whichever Stage-1 lane contract the change touches —
   [`references/market/market-lane.schema.json`](references/market/market-lane.schema.json),
   [`references/user/user-lane.schema.json`](references/user/user-lane.schema.json),
   [`references/commercial/commercial-lane.schema.json`](references/commercial/commercial-lane.schema.json),
   [`references/policy/policy-lane.schema.json`](references/policy/policy-lane.schema.json)
   — beside its own vocabulary file;
8. the three [`references/session/`](references/session/) schemas and
   [`scripts/compile_pol_composition.py`](scripts/compile_pol_composition.py)
   before editing or invoking the composer;
9. [`prompts/README.md`](prompts/README.md) before authoring or dispatching a
   Session prompt for any stage;
10. [`modules/README.md`](modules/README.md), whichever module a concrete
    consumer binding requires;
11. the composed method this stage consumes — see
    [`references/composition-manifest.json`](references/composition-manifest.json)
    for the current list, each linked from the matching stage prompt;
12. [`../product-reverse-engineering-loop/AGENTS.md`](../product-reverse-engineering-loop/AGENTS.md)
    before restating anything from its problem-closure or session-dispatch
    surface — that Skill is a separate predecessor/consumer route this
    convergence routes to and never copies;
13. the exact issue, pull request, commit and tree subject.

Chat history, a branch name, an issue title, a scanner's output and model
agreement are not evidence substitutes.

## Agent roles

### Stage Worker (stages 0-11)

Owns one stage's exact subject binding, its lane or session artifact, its
oracle and negative controls, and its handoff to the next owner. A Stage
Worker may not promote its own output past the rung its own receipt kind
earns, may not fuse two lanes into one sentence, and may not treat a start
dependency as satisfied by anything short of a readable interface or a
completion dependency as satisfied by anything short of an admitted receipt.
Full per-stage binding is in [`prompts/README.md`](prompts/README.md).

### Independent Shadow (stage 8 — Shadow closure)

Read-only, on the same immutable subject as the compiled
`pol/closure-matrix/v1`, with no writer lease and no repair authority.
Independently attacks:

```text
a lane artifact its own frozen contract would refuse, composed anyway
a receipt's own subject_commit carried into the ladder uncompared
a compiled document re-read without noticing a downstream edit
a lane cleared above its own ladder rung
a cleared cell resting on a lane that reached no rung
a skipped lane or a dropped failed attempt left out of the denominator
market attention, feature delta, pain, interest, one payment or a
  subscription reported as demand, wedge, switch intent, validation,
  repeatability or entitlement
a prompt packet, bootstrap PASS or external projection reported as a
  running session, provider execution or machine authority
stale policy, source or receipt reused past its own revision
```

Shadow outputs findings plus `ADMIT_FOR_DOWNSTREAM`, `BLOCK` or
`REPLAN_REQUIRED`. A same-context review may warn and can never satisfy this
role. Shadow's own procedure and mutation-proof method belong to
[`../procedural-shadow-runtime/`](../procedural-shadow-runtime/README.md);
this Skill only binds the exact subject Shadow reviews.

### Human (every stage)

Rights admission, merge, release, credential or confidential-data expansion,
independent-reviewer identity, MVP `KILL` and every outcome disposition are
decided by a person and recorded on the record. No lane state, rung, replay
count or green suite may be accumulated into one of these.

## CodexDoc / GitHub trace law

Prose law only. No consumer identity, live routing table or credential lives
in this portable core.

```text
source / REF / revision
→ claim / opportunity / requirement
→ issue DAG
→ PR / head / receipt, when implementation exists
→ external projection request
→ Google Doc / Sheet / CodexDoc read-back receipt
```

An external projection is never source, implementation, user, paid, merge or
release authority — it is one more thing to be read back and compared. This
chain binds to two frozen schemas: a projection request is one entry in
`prel/external-projection-registry/v1` (`external_kind` one of `DOCUMENT`,
`SPREADSHEET`, `CODEX_DOC`, `SLIDE_DECK`, `WIKI_PAGE`; `authority` pinned
false throughout; `read_back.compared_revision` and `read_back.compared_digest`
are `null` until an independent read-back actually ran), owned by
[`../product-reverse-engineering-loop/`](../product-reverse-engineering-loop/README.md),
and the foldback decision at the far end is `pol/outcome-foldback-request/v1`,
whose `read_back_questions` require at least one question and whose
`decision` field is emitted empty on every compilation — a person, not this
chain, writes it. Nothing in this law authorizes wiring a live Google API,
CodexDoc client or GitHub webhook from this directory; that is a consumer
binding, never part of the portable core.

## Writer and mutation laws

- One writer per program instance; path leases are disjoint per composed
  method and per Stage-1 lane.
- A doc-convergence change (this file, `README.md`, `SKILL.md`,
  `modules/**`, `prompts/**`) may describe a landed contract's or compiler's
  status and evidence ceiling. It may never edit `references/**`,
  `scripts/**`, `tests/**`, `evals.json` or `cases.json` — those are
  separate frozen leases (`POL-C0`/`M`/`U`/`B`/`P`/`K`/`E`, each its own
  issue and receipt).
- No consumer identity (a named external repository, carrier or program
  instance) may appear inside this directory. A consumer binds this method
  from its own repository and its own lease; naming one here would make
  every other consumer a special case of the first.
- A module under `modules/` may narrow this contract — add evidence,
  strengthen a constraint, reduce authority. It may not relax a lane, a rung
  or an authority constant; a module that does is a fork wearing an
  extension's name.
- Do not weaken a schema, a refusal control, a test or an evidence
  requirement to make a stage's output land.

## Ancestry note — read before quoting any suite line

"Landed in the repository" and "landed in *this* branch's history" are two
different facts, and this convergence exists partly because that distinction
was collapsed twice in the prior wave. State both, always:

- The four Stage-1 lane contracts (`POL-M`/`U`/`B`/`P`, `#423`-`#426`) and the
  deterministic composer (`POL-K`, `#427`) are ancestors of this directory's
  current tree. `tests/run-all.sh` in this worktree replays them and printed,
  on this run: `POL-SELFTEST-GREEN 8 positive instances validate, 49 controls
  refused, 49 of 49 discriminating under knockout of their own named
  keyword`. `scripts/compile_pol_composition.py --selftest` in this worktree
  printed: `POL-COMPILE-GREEN 6 artifacts byte-stable across two compilations
  and one reordering, validated against 6 committed contracts, 8 refusal
  codes fired by 12 crafted inputs`.
- The evidence plane (`POL-E`, `#428`) exists in this repository at commit
  `b7f69e0f9a2c5a0dcfb6a413f745d51a588315c3` — its own receipt claims
  `tests/evidence_plane.py`, `cases.json`, `evals.json`, a widened
  `tests/run-all.sh` (invoking the compiler and the plane in the same entry
  point) and a 97→100 skill-eval-claim count, all verified against that
  commit by its own worker. That commit is **not an ancestor of this
  worktree's `HEAD`**: it landed on a sibling worktree branch that this
  convergence's mandatory base merge did not include. Concretely, in
  *this* tree: `tests/run-all.sh` still only calls `tests/selftest.py` and
  prints only the `POL-SELFTEST-GREEN` line above; `tests/evidence_plane.py`
  and `cases.json`/`evals.json` for this Skill do not exist on disk here at
  all (the `POL-COMPILE-GREEN` line above came from invoking
  `scripts/compile_pol_composition.py --selftest` directly, not from
  `run-all.sh`, and no `POL-PLANE-GREEN` line can be produced in this tree
  by any command); and `scripts/check_skill_eval_plane.py` prints the
  pre-`#428` count, `97 runnable claim(s) across 12 skill(s)`.
- Do not resolve this by pasting `#428`'s suite line into a transcript this
  tree cannot reproduce. Resolve it by fast-forwarding or merging
  `b7f69e0f9a2c5a0dcfb6a413f745d51a588315c3` into whatever branch admits this
  convergence, then re-running `tests/run-all.sh` and replacing this note
  with what that run actually prints.
- [`../../docs/traceability/productization-operating-loop/README.md`](../../docs/traceability/productization-operating-loop/README.md)'s
  "Current states" table and method-composition list were frozen at `#421`
  prep time and now understate progress on `POL-C0` through `POL-E` (all
  merged or landed since); its "Planned directory ownership" tree is the one
  this convergence fulfils. That file is outside this lease — routing it to
  current reality is the shared-index reconciliation this convergence hands
  off, not a repair this convergence performs.

## Required dispatch packet

```text
exact stage and program subject (commit/tree)
lease (this directory's own path lease, or the composed method's own)
evidence lanes touched and the rung, if any, each stage may raise
start dependencies, satisfied_by READABLE_INTERFACE, separately from
completion dependencies, satisfied_by ADMITTED_RECEIPT
oracle and negative controls for this stage
rollback subject (base_commit)
Human-owned operations this stage cannot discharge
next owner
```

A field with no answer is `ABSENT`. Do not infer one.

## Stop conditions

Stop when a lane's fourth fact (what it never becomes, per
`controlled-vocabulary.md`) would be violated by the sentence about to be
written, when a rung is claimed without its own receipt kind, when a
Human-owned operation would be manufactured by accumulation, when a consumer
identity would have to enter this portable core for the work to be
describable, or when a suite line would have to be quoted from a commit that
is not this worktree's own ancestor. After three qualifying failures against
the same invariant or acceptance target, stop blind repair and open a fresh
diagnosis on a new isolated worktree.

## Evidence ceiling

`ROUTING_PROMPT_TRACE_CONVERGENCE`. This directory establishes a zero-context
read route, pasteable stage prompts and the CodexDoc/GitHub trace law as
prose. It does not establish that `POL-E`'s evidence plane is an ancestor of
any particular branch (see the ancestry note above), that a market is
attractive, that a user would switch, that anyone would pay, that a rule
permits anything, that any session ran, or that any of this may be merged or
released.

## Completion report

Report the exact base and head commit and tree, the complete changed-path
denominator (restricted to this lease), every suite command actually run in
this worktree with its exit code and its literal printed line, which
predecessor receipts were read versus independently re-verified here, the
ancestry status of every predecessor commit named above, the `#373` /
Product Reverse reconciliation state as read (not as assumed), the docs/
traceability drift left for the shared-index owner, the rollback subject, and
the Human-owned operations that remain.
