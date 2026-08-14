"""Deterministic positive fixtures used by tests and selftest."""
from __future__ import annotations

from typing import Any

from .common import (
    EXPECTED_TRANSITIONS,
    NON_DURABLE_STATES,
    STATES,
    TERMINAL_STATES,
    canonical_sha256,
)

def build_fixture_contract(
    *,
    implementation_digest: str,
    bound_blob_sha: str,
) -> dict[str, Any]:
    """Return an in-memory positive contract for selftest only."""
    return {
        "schema_version": "intent-promotion-contract/v1",
        "contract_id": "skills-shared-intent-promotion",
        "contract_version": "1.1.0",
        "subject_identity": {
            "repository": "ed3c/skills-shared",
            "commit_sha": "a" * 40,
            "tree_sha": "9" * 40,
        },
        "intent_bound_contract": {
            "repository": "ed3c/skills-shared",
            "path": "evals/fixtures/controlled-language/intent-contract.json",
            "contract_id": "controlled-language-foundation",
            "contract_version": "1.0.0",
            "git_blob_sha": bound_blob_sha,
        },
        "lifecycle": {
            "states": list(STATES),
            "non_durable_states": list(NON_DURABLE_STATES),
            "terminal_states": list(TERMINAL_STATES),
            "transitions": [
                {
                    "from": source,
                    "to": target,
                    "requires": sorted(requirements),
                }
                for (source, target), requirements in EXPECTED_TRANSITIONS.items()
            ],
        },
        "evaluator_registry": [
            {
                "evaluator_id": "local-intent-promotion-gate",
                "version": "1.1.0",
                "implementation_path": "scripts/check_intent_promotions.py",
                "implementation_digest": implementation_digest,
                "authority": "LOCAL",
                "owning": False,
                "required_for_states": [
                    "CANDIDATE",
                    "PROPOSED",
                    "VERIFIED",
                    "ADMITTED",
                    "CANONICAL",
                ],
            },
            {
                "evaluator_id": "skill-eval-contract",
                "version": "1.1.0",
                "implementation_path": "scripts/check_intent_promotions.py",
                "implementation_digest": implementation_digest,
                "authority": "OWNING_CI",
                "owning": True,
                "required_for_states": ["VERIFIED", "ADMITTED", "CANONICAL"],
            },
        ],
        "writeback_policy": {
            "append_only": True,
            "similarity_overwrite_allowed": False,
            "durable_writeback_min_state": "ADMITTED",
            "declared_destinations": [
                {
                    "destination_id": "session-scratch",
                    "scope": "SCRATCHPAD",
                    "durability": "TRANSIENT",
                    "allowed_states": ["CANDIDATE"],
                    "locator_prefix": "scratch:intent:",
                    "human_owned": False,
                },
                {
                    "destination_id": "pr-metadata",
                    "scope": "PR_METADATA",
                    "durability": "TRANSIENT",
                    "allowed_states": ["PROPOSED"],
                    "locator_prefix": "github:ed3c/skills-shared#",
                    "human_owned": False,
                },
                {
                    "destination_id": "evidence-index",
                    "scope": "EVIDENCE",
                    "durability": "TRANSIENT",
                    "allowed_states": ["VERIFIED"],
                    "locator_prefix": "evidence:intent:",
                    "human_owned": False,
                },
                {
                    "destination_id": "module-context",
                    "scope": "MODULE",
                    "durability": "DURABLE",
                    "allowed_states": ["ADMITTED", "CANONICAL"],
                    "locator_prefix": "skills/controlled-technical-language-harness/",
                    "human_owned": False,
                },
                {
                    "destination_id": "project-memory",
                    "scope": "PROJECT",
                    "durability": "DURABLE",
                    "allowed_states": ["ADMITTED", "CANONICAL"],
                    "locator_prefix": "project:skills-shared:ctl:",
                    "human_owned": False,
                },
                {
                    "destination_id": "root-context",
                    "scope": "ROOT_GLOBAL",
                    "durability": "DURABLE",
                    "allowed_states": ["CANONICAL"],
                    "locator_prefix": "CONTEXT.md#",
                    "human_owned": True,
                },
                {
                    "destination_id": "intent-history",
                    "scope": "HISTORY",
                    "durability": "DURABLE",
                    "allowed_states": ["SUPERSEDED", "REVOKED"],
                    "locator_prefix": "docs/intent-history/",
                    "human_owned": False,
                },
            ],
        },
        "approval_policy": {
            "agent_may_create_approval": False,
            "automation_may_create_approval": False,
            "caller_flag_may_request": True,
            "caller_flag_may_grant": False,
            "root_global_requires_human": True,
        },
        "supersession_policy": {
            "append_only_history": True,
            "replacement_requires_supersedes": True,
            "similarity_match_is_authority": False,
            "terminal_projection_must_be_false": True,
        },
        "completion_policy": {
            "stale_evidence_blocks": True,
            "evaluator_change_invalidates": True,
            "pr_open_is_non_authoritative": True,
            "ci_green_without_owning_receipt_is_non_authoritative": True,
            "deterministic_failure_vetoes_advisory": True,
            "private_chain_of_thought": "FORBIDDEN",
        },
        "private_reasoning_persistence": "FORBIDDEN",
    }


def build_fixture_receipt(
    contract: dict[str, Any],
    contract_raw: bytes,
    *,
    target: str = "VERIFIED",
) -> dict[str, Any]:
    subject_sha = "b" * 40
    edge_by_target = {
        "VERIFIED": ("PROPOSED", "VERIFIED"),
        "ADMITTED": ("VERIFIED", "ADMITTED"),
        "CANONICAL": ("ADMITTED", "CANONICAL"),
    }
    source, destination = edge_by_target[target]
    runs = []
    for evaluator in contract["evaluator_registry"]:
        if target not in evaluator["required_for_states"]:
            continue
        runs.append(
            {
                "evaluator_id": evaluator["evaluator_id"],
                "version": evaluator["version"],
                "implementation_path": evaluator["implementation_path"],
                "implementation_digest": evaluator["implementation_digest"],
                "authority": evaluator["authority"],
                "owning": evaluator["owning"],
                "subject_commit_sha": subject_sha,
                "status": "PASS",
                "output_digest": "sha256:" + "d" * 64,
                "receipt_digest": "sha256:" + "e" * 64,
            }
        )
    admitted = None
    approval = None
    writebacks = []
    if target == "VERIFIED":
        writebacks = [
            {
                "destination_id": "evidence-index",
                "scope": "EVIDENCE",
                "durability": "TRANSIENT",
                "locator": "evidence:intent:MI-CTL-EVIDENCE",
                "mode": "APPEND",
                "content_digest": "sha256:" + "3" * 64,
                "authority_subject": subject_sha,
                "current_projection": True,
            }
        ]
    else:
        admitted = {
            "kind": "MERGE_COMMIT",
            "repository": "ed3c/skills-shared",
            "source_head_sha": subject_sha,
            "admitted_identity": "f" * 40,
            "status": "ADMITTED",
            "receipt_digest": "sha256:" + "4" * 64,
        }
        if target == "ADMITTED":
            writebacks = [
                {
                    "destination_id": "module-context",
                    "scope": "MODULE",
                    "durability": "DURABLE",
                    "locator": "skills/controlled-technical-language-harness/references/INTENT.md",
                    "mode": "APPEND",
                    "content_digest": "sha256:" + "5" * 64,
                    "authority_subject": "f" * 40,
                    "current_projection": True,
                }
            ]
        else:
            approval = {
                "approver_identity": "ed3c",
                "approver_kind": "HUMAN",
                "approval_state": "ADMITTED",
                "approval_subject": "f" * 40,
                "allowed_actions": ["PROMOTE_CANONICAL", "WRITE:root-context"],
                "receipt_digest": "sha256:" + "6" * 64,
            }
            writebacks = [
                {
                    "destination_id": "root-context",
                    "scope": "ROOT_GLOBAL",
                    "durability": "DURABLE",
                    "locator": "CONTEXT.md#controlled-language",
                    "mode": "APPEND",
                    "content_digest": "sha256:" + "7" * 64,
                    "authority_subject": "f" * 40,
                    "current_projection": True,
                }
            ]
    bound = contract["intent_bound_contract"]
    return {
        "schema_version": "intent-promotion-receipt/v1",
        "receipt_id": f"IPR-FIXTURE-{target}",
        "intent_id": "MI-CTL-EVIDENCE",
        "contract_identity": {
            "contract_id": contract["contract_id"],
            "contract_version": contract["contract_version"],
            "contract_digest": canonical_sha256(contract_raw),
        },
        "intent_bound_contract_identity": {
            "contract_id": bound["contract_id"],
            "contract_version": bound["contract_version"],
            "git_blob_sha": bound["git_blob_sha"],
        },
        "subject": {
            "repository": "ed3c/skills-shared",
            "commit_sha": subject_sha,
            "tree_sha": "c" * 40,
            "branch": "ctl/04-intent-promotion",
            "pull_request": 120,
        },
        "from_state": source,
        "to_state": destination,
        "evidence_fresh": True,
        "pr_subject": {
            "repository": "ed3c/skills-shared",
            "number": 120,
            "head_sha": subject_sha,
            "base_ref": "main",
            "state": "MERGED" if target in {"ADMITTED", "CANONICAL"} else "OPEN",
            "observation_digest": "sha256:" + "2" * 64,
        }
        if destination in {"PROPOSED", "VERIFIED", "ADMITTED"}
        else None,
        "evaluator_receipts": runs,
        "admitted_subject": admitted,
        "writebacks": writebacks,
        "human_approval": approval,
        "lineage": {
            "supersedes": [],
            "superseded_by": None,
            "revocation_reason": None,
        },
        "caller_flags": [],
        "decision": "PROMOTE",
        "final_status": "PASS",
    }
