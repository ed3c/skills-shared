# Scripts

## `check_refactor_proof.py`

Validates a refactor-proof packet. It enforces treatment roles and immutable identities, old-strength coverage, monotone proof layers, matched-task fairness, complete denominator policy, cleanup, remaining issue ownership and non-widening authority.

## `check_golden_proof_registry.py`

Validates the golden-proof registry against current repository bytes. It checks unique IDs, owner/entrypoint/runner paths, runner reachability, frozen Git blob identities, proof-layer ceiling, denominator/cleanup claims and authority.

## `check_refactor_proof_stack.py`

Validates the molecular issue/PR graph. It enforces unique issue/PR ownership, one convergence owner, exactly one Git parent for each true child, base-branch/parent agreement, declared consumed artifacts, no fake serial sibling, no Stack paths on external evidence, open-head lookup through GitHub metadata, immutable evidence for merged state, and non-widening delivery authority.

All scripts are zero-network and standard-library only except for the pinned Draft 2020-12 validator. They return non-zero on mechanism or semantic failure. They do not execute a model/provider or grant synchronization, publication, merge, release or promotion authority.
