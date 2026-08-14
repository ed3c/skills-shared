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
| Base copyable System / Spec Prompt | [`references/system-prompt.md`](references/system-prompt.md) |
| Repeated-failure System Prompt overlay | [`references/system-prompt-recovery-overlay.md`](references/system-prompt-recovery-overlay.md) |
| Three-failure issue/fresh-diagnosis/worktree contract | [`references/three-failure-escalation.md`](references/three-failure-escalation.md) |
| Human-readable and JSON spec packet | [`references/spec-packet-template.md`](references/spec-packet-template.md) |
| Linux namespace/cgroup/seccomp/microVM instance | [`modules/linux-isolation-runtime.md`](modules/linux-isolation-runtime.md) |
| Deterministic contract checker | [`scripts/check_system_contract.py`](scripts/check_system_contract.py) |
| Positive, hollow, mutation, and recovery-routing controls | [`evals.json`](evals.json), [`tests/`](tests/) |

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
                              │
                              ├── PASS → handoff
                              ├── FAIL #1/#2 → bounded retry
                              └── qualifying FAIL #3
                                      ↓
                              ESCALATION_REQUIRED
                                      ↓
                              forge issue + failure packet
                                      ↓
                              fresh diagnosis context
                                      ↓
                              new isolated worktree/branch
                                      ↓
                              repair → owning oracle + negative control
                                      ↓ PASS
                              commit → forge-native PR
                                      ↓
                              existing Human/trusted-operator merge policy
```

Normal repositories with an admitted local Forgejo binding route the escalation
issue and PR through `forgejo-delivery-loop`. GitHub Actions and GitHub-hosted CI
incidents stay on GitHub so workflow/run/job/head evidence remains authoritative
and publication uses `github-delivery-loop`. `git-town-stacked-pr-worker` owns
the portable isolated-worktree/branch method when the consumer admits Git Town.

The intended desktop recovery workflow opens a new ChatGPT Desktop
question/session after the issue packet exists. That is a host/operator step; a
runtime that cannot launch the desktop session must emit a fresh-diagnosis
handoff instead of claiming it ran.

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
    ├── recovery-escalation/
    │   └── verify.sh
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
three-failure escalation routing               IMPLEMENTED
fresh ChatGPT Desktop session execution        HOST_OPERATOR_BOUND
physical Linux isolation behavior              NOT_EXERCISED
real hardware performance                      NOT_EXERCISED
security or production-readiness claim         HUMAN_ADMIT_REQUIRED
```

The deterministic checker proves that the contract is structurally closed and
internally consistent. The recovery routing control proves that the mandatory
three-failure/fresh-context/worktree/forge boundaries are present. Neither can
prove that a referenced runtime receipt is truthful, that a desktop session ran,
that the kernel behaves as assumed, or that the system is secure.

## Run the controls

```bash
bash skills/spatial-loop-systems-engineering/tests/run-all.sh
```

A green suite means the good contract is admitted, planted defects are refused,
and the recovery-routing contract is present. It does not mean a sandbox,
hypervisor, kernel, hardware target, Forgejo mutation, GitHub Actions run, or
ChatGPT Desktop session was executed.
