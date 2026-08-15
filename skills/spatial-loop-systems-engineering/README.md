# spatial-loop-systems-engineering

A portable **Constraint-First Spatial Systems Engineering** method with a monitor-first **Shadow Architecture Control Loop**.

The default operating mode is `MONITOR`: the Builder may explore, design, implement, test, and refactor normally while a separate Shadow Architect watches material System Design deltas, hidden assumptions, and evidence drift. `PRECHECK` is reserved for high-risk or irreversible transitions. `POSTMORTEM` reverse-engineers the actual architecture after failure or first-green.

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
| [`MONITOR`](modes/monitor.md) | yes | preserve Builder exploration while watching architecture/evidence drift |
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
```

It asks:

```text
What became newly possible?
What must now remain true?
How would we know it is false?
```

The Shadow Architect is not a second implementation writer.

## Mandatory checkpoints

```text
ARCHITECTURE_CHOICE
FIRST_VERTICAL_SLICE
PERSISTENCE_INTRODUCED
ASYNC_OR_CONCURRENCY_INTRODUCED
EXTERNAL_INTEGRATION_INTRODUCED
FIRST_GREEN
BEFORE_PR_OR_PUBLICATION
CI_OR_RUNTIME_FAILURE_WITH_DESIGN_IMPACT
```

`FIRST_GREEN` is intentionally special: passing tests may prove a coded path while leaving implicit assumptions, unexercised runtime behavior, failure states, or unreconciled side effects. Green remains green for its exact evidence subject; it does not automatically mean done.

## Document authority

| Question | Route |
|---|---|
| Universal compiler, modes, complexity, hard laws, gates, anti-drift | [`SKILL.md`](SKILL.md) |
| Base universal System / Spec Prompt | [`references/system-prompt.md`](references/system-prompt.md) |
| MONITOR-mode copyable overlay | [`references/system-prompt-monitor-overlay.md`](references/system-prompt-monitor-overlay.md) |
| Shadow Architecture watch loop | [`references/architecture-watch-loop.md`](references/architecture-watch-loop.md) |
| Repeated-failure System Prompt overlay | [`references/system-prompt-recovery-overlay.md`](references/system-prompt-recovery-overlay.md) |
| Three-failure issue/fresh-diagnosis/worktree contract | [`references/three-failure-escalation.md`](references/three-failure-escalation.md) |
| Human-readable and JSON spec packet | [`references/spec-packet-template.md`](references/spec-packet-template.md) |
| Triggered domain expansion policy | [`modules/README.md`](modules/README.md) |
| Linux isolation specialization | [`modules/linux-isolation-runtime.md`](modules/linux-isolation-runtime.md) |
| Deterministic system-contract checker | [`scripts/check_system_contract.py`](scripts/check_system_contract.py) |
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
        ↓
assumption + state + authority + lifecycle + evidence ledgers
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

The universal method stays in `SKILL.md`. Domain-specific knowledge stays in `modules/` and is loaded only when triggered. Domain modules may extend the core method; they may not replace it, downgrade complexity, redefine evidence states, bypass a material-boundary gate, or disable architecture monitoring.

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
│   ├── architecture-watch-loop.md
│   ├── system-prompt.md
│   ├── system-prompt-monitor-overlay.md
│   ├── system-prompt-recovery-overlay.md
│   ├── three-failure-escalation.md
│   └── spec-packet-template.md
├── modules/
│   ├── README.md
│   └── linux-isolation-runtime.md
├── scripts/
│   └── check_system_contract.py
└── tests/
    ├── run-all.sh
    ├── architecture-watch/verify.sh
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
machine contract structure and gate consistency    IMPLEMENTED
three-failure escalation routing                   IMPLEMENTED
live continuous Shadow Architect runtime           NOT_EXERCISED
fresh ChatGPT Desktop session execution            HOST_OPERATOR_BOUND
physical Linux isolation behavior                  NOT_EXERCISED
real hardware performance                          NOT_EXERCISED
security or production acceptance                  HUMAN_ADMIT_REQUIRED
```

## Run the controls

```bash
bash skills/spatial-loop-systems-engineering/tests/run-all.sh
```

A green suite proves the checked repository bytes retain the monitor-first laws, universal entry, machine-contract closure, and recovery routing. It does not prove that a live agent host continuously monitored another agent, that an external provider or physical substrate ran, or that the resulting system is production-safe.