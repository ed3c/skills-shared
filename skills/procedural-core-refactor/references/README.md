# Refactor contracts and proof references

These references are host-neutral and consumer-independent.

- `refactor-contract.schema.json` defines the portable input contract for one Skill refactor.
- `example-refactor-contract.json` is a positive static example. It does not prove a checker, target refactor, runtime, provider or delivery lane executed.
- `golden-proof.schema.json` and `tech-lead-golden-proof.json` are introduced by issue #328 after the executable checker and proof subjects are available.

## Ownership

References may contain typed target identifiers, immutable content digests, evidence states and issue/PR trace IDs. They may not contain raw secrets, credentials, private reasoning, machine-portable sessions, unbounded source bodies, mutable provider state or implied Human approval.

## Data flow

```text
exact refactor request
→ refactor-contract.schema.json
→ ownership and law manifest
→ immutable treatment references
→ assertion and A/B receipts
→ golden-proof contract
```

A schema-valid document remains `STATIC_CONTRACT`. Only an owning executable assertion can advance an assertion state, and only exact runtime/provider/Human receipts can advance their corresponding higher evidence class.
