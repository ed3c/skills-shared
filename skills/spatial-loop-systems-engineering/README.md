# spatial-loop-systems-engineering

A portable method for turning kernel-, hardware-, concurrency-, resource-, and
lifecycle-dependent work into a falsifiable system contract before core code is
written.

The Skill uses spatial language to preserve whole-system reasoning, but every
metaphor must resolve to a concrete owner, mechanism, transition, budget, probe,
oracle, or receipt.

## Document authority

| Question | Route |
|---|---|
| Procedure, state machine, gates, and evidence laws | [`SKILL.md`](SKILL.md) |
| Copyable System / Spec Prompt | [`references/system-prompt.md`](references/system-prompt.md) |
| Human-readable and JSON spec packet | [`references/spec-packet-template.md`](references/spec-packet-template.md) |
| Linux namespace/cgroup/seccomp/microVM instance | [`modules/linux-isolation-runtime.md`](modules/linux-isolation-runtime.md) |
| Deterministic contract checker | [`scripts/check_system_contract.py`](scripts/check_system_contract.py) |
| Positive, hollow, and mutation controls | [`evals.json`](evals.json), [`tests/`](tests/) |

## Owned state and data flow

```text
task + exact subject + environment
        ↓
realm / boundary / flow map
        ↓
state machine + hard invariants + resource envelope
        ↓
capability probes + collision matrix + teardown symmetry
        ↓
verification oracles + performance contract
        ↓
spatial-loop-system-contract/v1
        ↓
deterministic closure check
   ┌────┴────────────────────┐
   ↓                         ↓
BLOCKED / PROTOTYPE      READY_FOR_IMPLEMENTATION
   ↓                         ↓
bounded handoff          implementation reconciliation loop
```

`loop-harness-standard` owns generic execution-loop scaffolding.
`truth-verify-loop` owns mutable external-claim verification. This Skill owns
the system-state-space contract that decides what may be implemented and what
may be claimed.

## Directory map

```text
skills/spatial-loop-systems-engineering/
├── README.md
├── SKILL.md
├── evals.json
├── references/
│   ├── README.md
│   ├── system-prompt.md
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
    └── system-contract/
        ├── verify.sh
        └── fixtures/good.json
```

## Evidence boundary

```text
contract structure and gate consistency       IMPLEMENTED
vague-performance refusal                     IMPLEMENTED
required-capability gate                       IMPLEMENTED
teardown/reference closure                     IMPLEMENTED
physical Linux isolation behavior              NOT_EXERCISED
real hardware performance                      NOT_EXERCISED
security or production-readiness claim         HUMAN_ADMIT_REQUIRED
```

The deterministic checker proves that the contract is structurally closed and
internally consistent. It cannot prove that a referenced runtime receipt is
truthful, that the kernel behaves as assumed, or that the system is secure.

## Run the controls

```bash
bash skills/spatial-loop-systems-engineering/tests/run-all.sh
```

A green suite means the good contract is admitted and planted defects are
refused. It does not mean a sandbox, hypervisor, kernel, or hardware target was
executed.
