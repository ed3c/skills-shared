"""Validate exact-subject intent-promotion transition receipts."""
from __future__ import annotations

from typing import Any

from .common import (
    EXPECTED_TRANSITIONS,
    NON_DURABLE_STATES,
    SHA256,
    SHA40,
    TERMINAL_STATES,
    PolicyRefusal,
    canonical_sha256,
    reject_private_reasoning,
    reject_unknown_keys,
    require_array,
    require_bool,
    require_object,
    require_sha256,
    require_sha40,
    require_text,
)

def validate_receipt(
    receipt: dict[str, Any],
    contract: dict[str, Any],
    contract_raw: bytes,
) -> None:
    reject_private_reasoning(receipt)
    allowed = {
        "schema_version",
        "receipt_id",
        "intent_id",
        "contract_identity",
        "intent_bound_contract_identity",
        "subject",
        "from_state",
        "to_state",
        "evidence_fresh",
        "pr_subject",
        "evaluator_receipts",
        "admitted_subject",
        "writebacks",
        "human_approval",
        "lineage",
        "caller_flags",
        "decision",
        "final_status",
    }
    reject_unknown_keys(receipt, allowed, "receipt")
    if receipt.get("schema_version") != "intent-promotion-receipt/v1":
        raise PolicyRefusal(
            "receipt schema_version must be intent-promotion-receipt/v1"
        )

    contract_identity = require_object(
        receipt.get("contract_identity"), "receipt.contract_identity"
    )
    reject_unknown_keys(
        contract_identity,
        {"contract_id", "contract_version", "contract_digest"},
        "receipt.contract_identity",
    )
    if contract_identity.get("contract_id") != contract["contract_id"]:
        raise PolicyRefusal("receipt contract_id does not match the checked contract")
    if contract_identity.get("contract_version") != contract["contract_version"]:
        raise PolicyRefusal(
            "receipt contract_version does not match the checked contract"
        )
    expected_contract_digest = canonical_sha256(contract_raw)
    if contract_identity.get("contract_digest") != expected_contract_digest:
        raise PolicyRefusal(
            "receipt contract_digest does not match the exact checked contract bytes"
        )

    bound_identity = require_object(
        receipt.get("intent_bound_contract_identity"),
        "receipt.intent_bound_contract_identity",
    )
    bound = contract["intent_bound_contract"]
    if bound_identity != {
        "contract_id": bound["contract_id"],
        "contract_version": bound["contract_version"],
        "git_blob_sha": bound["git_blob_sha"],
    }:
        raise PolicyRefusal(
            "receipt intent_bound_contract_identity does not match the contract binding"
        )

    subject = require_object(receipt.get("subject"), "receipt.subject")
    reject_unknown_keys(
        subject,
        {"repository", "commit_sha", "tree_sha", "branch", "pull_request"},
        "receipt.subject",
    )
    repository = require_text(subject.get("repository"), "receipt.subject.repository")
    if repository != contract["subject_identity"]["repository"]:
        raise PolicyRefusal("receipt subject repository differs from the contract")
    commit_sha = require_sha40(subject.get("commit_sha"), "receipt.subject.commit_sha")
    require_sha40(subject.get("tree_sha"), "receipt.subject.tree_sha")
    branch = subject.get("branch")
    if branch is not None:
        require_text(branch, "receipt.subject.branch")
    pull_request = subject.get("pull_request")
    if pull_request is not None and (
        not isinstance(pull_request, int) or pull_request < 1
    ):
        raise PolicyRefusal("receipt.subject.pull_request must be a positive integer")

    source = require_text(receipt.get("from_state"), "receipt.from_state")
    target = require_text(receipt.get("to_state"), "receipt.to_state")
    edge = (source, target)
    if edge not in EXPECTED_TRANSITIONS:
        raise PolicyRefusal(f"transition {source}->{target} is not admitted")
    requirements = EXPECTED_TRANSITIONS[edge]

    evidence_fresh = require_bool(
        receipt.get("evidence_fresh"), "receipt.evidence_fresh"
    )
    decision = require_text(receipt.get("decision"), "receipt.decision")
    final_status = require_text(receipt.get("final_status"), "receipt.final_status")
    if decision not in {"PROMOTE", "STOP", "BLOCK", "HUMAN_ADMIT_REQUIRED"}:
        raise PolicyRefusal("receipt.decision is invalid")
    if final_status not in {"PASS", "FAIL", "BLOCKED", "HUMAN_ADMIT_REQUIRED"}:
        raise PolicyRefusal("receipt.final_status is invalid")
    if final_status == "PASS":
        if decision != "PROMOTE":
            raise PolicyRefusal("final PASS requires decision PROMOTE")
        if evidence_fresh is not True:
            raise PolicyRefusal("stale evidence cannot produce final PASS")

    pr_subject = receipt.get("pr_subject")
    if "EXACT_PR_SUBJECT" in requirements:
        pr = require_object(pr_subject, "receipt.pr_subject")
        reject_unknown_keys(
            pr,
            {
                "repository",
                "number",
                "head_sha",
                "base_ref",
                "state",
                "observation_digest",
            },
            "receipt.pr_subject",
        )
        if pr.get("repository") != repository:
            raise PolicyRefusal("PR subject repository differs from receipt subject")
        if pr.get("number") != pull_request:
            raise PolicyRefusal("PR subject number differs from receipt subject")
        if pr.get("head_sha") != commit_sha:
            raise PolicyRefusal(
                "PR subject head does not equal the exact candidate commit"
            )
        require_text(pr.get("base_ref"), "receipt.pr_subject.base_ref")
        if pr.get("state") not in {"DRAFT", "OPEN", "MERGED"}:
            raise PolicyRefusal(
                "required PR subject must be DRAFT, OPEN, or MERGED"
            )
        require_sha256(
            pr.get("observation_digest"), "receipt.pr_subject.observation_digest"
        )
    elif pr_subject is not None:
        require_object(pr_subject, "receipt.pr_subject")

    registry = {
        item["evaluator_id"]: item for item in contract["evaluator_registry"]
    }
    observed: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(
        require_array(receipt.get("evaluator_receipts"), "receipt.evaluator_receipts")
    ):
        run = require_object(item, f"receipt.evaluator_receipts[{index}]")
        reject_unknown_keys(
            run,
            {
                "evaluator_id",
                "version",
                "implementation_path",
                "implementation_digest",
                "authority",
                "owning",
                "subject_commit_sha",
                "status",
                "output_digest",
                "receipt_digest",
            },
            f"receipt.evaluator_receipts[{index}]",
        )
        evaluator_id = require_text(
            run.get("evaluator_id"), f"evaluator_receipts[{index}].evaluator_id"
        )
        if evaluator_id in observed:
            raise PolicyRefusal(f"duplicate evaluator receipt {evaluator_id}")
        declared = registry.get(evaluator_id)
        if declared is None:
            raise PolicyRefusal(
                f"evaluator {evaluator_id} is not registered by the contract"
            )
        for field in (
            "version",
            "implementation_path",
            "implementation_digest",
            "authority",
            "owning",
        ):
            if run.get(field) != declared.get(field):
                raise PolicyRefusal(
                    f"evaluator {evaluator_id} {field} differs from the registry; "
                    "changed evaluator identity invalidates old evidence"
                )
        if run.get("subject_commit_sha") != commit_sha:
            raise PolicyRefusal(
                f"evaluator {evaluator_id} ran against a different commit"
            )
        if run.get("status") != "PASS" and final_status == "PASS":
            raise PolicyRefusal(
                f"final PASS cannot contain evaluator {evaluator_id} in "
                f"state {run.get('status')}"
            )
        require_sha256(
            run.get("output_digest"), f"evaluator {evaluator_id}.output_digest"
        )
        require_sha256(
            run.get("receipt_digest"), f"evaluator {evaluator_id}.receipt_digest"
        )
        observed[evaluator_id] = run

    required_ids = {
        item["evaluator_id"]
        for item in contract["evaluator_registry"]
        if target in item["required_for_states"]
    }
    missing_ids = sorted(required_ids - set(observed))
    if missing_ids:
        raise PolicyRefusal(
            f"target {target} is missing required evaluator receipts: "
            f"{', '.join(missing_ids)}"
        )
    if "LOCAL_EVALUATOR_RECEIPT" in requirements and not any(
        run["authority"] == "LOCAL" and run["status"] == "PASS"
        for run in observed.values()
    ):
        raise PolicyRefusal(f"{target} requires a passing LOCAL evaluator receipt")
    if "OWNING_EXACT_HEAD_RECEIPT" in requirements and not any(
        run["owning"] is True
        and run["authority"] == "OWNING_CI"
        and run["status"] == "PASS"
        for run in observed.values()
    ):
        raise PolicyRefusal(
            f"{target} requires a passing owning exact-head evaluator receipt"
        )

    admitted = receipt.get("admitted_subject")
    admitted_identity: str | None = None
    if "ADMITTED_SUBJECT" in requirements:
        admitted_obj = require_object(admitted, "receipt.admitted_subject")
        reject_unknown_keys(
            admitted_obj,
            {
                "kind",
                "repository",
                "source_head_sha",
                "admitted_identity",
                "status",
                "receipt_digest",
            },
            "receipt.admitted_subject",
        )
        if admitted_obj.get("kind") not in {"MERGE_COMMIT", "RELEASE_ARTIFACT"}:
            raise PolicyRefusal("admitted_subject.kind is invalid")
        if admitted_obj.get("repository") != repository:
            raise PolicyRefusal("admitted subject repository differs from receipt")
        if admitted_obj.get("source_head_sha") != commit_sha:
            raise PolicyRefusal(
                "admitted subject source head differs from the candidate commit"
            )
        admitted_identity = require_text(
            admitted_obj.get("admitted_identity"),
            "receipt.admitted_subject.admitted_identity",
        )
        if not (
            SHA40.fullmatch(admitted_identity)
            or SHA256.fullmatch(admitted_identity)
        ):
            raise PolicyRefusal(
                "admitted_subject.admitted_identity must be a Git SHA or sha256 digest"
            )
        if admitted_obj.get("status") != "ADMITTED":
            raise PolicyRefusal("admitted subject must have status ADMITTED")
        require_sha256(
            admitted_obj.get("receipt_digest"),
            "receipt.admitted_subject.receipt_digest",
        )
    elif admitted is not None:
        admitted_obj = require_object(admitted, "receipt.admitted_subject")
        admitted_identity = admitted_obj.get("admitted_identity")

    approval = receipt.get("human_approval")
    if "HUMAN_APPROVAL" in requirements:
        approval_obj = require_object(approval, "receipt.human_approval")
        reject_unknown_keys(
            approval_obj,
            {
                "approver_identity",
                "approver_kind",
                "approval_state",
                "approval_subject",
                "allowed_actions",
                "receipt_digest",
            },
            "receipt.human_approval",
        )
        require_text(
            approval_obj.get("approver_identity"),
            "receipt.human_approval.approver_identity",
        )
        if approval_obj.get("approver_kind") != "HUMAN":
            raise PolicyRefusal(
                "Agent or automation cannot manufacture Human approval"
            )
        if approval_obj.get("approval_state") != "ADMITTED":
            raise PolicyRefusal("Human approval state must be ADMITTED")
        if admitted_identity is None:
            raise PolicyRefusal("Human approval requires an admitted subject")
        if approval_obj.get("approval_subject") != admitted_identity:
            raise PolicyRefusal(
                "Human approval was issued for a different admitted subject"
            )
        actions = require_array(
            approval_obj.get("allowed_actions"),
            "receipt.human_approval.allowed_actions",
        )
        if target == "CANONICAL" and "PROMOTE_CANONICAL" not in actions:
            raise PolicyRefusal(
                "CANONICAL promotion requires Human action PROMOTE_CANONICAL"
            )
        if target == "REVOKED" and "REVOKE_INTENT" not in actions:
            raise PolicyRefusal(
                "REVOKED transition requires Human action REVOKE_INTENT"
            )
        require_sha256(
            approval_obj.get("receipt_digest"),
            "receipt.human_approval.receipt_digest",
        )
    elif approval is not None:
        require_object(approval, "receipt.human_approval")

    flags = require_array(receipt.get("caller_flags"), "receipt.caller_flags")
    if approval is None:
        for flag in flags:
            if isinstance(flag, str) and (
                "override" in flag.lower() or "approve" in flag.lower()
            ):
                raise PolicyRefusal(
                    f"caller flag {flag!r} requests approval but cannot grant it"
                )

    lineage = require_object(receipt.get("lineage"), "receipt.lineage")
    reject_unknown_keys(
        lineage,
        {"supersedes", "superseded_by", "revocation_reason"},
        "receipt.lineage",
    )
    supersedes = require_array(lineage.get("supersedes"), "receipt.lineage.supersedes")
    superseded_by = lineage.get("superseded_by")
    revocation_reason = lineage.get("revocation_reason")
    if "SUPERSESSION_TARGET" in requirements:
        if not supersedes or superseded_by is None:
            raise PolicyRefusal(
                "SUPERSEDED transition requires both supersedes lineage and superseded_by"
            )
    if "REVOCATION_REASON" in requirements:
        require_text(revocation_reason, "receipt.lineage.revocation_reason")
    if target not in TERMINAL_STATES:
        if superseded_by is not None or revocation_reason is not None:
            raise PolicyRefusal(
                "active transition cannot declare terminal lineage state"
            )

    destinations = {
        item["destination_id"]: item
        for item in contract["writeback_policy"]["declared_destinations"]
    }
    for index, item in enumerate(
        require_array(receipt.get("writebacks"), "receipt.writebacks")
    ):
        writeback = require_object(item, f"receipt.writebacks[{index}]")
        reject_unknown_keys(
            writeback,
            {
                "destination_id",
                "scope",
                "durability",
                "locator",
                "mode",
                "content_digest",
                "authority_subject",
                "current_projection",
            },
            f"receipt.writebacks[{index}]",
        )
        destination_id = require_text(
            writeback.get("destination_id"), f"writebacks[{index}].destination_id"
        )
        destination = destinations.get(destination_id)
        if destination is None:
            raise PolicyRefusal(
                f"writeback destination {destination_id} is not declared"
            )
        for field in ("scope", "durability"):
            if writeback.get(field) != destination[field]:
                raise PolicyRefusal(
                    f"writeback {destination_id} {field} differs from the contract"
                )
        if target not in destination["allowed_states"]:
            raise PolicyRefusal(
                f"writeback destination {destination_id} does not admit state {target}"
            )
        locator = require_text(
            writeback.get("locator"), f"writeback {destination_id}.locator"
        )
        if not locator.startswith(destination["locator_prefix"]):
            raise PolicyRefusal(
                f"writeback {destination_id} locator is outside the declared prefix"
            )
        mode = require_text(
            writeback.get("mode"), f"writeback {destination_id}.mode"
        )
        if mode not in {"APPEND", "SUPERSEDE", "REVOKE"}:
            raise PolicyRefusal(f"writeback {destination_id}.mode is invalid")
        require_sha256(
            writeback.get("content_digest"),
            f"writeback {destination_id}.content_digest",
        )
        authority = require_text(
            writeback.get("authority_subject"),
            f"writeback {destination_id}.authority_subject",
        )
        durability = destination["durability"]
        if durability == "DURABLE":
            if target in NON_DURABLE_STATES:
                raise PolicyRefusal(
                    f"{target} cannot create durable writeback {destination_id}"
                )
            if admitted_identity is None or authority != admitted_identity:
                raise PolicyRefusal(
                    f"durable writeback {destination_id} must bind the admitted subject"
                )
        elif authority != commit_sha:
            raise PolicyRefusal(
                f"transient writeback {destination_id} must bind the candidate commit"
            )
        if mode == "SUPERSEDE" and not supersedes:
            raise PolicyRefusal(
                f"writeback {destination_id} uses SUPERSEDE without lineage"
            )
        current_projection = require_bool(
            writeback.get("current_projection"),
            f"writeback {destination_id}.current_projection",
        )
        if target in TERMINAL_STATES and current_projection is not False:
            raise PolicyRefusal(
                f"terminal intent cannot remain a current projection at {destination_id}"
            )
        if target not in TERMINAL_STATES and current_projection is not True:
            raise PolicyRefusal(
                f"active intent writeback {destination_id} must be current"
            )
        if destination["human_owned"] is True:
            approval_obj = require_object(
                approval, f"Human-owned writeback {destination_id} approval"
            )
            required_action = f"WRITE:{destination_id}"
            if required_action not in approval_obj.get("allowed_actions", []):
                raise PolicyRefusal(
                    f"Human approval does not allow {required_action}"
                )

    if target in TERMINAL_STATES:
        for item in receipt["writebacks"]:
            if item["scope"] != "HISTORY":
                raise PolicyRefusal(
                    "terminal transitions may append history only; they may not project "
                    "module, project, or root state"
                )

    if final_status == "PASS" and target in {
        "CANDIDATE",
        "PROPOSED",
        "VERIFIED",
        "ADMITTED",
        "CANONICAL",
        "SUPERSEDED",
        "REVOKED",
    }:
        return
    if final_status == "PASS":
        raise PolicyRefusal(f"unsupported PASS target state {target}")
