# repo-agent-native

`repo-agent-native` is the portable procedure for recovering source-anchored repository contracts before brownfield planning or modification.

## Document authority

| Path | Authority |
|---|---|
| [`SKILL.md`](SKILL.md) | portable trigger, workflow, evidence laws, typed output, failure states, and Human boundary |
| [`agents/openai.yaml`](agents/openai.yaml) | Codex-facing display and invocation policy metadata |
| [`modules/`](modules/) | optional trigger-selected capability or methodology modules |
| [`scripts/check_repo_agent_native.py`](scripts/check_repo_agent_native.py) | deterministic structural assertion authority |
| [`tests/verify.sh`](tests/verify.sh) | positive and planted-negative controls for the structural checker |
| [`evals.json`](evals.json) | local index of deterministic and behavioral evals |
| repository binding | consumer routes, providers, versions, commands, policies, output path, and live evidence |
| `evals/cases/repo-agent-native/` | public current/candidate/no-skill/wrong-skill behavior contracts |
| deterministic output verifier | hard-gate authority for the declared output artifact |
| Human Admit | merge, promotion, provider activation, durable-law update, and rollback |

Markdown explains the contract; it does not replace source, tests, receipts, provider health, or Human Admit.

## Mandatory read order

```text
consumer repository entry route
→ consumer repo-agent-native binding
→ this README
→ SKILL.md
→ modules/README.md
→ matching modules only
→ consumer source/tests/receipts
→ evals.json and exact case/verifier
→ exact issue/PR
```

## Directory state machine

```text
PORTABLE PROCEDURE PROPOSED
→ FRONTMATTER VALIDATED
→ CORE LAWS VALIDATED
→ MODULE TRIGGERS VALIDATED
→ RELATIVE REFERENCES CLOSED
→ DETERMINISTIC SELFTEST GREEN
→ BEHAVIOR CASES REGISTERED
→ CONSUMER BINDING VERIFIED
→ PHYSICAL A/B EXECUTED
→ HUMAN ADMIT
```

Failure states include:

```text
NON_PORTABLE_BODY
MISSING_CORE_SECTION
BROKEN_RELATIVE_REFERENCE
MODULE_CONTRACT_INCOMPLETE
DEAD_ASSERTION
EVAL_CLOSURE_BROKEN
CONSUMER_BINDING_ABSENT
PROVIDER_STATE_UNPROVEN
PHYSICAL_AB_NOT_EXERCISED
```

## Data flow

```text
user task / planning request
        │
        ▼
consumer document route and binding
        │
        ▼
portable repo-agent-native procedure
        │
        ├── deterministic source discovery
        ├── optional semantic candidates
        ├── optional symbol candidates
        ├── optional graph-impact candidates
        └── optional memory hints
        │
        ▼
source/document/test/runtime readback
        │
        ▼
structured invariants + negative invariants + implicit dependencies
        │
        ▼
deterministic assertions and behavior verifier
        │
        ▼
plan/spec/refactor handoff + unresolved evidence + Human boundary
```

## Procedure versus modules

`SKILL.md` contains procedural generalization. Modules are optional instances selected by trigger:

- document routing policy;
- semantic candidate retrieval;
- symbol/reference operations;
- graph-impact candidates;
- project or user memory hints;
- deeper extraction and specification methods.

A module cannot override the Skill's evidence laws. A provider module being present does not prove that provider is installed, healthy, current, authorized, or complete.

## Code execution and assertions

The host Agent executes code. This Skill only defines when and why to invoke:

```text
bundled checker
repository test/linter/compiler
consumer binding checker
admitted MCP capability
controlled runtime canary
```

Hard assertions require deterministic exit status and a declared subject. A checklist or model self-review remains advisory. A skipped, unavailable, or no-runner command is not `PASS`.

## A/B evidence

Two layers are deliberately separate:

1. **Static contract A/B** — compare portability, route closure, executable assertions, negative controls, and eval coverage.
2. **Physical model-output A/B** — run the same cases through `current_skill` and `candidate_skill`, alongside `no_skill` and `wrong_skill`, using exact Skill SHAs, fresh workspaces, zero retries, and at least three seeds.

A candidate may advance only when every hard gate is no worse and the admitted aggregate metric improves. Until physical runs exist, report `NOT_EXERCISED` rather than “better.”

## Current evidence

The files in this directory establish the portable procedure and deterministic structural checks. They do not establish any consumer provider's health, source-index freshness, model performance, graph completeness, memory accuracy, or physical A/B result.

## Change contract

A change requires:

- exact procedural law or module trigger changed;
- portability and consumer-impact analysis;
- implementation target and verifier;
- positive, hollow, mutation, and routing controls;
- evidence ceiling and fallback behavior;
- A/B case impact;
- rollback subject;
- exact issue/PR and Human Admit.
