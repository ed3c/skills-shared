# spatial-loop-systems-engineering

A portable **Constraint-First Spatial Systems Engineering** method that converts incomplete prompts, PDFs, PRDs, diagrams, repository requests, and architecture proposals into a falsifiable executable specification before substantive implementation.

The Skill is no longer substrate-only. It classifies work from Level A local deterministic changes through Level D substrate-sensitive systems, then applies the minimum safe amount of constraint discovery. Level B/C/D work receives full invariant/failure analysis; Level C/D may never silently degrade into ordinary feature-generation behavior.

## Canonical flow

```text
┌──────────────────────────────────────────────┐
│ Universal Constraint-First System Prompt    │
│ how to reason; when direct implementation   │
│ is forbidden                                │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│ User Prompt / PDF / PRD / Diagram / Repo    │
│ what the user wants                         │
└──────────────────────┬───────────────────────┘
                       ↓
              Constraint Compiler
                       ↓
      ┌────────────────┼────────────────┐
      ↓                ↓                ↓
 Domain module     Unknown probes    Hard laws
      └────────────────┼────────────────┘
                       ↓
                Executable Spec
                       ↓
                Implementation
                       ↓
                 Harness / Evals
```

The core transformation is:

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

## Document authority

| Question | Route |
|---|---|
| Universal compiler, complexity classes, hard laws, required outputs, gate, anti-drift | [`SKILL.md`](SKILL.md) |
| Copyable universal System / Spec Prompt | [`references/system-prompt.md`](references/system-prompt.md) |
| Repeated-failure System Prompt overlay | [`references/system-prompt-recovery-overlay.md`](references/system-prompt-recovery-overlay.md) |
| Three-failure issue/fresh-diagnosis/worktree contract | [`references/three-failure-escalation.md`](references/three-failure-escalation.md) |
| Human-readable and JSON spec packet | [`references/spec-packet-template.md`](references/spec-packet-template.md) |
| Triggered domain expansion policy | [`modules/README.md`](modules/README.md) |
| Linux namespace/cgroup/seccomp/microVM specialization | [`modules/linux-isolation-runtime.md`](modules/linux-isolation-runtime.md) |
| Deterministic system-contract checker | [`scripts/check_system_contract.py`](scripts/check_system_contract.py) |
| Positive, hollow, mutation, recovery, and entrypoint controls | [`evals.json`](evals.json), [`tests/`](tests/) |

## Owned state and data flow

```text
source intent / candidate architecture
        ↓
claim classification + complexity A/B/C/D
        ↓
realm / authority / ownership / flow map
        ↓
state machines + Golden Invariants
        ↓
unknown register + probes + failure matrix
        ↓
resource envelope + reconciliation loops
        ↓
verification plan + evidence ladder
        ↓
spatial-loop-system-contract/v1
        ↓
deterministic closure check
   ┌────┴────────────────────┐
   ↓                         ↓
BLOCKED / PROTOTYPE      READY_FOR_IMPLEMENTATION
   ↓                         ↓
probe/spec/handoff       smallest falsifiable implementation
                              ↓
                         Harness / Evals
                              │
                              ├── PASS → handoff
                              ├── FAIL #1/#2 → bounded repair
                              └── qualifying FAIL #3
                                      ↓
                              issue + exact failure packet
                                      ↓
                              fresh diagnosis context
                                      ↓
                              new isolated worktree
                                      ↓
                              repair + owning oracle + negative control
                                      ↓
                              forge-native delivery / Human merge boundary
```

## Domain decoupling

The universal method stays in `SKILL.md`. Domain-specific knowledge stays in `modules/` and is loaded only when triggered.

```text
Universal compiler
    ├── hard-law families
    ├── unknown discovery
    ├── evidence/gate semantics
    └── required output contract
             +
Triggered domain module
    ├── domain realms
    ├── hidden assumptions
    ├── specialized failure vectors
    ├── capability probes
    └── domain-specific oracles
             ↓
       Executable Spec
```

A domain module may extend the core method; it may not replace it, downgrade complexity, redefine evidence states, or bypass the implementation gate.

## Directory map

```text
skills/spatial-loop-systems-engineering/
├── README.md
├── SKILL.md
├── evals.json
├── references/
│   ├── README.md
│   ├── system-prompt.md
│   ├── system-prompt-recovery-overlay.md
│   ├── three-failure-escalation.md
│   └── spec-packet-template.md
├── modules/
│   ├── README.md
│   └── linux-isolation-runtime.md
├── scripts/
│   ├── README.md
│   └── check_system_contract.py
└── tests/
    ├── README.md
    ├── run-all.sh
    ├── universal-entry/
    │   └── verify.sh
    ├── recovery-escalation/
    │   └── verify.sh
    └── system-contract/
        ├── verify.sh
        └── fixtures/good.json
```

## Evidence boundary

```text
universal Constraint-First entry method           IMPLEMENTED
A/B/C/D complexity and anti-degradation law       IMPLEMENTED
domain-extension/decoupling contract              IMPLEMENTED
machine contract structure and gate consistency    IMPLEMENTED
vague-performance refusal                          IMPLEMENTED
required-capability gate                           IMPLEMENTED
teardown/reference closure                         IMPLEMENTED
three-failure escalation routing                   IMPLEMENTED
fresh ChatGPT Desktop session execution            HOST_OPERATOR_BOUND
physical Linux isolation behavior                  NOT_EXERCISED
real hardware performance                          NOT_EXERCISED
security or production acceptance                  HUMAN_ADMIT_REQUIRED
```

The deterministic checker proves structural closure and internal gate consistency. It does not prove that a referenced runtime receipt is truthful or that a designed system is safe.

## Run the controls

```bash
bash skills/spatial-loop-systems-engineering/tests/run-all.sh
```

A green suite means the universal entry laws, good contract, planted defects, and recovery routing controls agree with the repository bytes. It does not mean an external provider, kernel, hardware target, Forgejo mutation, GitHub Actions publication, or Desktop session was physically exercised.
