# Refactor contracts and proof references

These references are host-neutral and consumer-independent.

- `refactor-contract.schema.json` defines the portable input contract for one Skill refactor.
- `example-refactor-contract.json` binds the Agentic Tech Lead worked proof to the portable law/ownership contract.
- `golden-proof.schema.json` separates immutable treatments, structural A/B, synthetic real-task A/B, live evidence states, authority and traceability.
- `tech-lead-golden-proof.json` preserves the exact old/B0/B1/B2 treatment blobs plus #308/#315 proof heads and explicit non-claims.

## Ownership

References may contain typed target identifiers, immutable content digests, evidence states and issue/PR trace IDs. They may not contain raw secrets, credentials, private reasoning, machine-portable sessions, unbounded source bodies, mutable provider state or implied Human approval.

## Data flow

```text
exact refactor request
→ refactor-contract.schema.json
→ ownership and PCR-LAW manifest
→ immutable treatment references
→ structural A/B and real-task records
→ golden-proof.schema.json
→ check_refactor_contract.py
→ deterministic proof receipt
```

## Evidence ceiling

- schema-valid contract: `STATIC_CONTRACT`;
- checker/mutation closure: `DETERMINISTIC_FIXTURE`;
- linked-worktree/subprocess canary: `SYNTHETIC_RUNTIME`;
- live model/provider/delivery: still `NOT_EXERCISED` until exact external receipts exist;
- merge/promotion: `HUMAN_ADMIT_REQUIRED`.

A lower evidence class cannot satisfy a higher claim.
