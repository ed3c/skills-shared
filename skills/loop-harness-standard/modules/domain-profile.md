# Loop-harness domain profile

Historical driver, consumer-topology, and provider-specific detail remains recoverable from pre-refactor blob `5f939b42da14491c8d65498fc4ba141836d97824`.

## Trigger
Load when a concrete driver, execution harness, consumer loop topology, seed profile, provider/runtime, or repository layout must be bound.

## Non-trigger
Do not load for generic loop state, attempt budgeting, checkpointing, judge separation, convergence, rollback, or evidence accounting.

## Assumptions
A loop has an explicit objective, state, bounded attempt budget, evaluator/acceptance rule, and observable artifacts.

## Specialization inventory
Named drivers/models, consumer loop directories, repository-specific harness layouts, production seed examples, and provider runtime controls belong here.

## Evidence ceiling
A harness invocation or driver success proves only that invocation; convergence and correctness require the owning evaluator/assertion on the exact subject.

## Fallback
When an optional driver/provider is unavailable, retain the loop state and task packet and use a deterministic/local fallback or return an explicit unavailable state.

## Forbidden overrides
This module may not override `CORE-LAW-001` through `CORE-LAW-005`, remove failures from the denominator, mutate evaluator definitions to obtain green, or widen runtime/secret/merge authority.
