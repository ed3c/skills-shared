# Scripts

## `check_refactor_proof.py`

Validates a refactor-proof packet. It enforces treatment roles and immutable identities, old-strength coverage, monotone proof layers, matched-task fairness, complete denominator policy, cleanup, remaining issue ownership and non-widening authority.

## `check_golden_proof_registry.py`

Validates the golden-proof registry against current repository bytes. It checks unique IDs, owner/entrypoint/runner paths, runner reachability, frozen Git blob identities, proof-layer ceiling, denominator/cleanup claims and authority.

## `check_refactor_proof_stack.py`

Validates the molecular issue/PR graph. It enforces unique issue/PR ownership, one convergence owner, exactly one Git parent for each true child, base-branch/parent agreement, declared consumed artifacts, no fake serial sibling, no Stack paths on external evidence, open-head lookup through GitHub metadata, immutable evidence for merged state, and non-widening delivery authority.

## `check_skill_adoption_ledger.py`

Validates the cross-Skill adoption ledger against current repository bytes. It checks scope completeness against the audited set, evidence-path existence, the state-to-evidence contract (`PASS`/`PARTIAL`/`NOT_EXERCISED` must name evidence, `ABSENT`/`NOT_IMPLEMENTED` must not), executable claims proved by an executable rather than by Markdown, frozen treatments bound to a registered golden proof, registry agreement in both directions, evidence-layer ceilings, and a known owning issue for every gap. Being zero-network, it refuses a `molecular_traceability` PASS outright: no offline byte proves current issue/PR delivery state.

It also replays the `migration_order`. The recorded sequence is discarded and recomputed from `depends_on` alone by stable topological sort (alphabetically first Skill whose blockers are all placed), so a hand-sorted list is refused as `MIGRATION_ORDER_NOT_CANONICAL` and a dependency cycle as `MIGRATION_ORDER_CYCLE` — distinct states, because one means the order drifted and the other means no order exists. Every ordered Skill must be in scope exactly once, its leaf issue must be known and must own at least one of that Skill's gaps and none of any other Skill's, and every blocker must name an ordered Skill and be backed by basis paths that exist.

## `render_adoption_audit.py`

Renders `docs/traceability/SKILL_REFACTOR_ADOPTION_AUDIT.md` from the adoption ledger: headline counts, the per-Skill × criterion matrix, every gap grouped under the issue that owns it, and the migration order with the blocker and basis paths each edge was read out of. The report is a projection, never a second source — `--check` re-renders and byte-compares, so a hand-edited report, a stale report, or a ledger change nobody re-rendered is a red suite. It names the admission record in its header and asserts nothing about it beyond which method is canonical.

All scripts are zero-network and standard-library only except for the pinned Draft 2020-12 validator. They return non-zero on mechanism or semantic failure. They do not execute a model/provider or grant synchronization, publication, merge, release or promotion authority.
