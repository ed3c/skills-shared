# spatial-loop-systems-engineering

A portable **Constraint-First Spatial Systems Engineering** method with a monitor-first **Shadow Architecture Control Loop**.

The default operating mode is `MONITOR`: the Builder may explore, design, implement, test, and refactor normally while a separate Shadow Architect watches material System Design deltas, hidden assumptions, evidence drift, and—when Agent Skills are material—procedural grounding drift. `PRECHECK` is reserved for high-risk or irreversible transitions. `POSTMORTEM` reverse-engineers the actual architecture after failure or first-green.

The Skill still classifies work from Level A local deterministic changes through Level D substrate-sensitive systems. Level C/D work may never silently degrade into ordinary feature-generation behavior.

## Canonical flow

```text
Universal Constraint-First System Prompt
        ↓
User Prompt / PDF / PRD / Diagram / Repo
        ↓
Constraint Compiler
   ┌────┼────────┐
   ↓    ↓        ↓
Domain Unknown   Hard laws
module probes
   └────┼────────┘
        ↓
Executable Spec
        ↓
Builder implementation
        ↕
Shadow Architecture Watch Loop
        ├── architecture/evidence deltas
        └── optional Procedural Grounding Shadow Plane
                    ↓
             Harness / Evals
```

The core transformation remains:

```text
WHAT THE USER WANTS
→ WHAT MUST ALWAYS REMAIN TRUE
→ HOW WE CAN KNOW IT REMAINS TRUE

Intent
→ Boundary
→ State
→ Invariant
→ Failure
→ Oracle
→ Evidence
→ Implementation
```

Under `MONITOR`, that transformation can be applied incrementally as implementation reveals architecture deltas instead of blocking harmless exploration up front.

## Operating modes

| Mode | Default? | Purpose |
|---|---:|---|
| [`MONITOR`](modes/monitor.md) | yes | preserve Builder exploration while watching architecture/evidence/procedural drift |
| [`PRECHECK`](modes/precheck.md) | no | gate high-risk or irreversible material transitions before they occur |
| [`POSTMORTEM`](modes/postmortem.md) | no | reconstruct implicit architecture from actual code/runtime/failure evidence |

The monitor contract is [`references/architecture-watch-loop.md`](references/architecture-watch-loop.md). A compact copyable prompt overlay is [`references/system-prompt-monitor-overlay.md`](references/system-prompt-monitor-overlay.md).

## Shadow Architecture intervention

```text
L0 OBSERVE
→ L1 WARN
→ L2 REVIEW
→ L3 BLOCK
```

The Shadow Architect monitors these material deltas:

```text
ASSUMPTION_DELTA
STATE_DELTA
AUTHORITY_DELTA
OWNERSHIP_DELTA
LIFECYCLE_DELTA
CONCURRENCY_DELTA
RESOURCE_DELTA
EXTERNAL_SIDE_EFFECT_DELTA
FAILURE_SURFACE_DELTA
EVIDENCE_DELTA
PROCEDURAL_GROUNDING_DELTA
```

It asks:

```text
What became newly possible?
What must now remain true?
How would we know it is false?
```

The Shadow Architect is not a second implementation writer.

## Procedural Grounding Shadow Plane

When searched, installed, or repository-local Agent Skills materially affect the
task, compose
[`references/procedural-grounding-shadow-plane.md`](references/procedural-grounding-shadow-plane.md).

The plane keeps these states separate:

```text
Skill discovered
≠ procedure mentioned
≠ procedure planned
≠ procedure encoded in the Harness
≠ procedure executed
≠ expected runtime behavior observed
≠ negative control passed
```

It normalizes relevant `SKILL.md` content into source-bound procedure atoms,
computes weighted mention/Harness/execution/evidence coverage, admits bounded
context forks at named checkpoints, and returns only a compact actionable
**Context Capsule** to the parent runtime. Raw private reasoning traces are not a
capsule payload.

```text
Skill search / local discovery
→ source/ref/path/blob/content hashes + trust/rights review
→ procedure atoms + proof modes
→ current uptake observations
→ bounded abstraction fork when useful
→ Context Capsule injection gate
→ assertion/probe/negative-control obligation
→ exact-subject runtime receipt
→ recomputed coverage
```

A critical `EXECUTION_REQUIRED` or `NEGATIVE_CONTROL_REQUIRED` atom cannot pass
through model prose. Unknown or Skill-specific critical procedures require the
smallest satisfied assertion/probe obligation before receipt-level `PASS`.

The machine schema is
[`references/procedural-grounding-receipt.schema.json`](references/procedural-grounding-receipt.schema.json),
and the checker is
[`scripts/check_procedural_grounding.py`](scripts/check_procedural_grounding.py).
Provider/host mappings for skills.sh, Skillsmith, Claude Code, VS Code, Codex, and
Gemini CLI are isolated in
[`modules/agent-host-procedural-grounding.md`](modules/agent-host-procedural-grounding.md).

The plane measures observable behavioral uptake. It does not claim direct access
to model training membership, weights, hidden activations, or private chain of
thought. Attribution requires repeated clean-context trials across
`NO_SKILL`, `METADATA_ONLY`, `FULL_SKILL`, and
`FULL_SKILL_PLUS_GROUNDING`.

## Mandatory checkpoints

```text
SKILL_DISCOVERY when external/retrieved procedures are material
ARCHITECTURE_CHOICE
FIRST_VERTICAL_SLICE
PERSISTENCE_INTRODUCED
ASYNC_OR_CONCURRENCY_INTRODUCED
EXTERNAL_INTEGRATION_INTRODUCED
NOVELTY_OR_DIVERGENCE
FIRST_GREEN
BEFORE_COMMIT when critical procedure proof owns eligibility
BEFORE_PR_OR_PUBLICATION
CI_OR_RUNTIME_FAILURE_WITH_DESIGN_IMPACT
```

`FIRST_GREEN` is intentionally special: passing tests may prove a coded path while leaving implicit assumptions, unexercised runtime behavior, failure states, unreconciled side effects, or ungrounded Skill procedures. Green remains green for its exact evidence subject; it does not automatically mean done.

## Document authority

| Question | Route |
|---|---|
| Universal compiler, modes, complexity, hard laws, gates, anti-drift | [`SKILL.md`](SKILL.md) |
| Base universal System / Spec Prompt | [`references/system-prompt.md`](references/system-prompt.md) |
| MONITOR-mode copyable overlay | [`references/system-prompt-monitor-overlay.md`](references/system-prompt-monitor-overlay.md) |
| Shadow Architecture watch loop | [`references/architecture-watch-loop.md`](references/architecture-watch-loop.md) |
| Procedural uptake/fork/capsule/assertion contract | [`references/procedural-grounding-shadow-plane.md`](references/procedural-grounding-shadow-plane.md) |
| Procedural grounding machine schema | [`references/procedural-grounding-receipt.schema.json`](references/procedural-grounding-receipt.schema.json) |
| Claude/Codex/VS Code/Gemini and discovery-service mapping | [`modules/agent-host-procedural-grounding.md`](modules/agent-host-procedural-grounding.md) |
| Repeated-failure System Prompt overlay | [`references/system-prompt-recovery-overlay.md`](references/system-prompt-recovery-overlay.md) |
| Three-failure issue/fresh-diagnosis/worktree contract | [`references/three-failure-escalation.md`](references/three-failure-escalation.md) |
| Human-readable and JSON spec packet | [`references/spec-packet-template.md`](references/spec-packet-template.md) |
| Triggered domain expansion policy | [`modules/README.md`](modules/README.md) |
| Linux isolation specialization | [`modules/linux-isolation-runtime.md`](modules/linux-isolation-runtime.md) |
| Deterministic system-contract checker | [`scripts/check_system_contract.py`](scripts/check_system_contract.py) |
| Deterministic procedural-grounding checker | [`scripts/check_procedural_grounding.py`](scripts/check_procedural_grounding.py) |
| Regression controls | [`evals.json`](evals.json), [`tests/`](tests/) |

## Owned state and data flow

```text
source intent / candidate architecture
        ↓
complexity A/B/C/D + operating mode
        ↓
Builder exploration / implementation
        ↕
Shadow Architect observes material deltas
        ├── assumptions/state/authority/lifecycle/evidence ledgers
        └── Skill procedure atoms/coverage/fork/capsule ledgers when triggered
        ↓
constraint compiler / domain expansion / unknown probes
        ↓
material-boundary gate when required
        ↓
Harness / Evals
        ↓
checkpoint review, especially FIRST_GREEN and BEFORE_PR
        ↓
PASS / bounded repair / postmortem / three-failure escalation
```

## Domain decoupling

The universal method stays in `SKILL.md`. Host-neutral contracts stay in
`references/`. Domain/provider/host mappings stay in `modules/` and are loaded
only when triggered. Domain modules may extend the core method; they may not
replace it, downgrade complexity, redefine evidence states, bypass a
material-boundary gate, disable architecture monitoring, or manufacture host
capabilities.

## Directory map

```text
skills/spatial-loop-systems-engineering/
├── README.md
├── SKILL.md
├── evals.json
├── modes/
│   ├── monitor.md
│   ├── precheck.md
│   └── postmortem.md
├── references/
│   ├── README.md
│   ├── architecture-watch-loop.md
│   ├── procedural-grounding-shadow-plane.md
│   ├── procedural-grounding-receipt.schema.json
│   ├── system-prompt.md
│   ├── system-prompt-monitor-overlay.md
│   ├── system-prompt-recovery-overlay.md
│   ├── three-failure-escalation.md
│   └── spec-packet-template.md
├── modules/
│   ├── README.md
│   ├── agent-host-procedural-grounding.md
│   └── linux-isolation-runtime.md
├── scripts/
│   ├── README.md
│   ├── check_procedural_grounding.py
│   └── check_system_contract.py
└── tests/
    ├── README.md
    ├── run-all.sh
    ├── architecture-watch/verify.sh
    ├── procedural-grounding/
    │   ├── README.md
    │   ├── verify.py
    │   ├── verify.sh
    │   └── fixtures/valid.json
    ├── universal-entry/verify.sh
    ├── recovery-escalation/verify.sh
    └── system-contract/
        ├── verify.sh
        └── fixtures/good.json
```

## Evidence boundary

```text
monitor-first operating contract                   IMPLEMENTED
Shadow Architecture delta/intervention contract    IMPLEMENTED
FIRST_GREEN meta-review                             IMPLEMENTED
PRECHECK / POSTMORTEM mode contracts               IMPLEMENTED
universal Constraint-First entry method            IMPLEMENTED
A/B/C/D anti-degradation law                       IMPLEMENTED
domain-extension/decoupling contract               IMPLEMENTED
machine system-contract structure/gate consistency IMPLEMENTED
three-failure escalation routing                   IMPLEMENTED
procedural atom/coverage/fork/capsule contract      IMPLEMENTED
procedural-grounding schema/checker                 IMPLEMENTED
procedural positive/hollow/mutation controls        IMPLEMENTED
live continuous Shadow Architect runtime           NOT_EXERCISED
live external Skill search adapter                  NOT_EXERCISED
live Claude/Codex separate context                  NOT_EXERCISED
live separate-model grounding fork                  NOT_EXERCISED
live multimodal browser/device observer             NOT_EXERCISED
four-condition cross-harness attribution            NOT_EXERCISED
fresh ChatGPT Desktop session execution             HOST_OPERATOR_BOUND
physical Linux isolation behavior                  NOT_EXERCISED
real hardware performance                          NOT_EXERCISED
model-weight/private-reasoning introspection        OUT_OF_SCOPE
security or production acceptance                  HUMAN_ADMIT_REQUIRED
```

## Run the controls

```bash
bash skills/spatial-loop-systems-engineering/tests/run-all.sh
```

A green suite proves the checked repository bytes retain the monitor-first laws,
universal entry, machine-contract closure, procedural-grounding fail-closed
rules, and recovery routing. It does not prove that a live agent host continuously
monitored another agent, searched an external Skill registry, created an
independent model context, executed a browser/device observer, ran a real
four-condition eval matrix, exercised an external provider or physical
substrate, or produced a production-safe system.
