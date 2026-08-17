# Scripts

## `check_refactor_proof.py`

Validates a refactor-proof packet. It enforces treatment roles and immutable identities, old-strength coverage, monotone proof layers, matched-task fairness, complete denominator policy, cleanup, remaining issue ownership and non-widening authority.

## `check_golden_proof_registry.py`

Validates the golden-proof registry against current repository bytes. It checks unique IDs, owner/entrypoint/runner paths, runner reachability, frozen Git blob identities, proof-layer ceiling, denominator/cleanup claims and authority.

## `check_refactor_proof_stack.py`

Validates the molecular issue/PR graph. It enforces unique issue/PR ownership, one convergence owner, exactly one Git parent for each true child, base-branch/parent agreement, declared consumed artifacts, no fake serial sibling, no Stack paths on external evidence, open-head lookup through GitHub metadata, immutable evidence for merged state, and non-widening delivery authority.

## `check_skill_adoption_ledger.py`

Validates the cross-Skill adoption ledger against current repository bytes. It checks scope completeness against the audited set, evidence-path existence, the state-to-evidence contract (`PASS`/`PARTIAL`/`NOT_EXERCISED` must name evidence, `ABSENT`/`NOT_IMPLEMENTED` must not), executable claims proved by an executable rather than by Markdown, frozen treatments bound to a registered golden proof, registry agreement in both directions, evidence-layer ceilings, and a known owning issue for every gap. Being zero-network, it refuses a `molecular_traceability` PASS outright: no offline byte proves current issue/PR delivery state.

## `render_adoption_report.py`

Renders the adoption ledger into a human report and, with `--check`, refuses any byte difference between that report and what the ledger currently renders (exit 2). Both `--ledger` and `--output` are arguments: this script lives inside a Skill and must not resolve upward into a repository root to find its input or its destination. The report is a projection with no authority of its own -- editing it is reverted, and a state it shows can only change by changing the ledger.

All scripts are zero-network and standard-library only except for the pinned Draft 2020-12 validator. They return non-zero on mechanism or semantic failure. They do not execute a model/provider or grant synchronization, publication, merge, release or promotion authority.
