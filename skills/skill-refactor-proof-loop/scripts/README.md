# Scripts

## `check_refactor_proof.py`

Validates a refactor-proof packet. It enforces treatment roles and immutable identities, old-strength coverage, monotone proof layers, matched-task fairness, complete denominator policy, cleanup, remaining issue ownership and non-widening authority.

## `check_golden_proof_registry.py`

Validates the golden-proof registry against current repository bytes. It checks unique IDs, owner/entrypoint/runner paths, runner reachability, frozen Git blob identities, proof-layer ceiling, denominator/cleanup claims and authority.

Both scripts are zero-network, standard-library only except for the pinned Draft 2020-12 validator, and return non-zero on mechanism or semantic failure. They do not execute a model/provider or grant merge/release authority.
