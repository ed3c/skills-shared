# `forgejo-delivery-loop/scripts/`

Owner: deterministic portable mechanisms for the shared procedure.

## `route.ts`

Inputs: a typed route request describing target, operation scale, local/external origin, preconditions, and admission state. Machine cases: [`../cases.json`](../cases.json).

Outputs: a typed actor/mode/mutation decision or a fail-closed rejection. The router does not authenticate, mutate Forgejo, read consumer secrets, choose issue scope, or perform merge.

```bash
bun run skills/forgejo-delivery-loop/scripts/route.ts --input route-input.json
bun run skills/forgejo-delivery-loop/scripts/route.ts --selftest
```

Change `route.ts` and `cases.json` together. Missing/ambiguous target, unsupported origin, absent admission, or unsafe mutation must turn red. README prose cannot replace the executable route result.
