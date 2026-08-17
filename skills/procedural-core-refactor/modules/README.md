# Domain and proof modules

Modules specialize the portable refactor method for one target Skill or proof family. They do not replace `SKILL.md` laws.

## Selection contract

Every module declares:

```text
module_id
trigger
non_trigger
assumptions
inputs
outputs
predecessor_states
produces_state
executable_owner
receipt_contract
evidence_ceiling
fallback
forbidden_overrides
authority_ceiling
```

Selection is compiled from the frozen refactor contract. A module does not activate because its file exists, a tool is installed, a model prefers it, or a prior run used it.

## Runtime route

```text
frozen target need
→ trigger evidence
→ REQUIRED | OPTIONAL_SELECTED | NOT_APPLICABLE
→ predecessor proof
→ exact module
→ executable owner
→ identity-bound receipt
→ downstream refactor state
```

`NOT_APPLICABLE` produces no invocation receipt. A required module fails closed. An optional fallback must be explicit and cannot raise the evidence state.

## Forbidden overrides

A module may not:

- delete, rename or weaken `PCR-LAW-*`;
- move provider/consumer/runtime authority into portable core;
- rewrite historical treatment bytes;
- hide an old strength or intermediate regression;
- change matched A/B subjects, tests, budgets, carrier or denominator;
- infer invocation from reachability;
- promote static, fixture or synthetic evidence to live PASS;
- suppress failed/stale/dissenting results;
- widen filesystem, network, secret, merge, publication, provider, permission, semantic-conflict, release or promotion authority.

## Module registry

| Module | Trigger | Executable owner | Evidence ceiling | State |
|---|---|---|---|---|
| [`golden-proof-tech-lead.md`](golden-proof-tech-lead.md) | preserve the Agentic Tech Lead old/B0/B1/B2 and production-shaped deterministic proof chain | `scripts/check_refactor_contract.py` | structural `DETERMINISTIC_FIXTURE`; real-task `SYNTHETIC_RUNTIME` | `PASS` for the bounded proof ledger; live lanes remain `NOT_EXERCISED` |

Future target modules must be indexed here before use. Unindexed module files are repository drift, not hidden capability.
