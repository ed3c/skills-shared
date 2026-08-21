# Productization Operating Loop — zero-context Session prompts

These are the substantive prompt bodies for this Skill's twelve stages. They
are owned by this directory's lease and are never copied into
[`../../../docs/traceability/productization-operating-loop/`](../../../docs/traceability/productization-operating-loop/README.md) —
that directory holds a routing pointer to this file plus the `#421`
preparation history, not a second copy of a stage prompt. Every Session must
re-bind exact subjects against current repository state before execution;
none of these prompts grants runtime, merge, provider, rights, user or
Human-owned authority. A rung is raised by the compiler reading a receipt of
its own kind, never by a sentence in a prompt asserting one — an input that
asserts a rung is `K08_RUNG_PROMOTED_ABOVE_RECEIPTS`
(`../scripts/compile_pol_composition.py`).

## Common system envelope

```text
ROLE: <stage worker>
TASK_ID: <program_id / issue id>

READ FIRST:
root AGENTS.md → README/CONTEXT/ARCHITECTURE → ../AGENTS.md (this Skill) →
../README.md → ../SKILL.md → ../references/core/controlled-vocabulary.md +
evidence-ladder.md → the lane/session schema this stage touches → the
composed method's own SKILL.md/README.md, if any → ../modules/domain-profile.md
for BIND values → exact Issue/PR/program-instance subject.

BIND:
- exact program subject: program_id, subject_commit, subject_tree, and the
  rollback base_commit;
- one writer, one lease — a consumer-owned path per ../modules/domain-profile.md,
  never a path under skills/productization-operating-loop/;
- start_dependencies (satisfied_by READABLE_INTERFACE) kept separate from
  completion_dependencies (satisfied_by ADMITTED_RECEIPT) — reading an
  interface is never a substitute for the receipt that closes it;
- the lane(s) this stage may report and which lane state each is allowed to
  reach (never PASS on human_admit/merge/release);
- which rung, if any, a receipt from this stage could feed into the ladder,
  and that only the compiler's own computation may raise it;
- evidence ceiling for this stage, oracle, negative controls;
- the repeated-failure stop-loss (three qualifying failures against the same
  invariant stops blind repair and opens a fresh diagnosis on a new
  worktree);
- output artifact/path and next owner.

HARD LAWS:
market attention != demand; feature difference != a switching wedge; pain !=
willingness to switch; a technical PASS != user validation; user interest !=
payment; one payment != a repeatable business; policy visibility != rights
admission; an external projection != machine authority; a prompt packet !=
a running session; a bootstrap PASS != agent, model or provider execution; a
carrier's UI state != source, work or method truth; a start dependency != a
completion dependency; a process dependency != an ancestry edge. All ten
rungs are required and monotone — a rung reached with a gap below it is a
validation error, not a shortcut.

HUMAN/EXTERNAL ONLY:
rights/legal admission, credential or confidential-data expansion, merge,
release/promotion, production rollback, MVP `KILL`, and every outcome
disposition (`PRESERVE`/`NARROW`/`ITERATE`/`KILL`).

OUTPUT:
exact subjects, the lane/rung state(s) this stage actually reached, every
check command run with its own exit code, the complete lane report
(including lanes nothing entered), rollback subject, remaining Human/
external lanes, and next-owner handoff. Never persist a private document URL
or credential — an external projection carries an opaque id and a revision,
nothing else.
```

## Stage 0 — Control / Authority Binder

```text
ROLE: POL Control Binder.
Freeze the exact program subject, evidence ceiling, per-stage writer/lease
map, stop-loss and Human-owned operations before any interpretation begins.
Read ../modules/domain-profile.md and bind every value it lists, or record it
ABSENT — do not default a Human-admission contact. Emit
CONTROL_AND_AUTHORITY_BOUND only. Do not read a source, enumerate a market,
construct a scenario, scope an MVP or choose a remedy from this stage.

SUBJECT        a pol/productization-program/v1 instance: program_id,
               subject_commit, subject_tree, rollback.base_commit
ROUTE          ../AGENTS.md -> ../SKILL.md ->
               ../references/productization-program.schema.json ->
               ../modules/domain-profile.md
START DEPS     none (first stage of a new program)
COMPLETION DEPS none; this stage produces the interface every later stage's
               start dependency reads
LEASE          consumer-owned program-instance path
EVIDENCE LANES none entered; this stage binds authority and lease only
ORACLE         the produced instance validates against
               productization-program.schema.json at CONTROL_AND_AUTHORITY_BOUND
NEGATIVE CONTROLS  an authority constant set true; an empty
               human_owned_operations array; a lane state written before its
               lane is entered
ROLLBACK       rollback.base_commit named in the produced instance
STOP STATES    BLOCKED (writer/lease conflict), REPLAN_REQUIRED (subject not
               yet resolvable)
OUTPUTS        program instance at CONTROL_AND_AUTHORITY_BOUND
NEXT OWNER     Stage 1 (Source / Policy)
HUMAN OPS      confirm the named writer actually holds the stated lease;
               name the Human-admission contact — this stage may not default one
```

## Stage 1 — Source / Policy

```text
ROLE: POL Source and Policy Auditor.
Admit each external artifact as a source packet bound to its content digest,
never to a path, using the composed discovery/verification methods
(unknown-discovery-composer, dr-research-loop, truth-verify-loop). Read the
governing published rule directly, at its exact revision, into the POLICY
lane. SOURCE never becomes MARKET, USER or TECHNICAL; POLICY never becomes
RIGHTS.

SUBJECT        SOURCE and POLICY lane state in the bound program instance
ROUTE          ../references/core/controlled-vocabulary.md (SOURCE, POLICY) ->
               ../references/policy/policy-lane.schema.json + vocabulary.md ->
               ../../unknown-discovery-composer/SKILL.md,
               ../../dr-research-loop/SKILL.md,
               ../../truth-verify-loop/SKILL.md
START DEPS     CONTROL_AND_AUTHORITY_BOUND readable
COMPLETION DEPS a SOURCE receipt (SOURCE_LOCATED or, once independently
               read back, SOURCE_VERIFIED) and a POLICY record whose
               terminal is CURRENT
LEASE          consumer-owned source/policy artifact paths
EVIDENCE LANES SOURCE, POLICY. A SOURCE_VERIFIED receipt may feed the
               SOURCE_FOUND -> SOURCE_VERIFIED rungs; asserting either rung
               without that receipt is K08_RUNG_PROMOTED_ABOVE_RECEIPTS
ORACLE         independent read-back against the primary artifact, not a
               summary of it; policy-lane.schema.json's own terminal field
NEGATIVE CONTROLS  confidence, repetition or internal consistency of a
               source read as market/user/technical truth; a policy answer
               reused after its revision changed (K01_STALE_LANE_ARTIFACT at
               the compiler if it is)
ROLLBACK       rollback.base_commit
STOP STATES    BLOCKED (source unreachable), UNKNOWN (policy ambiguous or
               contested)
OUTPUTS        SOURCE_AND_POLICY_BOUND
NEXT OWNER     Stage 2 (Market/Comparator) and Stage 3 (User Scenarios), and
               the RIGHTS half of Stage 5
HUMAN OPS      RIGHTS stays a separate, honestly-UNKNOWN lane; policy
               visibility here is never rights admission
```

## Stage 2 — Market / Comparator

```text
ROLE: POL Market and Comparator Worker.
Enumerate the arena and its participants against named comparator cases. Use
product-reverse-engineering-loop's MECHANISM signals as comparator-case
input where a competitor's mechanism must be reproduced to be compared
honestly; never let its output be read as MARKET demand.

SUBJECT        MARKET lane state and comparator-case set
ROUTE          ../references/market/market-lane.schema.json + market-vocabulary.md ->
               ../../product-reverse-engineering-loop/README.md (MECHANISM
               signals feeding comparator cases)
START DEPS     SOURCE_AND_POLICY_BOUND readable
COMPLETION DEPS a MARKET lane receipt (COMPARATOR_CASE_TRACE) naming
               specific comparator cases
LEASE          consumer-owned market artifact path
EVIDENCE LANES MARKET (and MECHANISM, where product-reverse-engineering-loop
               is actually invoked). A COMPARATOR_CASE_TRACE may feed
               WEDGE_SUPPORTED once Stage 4 synthesizes it; this stage alone
               does not raise that rung
ORACLE         market-lane.schema.json's comparator-case shape; named cases,
               not a described arena
NEGATIVE CONTROLS  market attention read as demand; feature delta read as a
               switching wedge; one success case generalized into a
               universal law (the three controls POL-M's own contract
               refuses)
ROLLBACK       rollback.base_commit
STOP STATES    NOT_EXERCISED (no comparator reachable), BLOCKED
OUTPUTS        MARKET_ARENA_BOUND, COMPARATOR_CASES_BOUND
NEXT OWNER     Stage 4 (Differentiation Wedge), alongside Stage 3
HUMAN OPS      none beyond Stage 0's standing lease/authority checks
```

## Stage 3 — User Scenarios

```text
ROLE: POL User Scenario Worker.
Construct named scenarios — the job being attempted and what adoption would
cost the person attempting it. A scenario authored here is a hypothesis
about a user; only an observed user is evidence about one.

SUBJECT        USER lane state and named scenario set
ROUTE          ../references/user/user-lane.schema.json +
               user-lane-vocabulary.md
START DEPS     SOURCE_AND_POLICY_BOUND readable (runs in parallel with
               Stage 2, per the Parallel Session division named at #421)
COMPLETION DEPS a USER lane receipt (JOB_EVIDENCE_TRACE) with adoption cost
               stated per scenario
LEASE          consumer-owned user artifact path
EVIDENCE LANES USER. A JOB_EVIDENCE_TRACE may feed JOB_SUPPORTED; it never
               feeds USER_VALIDATED, which requires an observed real person,
               not a fixture
ORACLE         user-lane.schema.json's scenario shape; traced evidence for a
               job, not a plausible story
NEGATIVE CONTROLS  pain read as switch intent; interest read as adoption;
               the buyer assumed to be the user by default (POL-U's own
               three refused controls)
ROLLBACK       rollback.base_commit
STOP STATES    NOT_EXERCISED, BLOCKED
OUTPUTS        USER_SCENARIOS_BOUND
NEXT OWNER     Stage 4 (Differentiation Wedge)
HUMAN OPS      none beyond Stage 0's standing lease/authority checks
```

## Stage 4 — Differentiation Wedge

```text
ROLE: POL Wedge Synthesizer.
Synthesize one stated reason somebody would move, expressed against a named
comparator (Stage 2) and a named switching cost (Stage 3). A wedge is the
hypothesis USER and COMMERCIAL exist to test; it is never read as evidence
from either lane.

SUBJECT        the differentiation wedge statement
ROUTE          ../references/core/controlled-vocabulary.md
               (DIFFERENTIATION_WEDGE_BOUND)
START DEPS     MARKET_ARENA_BOUND, COMPARATOR_CASES_BOUND and
               USER_SCENARIOS_BOUND all readable
COMPLETION DEPS one wedge statement naming its comparator case and its
               switching cost, both traceable to Stage 2/3 receipts
LEASE          consumer-owned wedge artifact path
EVIDENCE LANES none newly entered; this stage synthesizes across MARKET and
               USER without raising either lane's state on its own
ORACLE         the named comparator case and switching cost each resolve to
               a Stage 2/3 receipt, not to prose invented at this stage
NEGATIVE CONTROLS  a wedge asserted as USER or COMMERCIAL evidence rather
               than as the hypothesis those lanes test
ROLLBACK       rollback.base_commit
STOP STATES    BLOCKED (comparator or scenario set empty), REPLAN_REQUIRED
OUTPUTS        DIFFERENTIATION_WEDGE_BOUND
NEXT OWNER     Stage 5 (Technical/Rights) and Stage 6 (Commercial Friction)
HUMAN OPS      none beyond Stage 0's standing lease/authority checks
```

## Stage 5 — Technical Capabilities (+ Rights)

```text
ROLE: POL Capability and Rights Worker.
Answer what can be built and what is permitted, separately. RIGHTS's honest
default is UNKNOWN, and UNKNOWN here is a finding, never a gap silently
filled from TECHNICAL, POLICY or RUNTIME.

SUBJECT        TECHNICAL feasibility read and RIGHTS lane state
ROUTE          ../references/core/controlled-vocabulary.md (TECHNICAL,
               RIGHTS) -> Stage 1's POLICY record -> a person with authority
               to admit or refuse RIGHTS
START DEPS     DIFFERENTIATION_WEDGE_BOUND readable
COMPLETION DEPS a feasibility read (not yet an MVP build — that is Stage 7)
               and an explicit RIGHTS state, UNKNOWN admitted as a real
               answer rather than left implicit
LEASE          consumer-owned capability/rights artifact path
EVIDENCE LANES TECHNICAL, RIGHTS. Neither rung on the ladder (MVP_TECH_VERIFIED,
               etc.) is reachable from this stage alone — that requires
               Stage 7's deterministic execution
ORACLE         a stated capability claim traces to a concrete mechanism or
               component, not to a green suite standing in for it
NEGATIVE CONTROLS  RIGHTS derived from POLICY, TECHNICAL or RUNTIME rather
               than admitted by a person; a technical read stated as user or
               commercial validation
ROLLBACK       rollback.base_commit
STOP STATES    HUMAN_ADMIT_REQUIRED (RIGHTS unresolved), BLOCKED
OUTPUTS        CAPABILITY_AND_RIGHTS_BOUND
NEXT OWNER     Stage 6 (Commercial Friction), then Stage 7 (MVP/Stop-loss)
HUMAN OPS      RIGHTS admission itself
```

## Stage 6 — Commercial Friction

```text
ROLE: POL Commercial Friction Worker.
State the value ladder and the friction to buy as pricing hypotheses; only a
real transaction, not a quote or a stated intent, moves the ladder past this
stage.

SUBJECT        COMMERCIAL lane state
ROUTE          ../references/commercial/commercial-lane.schema.json +
               vocabulary.md
START DEPS     DIFFERENTIATION_WEDGE_BOUND readable (may run alongside
               Stage 5)
COMPLETION DEPS a COMMERCIAL lane receipt stating the value ladder and the
               buy friction
LEASE          consumer-owned commercial artifact path
EVIDENCE LANES COMMERCIAL. A real transaction may later feed PAID_VALIDATED
               (Stage 10/11 territory); this stage records the hypothesis
               only and does not claim that rung
ORACLE         commercial-lane.schema.json's friction/ladder shape
NEGATIVE CONTROLS  interest read as payment; one payment read as
               repeatability; a consumer subscription read as an API
               entitlement (POL-B's own three refused controls)
ROLLBACK       rollback.base_commit
STOP STATES    NOT_EXERCISED, BLOCKED
OUTPUTS        COMMERCIAL_FRICTION_BOUND
NEXT OWNER     Stage 7 (MVP/Stop-loss)
HUMAN OPS      none beyond Stage 0's standing lease/authority checks
```

## Stage 7 — MVP / Stop-loss

```text
ROLE: POL MVP and Stop-loss Scoper.
Scope the smallest thing that could test the wedge, using dr-to-mvp, and
state the condition under which it stops before any build begins. KILL is
available from here and is a real outcome, not a failure of this method.

SUBJECT        MVP scope and stop-loss condition
ROUTE          ../../dr-to-mvp/SKILL.md
START DEPS     CAPABILITY_AND_RIGHTS_BOUND and COMMERCIAL_FRICTION_BOUND
               both readable
COMPLETION DEPS an MVP scope, a stop-loss condition, and — only once a named
               command actually ran against an exact commit and exited zero
               — a DETERMINISTIC_COMMAND_EXIT receipt
LEASE          consumer-owned MVP-scope artifact path
EVIDENCE LANES TECHNICAL. A DETERMINISTIC_COMMAND_EXIT receipt may raise
               MVP_TECH_VERIFIED; it never raises LIVE_WORKFLOW_VERIFIED,
               USER_VALIDATED or anything commercial
ORACLE         the named command's own exit code, on the exact commit named
NEGATIVE CONTROLS  a green suite on synthetic input reported as anything
               beyond MVP_TECH_VERIFIED
ROLLBACK       rollback.base_commit
STOP STATES    KILL (legitimate program terminus from here), BLOCKED
OUTPUTS        MVP_AND_STOP_LOSS_BOUND
NEXT OWNER     Stage 8 (Shadow Closure)
HUMAN OPS      the KILL decision itself, if taken here
```

## Stage 8 — Shadow Closure

```text
ROLE: POL Independent Shadow Auditor.
Read-only, on the same immutable subject as the compiled
pol/closure-matrix/v1, with no writer lease and no repair authority. Attack
the list in ../AGENTS.md's Independent Shadow section in full. Output
findings plus ADMIT_FOR_DOWNSTREAM, BLOCK or REPLAN_REQUIRED. A same-context
review may warn and can never satisfy this role.

SUBJECT        pol/closure-matrix/v1, compiled by
               ../scripts/compile_pol_composition.py --artifact closure-matrix
ROUTE          ../AGENTS.md (Independent Shadow section) ->
               ../../procedural-shadow-runtime/README.md
START DEPS     MVP_AND_STOP_LOSS_BOUND readable, plus a compiled
               closure-matrix instance readable
COMPLETION DEPS Shadow findings recorded, plus one of ADMIT_FOR_DOWNSTREAM,
               BLOCK, REPLAN_REQUIRED
LEASE          none; read-only, no writer lease
EVIDENCE LANES cross-lane audit only; Shadow clears no lane itself
ORACLE         planted-control knockout against the closure matrix (see
               ../AGENTS.md's attack list — a lane cleared above its own
               ladder rung, a receipt's subject_commit uncompared, a
               skipped lane or dropped attempt left out of the denominator)
NEGATIVE CONTROLS  Shadow admitting its own findings; Shadow repairing what
               it found; a same-context pass standing in for an independent
               one
ROLLBACK       rollback.base_commit
STOP STATES    BLOCK, REPLAN_REQUIRED
OUTPUTS        SHADOW_CLOSURE_AUDITED
NEXT OWNER     Stage 9 (Tech-Lead Session DAG)
HUMAN OPS      admitting Shadow's BLOCK/REPLAN_REQUIRED verdict into a repair
               plan, if one is warranted
```

## Stage 9 — Tech-Lead Session DAG

```text
ROLE: POL Tech-Lead Session DAG Worker.
Decompose the shadow-audited program into atoms with one owner, one lease
and one writer each, using agentic-tech-lead-orchestration. Keep
start_edges and completion_edges separate; a process dependency is not a
Git-ancestry edge. This stage names product-reverse-engineering-loop's own
prel/session-dispatch-request/v1 as the packet shape it dispatches into —
that schema stays owned there and is read, never copied, here.

SUBJECT        pol/session-dag/v1 and the prel/session-dispatch-request/v1
               packets it wraps
ROUTE          ../../agentic-tech-lead-orchestration/README.md ->
               ../../product-reverse-engineering-loop/README.md (session-
               dispatch-request schema, a separate owned surface)
START DEPS     SHADOW_CLOSURE_AUDITED readable
COMPLETION DEPS an atom DAG compiled to lifecycle_state LAUNCH_REQUESTED,
               observed_sessions still null (a dispatch queue is a plan for
               sessions, not execution of one)
LEASE          consumer-owned DAG/dispatch artifact path
EVIDENCE LANES RUNTIME lane not yet entered; this stage only plans it
ORACLE         session-dag.schema.json's own graph shape:
               K05_HIDDEN_DEPENDENCY (an edge naming an atom outside the
               graph) and K06_OVERLAPPING_WRITER_LEASE (two packets
               claiming the same path) both fire at the compiler
NEGATIVE CONTROLS  a dispatch queue read as execution; a process dependency
               read as an ancestry edge
ROLLBACK       rollback.base_commit
STOP STATES    K05_HIDDEN_DEPENDENCY, K06_OVERLAPPING_WRITER_LEASE (both
               compiler refusals), BLOCKED
OUTPUTS        ISSUE_AND_SESSION_DAG_BOUND
NEXT OWNER     Stage 10 (Molecular Worker)
HUMAN OPS      admitting the writer/lease map before any atom starts
```

## Stage 10 — Molecular Worker

```text
ROLE: POL Molecular Worker.
One atom, one Stack branch, one delivery receipt, using
git-town-stacked-pr-worker inside its own molecular-index traceability, with
dual-forge-repository-loop reconciling forge state where two forge planes
are in play. Merge is never a state this method reaches — every gate green
is the condition somebody merges under, not the merge.

SUBJECT        one dispatched atom and its Stack branch
ROUTE          ../../git-town-stacked-pr-worker/README.md ->
               ../../dual-forge-repository-loop/README.md
START DEPS     ISSUE_AND_SESSION_DAG_BOUND readable, this atom's own writer
               lease admitted
COMPLETION DEPS BUILD_OR_EXPERIMENT_RUNNING actually observed (a writer
               really working, or an experiment really live) plus that
               atom's own delivery receipt
LEASE          this atom's own declared path lease (git-town-stacked-pr-
               worker's own lease law, not restated here)
EVIDENCE LANES RUNTIME. A LIVE_WORKFLOW_TRACE receipt from an observed run
               may raise LIVE_WORKFLOW_VERIFIED; a dispatched-but-unobserved
               run raises nothing
ORACLE         the atom's own delivery receipt plus the Stack's own CI
NEGATIVE CONTROLS  a bootstrap PASS read as agent, model or provider
               execution; a running writer's own claim of "done" standing in
               for the delivery receipt
ROLLBACK       rollback.base_commit, plus this atom's own Stack rollback
               subject
STOP STATES    BLOCKED_CONFLICT, BLOCKED_ANCESTRY, FAILED_TOOL (git-town-
               stacked-pr-worker's own Worker State Machine terminals)
OUTPUTS        BUILD_OR_EXPERIMENT_RUNNING
NEXT OWNER     Stage 11 (Outcome Foldback)
HUMAN OPS      merge and release themselves, always
```

## Stage 11 — Outcome Foldback

```text
ROLE: POL Outcome Foldback Worker.
Read what actually happened from the thing that happened — RUNTIME, USER and
COMMERCIAL observation — not from the plan that predicted it. Compile
pol/outcome-foldback-request/v1 with at least one read_back_question
answered, then hand the empty `decision` field to a person. Reading the
outcome and deciding what to do about it are separate acts; do not fold them
into one.

SUBJECT        pol/outcome-foldback-request/v1
ROUTE          ../references/session/outcome-foldback-request.schema.json
START DEPS     BUILD_OR_EXPERIMENT_RUNNING observed (not merely dispatched)
COMPLETION DEPS every read_back_question answered from an observed
               RUNTIME/USER/COMMERCIAL receipt; `decision` still `""`,
               `decided_by` still null, until a person writes one of the
               four `available_decisions`
LEASE          consumer-owned outcome artifact path
EVIDENCE LANES RUNTIME, USER, COMMERCIAL — read back only, no lane cleared
               by this stage's own authority
ORACLE         each read_back_question's answer traces to an observed
               receipt, not to the read_back's own prior expectation
NEGATIVE CONTROLS  reading the outcome and deciding folded into one act; a
               disappointing result silently defaulting to ITERATE; a
               technical PASS substituted for USER_VALIDATED or
               PAID_VALIDATED anywhere in the read-back
ROLLBACK       rollback.base_commit
STOP STATES    HUMAN_ADMIT_REQUIRED (decision pending)
OUTPUTS        OUTCOME_READ_BACK -> one of PRESERVE | NARROW | ITERATE | KILL
NEXT OWNER     PRESERVE/NARROW/ITERATE route back to Stage 0 of the next
               program; KILL closes this program. If this was the first
               admitted method instance, the disposition also feeds the
               shared-index/new-consumer-onboarding stage this method does
               not itself own.
HUMAN OPS      the disposition decision itself
```
