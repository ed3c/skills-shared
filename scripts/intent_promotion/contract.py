"""Validate intent-promotion policy contracts."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .common import (
    ACTIVE_STATES,
    EXPECTED_TRANSITIONS,
    NON_DURABLE_STATES,
    REPOSITORY,
    SEMVER,
    STATES,
    TERMINAL_STATES,
    PolicyRefusal,
    git_blob_sha,
    load_object,
    reject_private_reasoning,
    reject_unknown_keys,
    require_array,
    require_bool,
    require_digest,
    require_object,
    require_sha40,
    require_text,
    verify_file_digest,
)

def validate_contract(
    contract: dict[str, Any],
    *,
    repository_root: Path | None = None,
    verify_external_bindings: bool = False,
) -> None:
    reject_private_reasoning(contract)
    allowed = {
        "schema_version",
        "contract_id",
        "contract_version",
        "subject_identity",
        "intent_bound_contract",
        "lifecycle",
        "evaluator_registry",
        "writeback_policy",
        "approval_policy",
        "supersession_policy",
        "completion_policy",
        "private_reasoning_persistence",
    }
    reject_unknown_keys(contract, allowed, "contract")

    if contract.get("schema_version") != "intent-promotion-contract/v1":
        raise PolicyRefusal(
            "contract schema_version must be intent-promotion-contract/v1"
        )
    require_text(contract.get("contract_id"), "contract.contract_id")
    version = require_text(contract.get("contract_version"), "contract.contract_version")
    if not SEMVER.fullmatch(version):
        raise PolicyRefusal("contract.contract_version must be semantic version x.y.z")

    subject = require_object(contract.get("subject_identity"), "contract.subject_identity")
    reject_unknown_keys(
        subject, {"repository", "commit_sha", "tree_sha"}, "contract.subject_identity"
    )
    repository = require_text(subject.get("repository"), "contract.subject_identity.repository")
    if not REPOSITORY.fullmatch(repository):
        raise PolicyRefusal("contract.subject_identity.repository must be owner/name")
    require_sha40(subject.get("commit_sha"), "contract.subject_identity.commit_sha")
    require_sha40(subject.get("tree_sha"), "contract.subject_identity.tree_sha")

    bound = require_object(
        contract.get("intent_bound_contract"), "contract.intent_bound_contract"
    )
    reject_unknown_keys(
        bound,
        {"repository", "path", "contract_id", "contract_version", "git_blob_sha"},
        "contract.intent_bound_contract",
    )
    if bound.get("repository") != repository:
        raise PolicyRefusal(
            "intent_bound_contract.repository must equal subject repository"
        )
    bound_path = require_text(bound.get("path"), "intent_bound_contract.path")
    require_text(bound.get("contract_id"), "intent_bound_contract.contract_id")
    bound_version = require_text(
        bound.get("contract_version"), "intent_bound_contract.contract_version"
    )
    if not SEMVER.fullmatch(bound_version):
        raise PolicyRefusal(
            "intent_bound_contract.contract_version must be semantic version x.y.z"
        )
    require_sha40(bound.get("git_blob_sha"), "intent_bound_contract.git_blob_sha")

    lifecycle = require_object(contract.get("lifecycle"), "contract.lifecycle")
    reject_unknown_keys(
        lifecycle,
        {"states", "transitions", "non_durable_states", "terminal_states"},
        "contract.lifecycle",
    )
    states = require_array(lifecycle.get("states"), "lifecycle.states")
    if set(states) != set(STATES) or len(states) != len(STATES):
        raise PolicyRefusal(f"lifecycle.states must be exactly {list(STATES)}")
    non_durable = require_array(
        lifecycle.get("non_durable_states"), "lifecycle.non_durable_states"
    )
    if set(non_durable) != set(NON_DURABLE_STATES) or len(non_durable) != len(
        NON_DURABLE_STATES
    ):
        raise PolicyRefusal(
            "lifecycle.non_durable_states must be exactly "
            f"{list(NON_DURABLE_STATES)}"
        )
    terminal = require_array(
        lifecycle.get("terminal_states"), "lifecycle.terminal_states"
    )
    if set(terminal) != set(TERMINAL_STATES) or len(terminal) != len(
        TERMINAL_STATES
    ):
        raise PolicyRefusal(
            f"lifecycle.terminal_states must be exactly {list(TERMINAL_STATES)}"
        )

    observed_transitions: dict[tuple[str, str], frozenset[str]] = {}
    for index, item in enumerate(
        require_array(lifecycle.get("transitions"), "lifecycle.transitions")
    ):
        transition = require_object(item, f"lifecycle.transitions[{index}]")
        reject_unknown_keys(
            transition, {"from", "to", "requires"}, f"lifecycle.transitions[{index}]"
        )
        source = require_text(transition.get("from"), f"transition[{index}].from")
        target = require_text(transition.get("to"), f"transition[{index}].to")
        requires = require_array(
            transition.get("requires"), f"transition[{index}].requires"
        )
        if not all(isinstance(item, str) and item for item in requires):
            raise PolicyRefusal(f"transition[{index}].requires must contain strings")
        edge = (source, target)
        if edge in observed_transitions:
            raise PolicyRefusal(f"duplicate lifecycle transition {source}->{target}")
        observed_transitions[edge] = frozenset(requires)
    if observed_transitions != EXPECTED_TRANSITIONS:
        missing = sorted(set(EXPECTED_TRANSITIONS) - set(observed_transitions))
        extra = sorted(set(observed_transitions) - set(EXPECTED_TRANSITIONS))
        wrong = sorted(
            edge
            for edge in set(observed_transitions) & set(EXPECTED_TRANSITIONS)
            if observed_transitions[edge] != EXPECTED_TRANSITIONS[edge]
        )
        raise PolicyRefusal(
            "lifecycle transition contract differs from the canonical graph; "
            f"missing={missing}, extra={extra}, wrong_requirements={wrong}"
        )

    registry: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(
        require_array(contract.get("evaluator_registry"), "contract.evaluator_registry")
    ):
        evaluator = require_object(item, f"evaluator_registry[{index}]")
        reject_unknown_keys(
            evaluator,
            {
                "evaluator_id",
                "version",
                "implementation_path",
                "implementation_digest",
                "authority",
                "owning",
                "required_for_states",
            },
            f"evaluator_registry[{index}]",
        )
        evaluator_id = require_text(
            evaluator.get("evaluator_id"), f"evaluator_registry[{index}].evaluator_id"
        )
        if evaluator_id in registry:
            raise PolicyRefusal(f"duplicate evaluator_id {evaluator_id}")
        evaluator_version = require_text(
            evaluator.get("version"), f"evaluator_registry[{index}].version"
        )
        if not SEMVER.fullmatch(evaluator_version):
            raise PolicyRefusal(f"{evaluator_id}.version must be semantic version")
        implementation_path = require_text(
            evaluator.get("implementation_path"),
            f"{evaluator_id}.implementation_path",
        )
        implementation_digest = require_digest(
            evaluator.get("implementation_digest"),
            f"{evaluator_id}.implementation_digest",
        )
        authority = require_text(
            evaluator.get("authority"), f"{evaluator_id}.authority"
        )
        if authority not in {"LOCAL", "OWNING_CI", "EXTERNAL"}:
            raise PolicyRefusal(f"{evaluator_id}.authority is invalid")
        owning = require_bool(evaluator.get("owning"), f"{evaluator_id}.owning")
        if owning != (authority == "OWNING_CI"):
            raise PolicyRefusal(
                f"{evaluator_id}.owning must be true only for OWNING_CI authority"
            )
        required_states = require_array(
            evaluator.get("required_for_states"),
            f"{evaluator_id}.required_for_states",
        )
        if not required_states or not all(state in STATES for state in required_states):
            raise PolicyRefusal(
                f"{evaluator_id}.required_for_states must name declared states"
            )
        registry[evaluator_id] = evaluator
        if verify_external_bindings:
            if repository_root is None:
                raise PolicyRefusal("repository_root is required to verify implementations")
            verify_file_digest(
                repository_root,
                implementation_path,
                implementation_digest,
                f"evaluator {evaluator_id}",
            )

    if not any(
        evaluator["authority"] == "LOCAL"
        and "CANDIDATE" in evaluator["required_for_states"]
        for evaluator in registry.values()
    ):
        raise PolicyRefusal(
            "evaluator_registry must include a LOCAL evaluator for CANDIDATE"
        )
    for state in ("VERIFIED", "ADMITTED", "CANONICAL"):
        if not any(
            evaluator["owning"] is True and state in evaluator["required_for_states"]
            for evaluator in registry.values()
        ):
            raise PolicyRefusal(
                f"evaluator_registry has no owning exact-head evaluator for {state}"
            )

    writeback_policy = require_object(
        contract.get("writeback_policy"), "contract.writeback_policy"
    )
    reject_unknown_keys(
        writeback_policy,
        {
            "append_only",
            "similarity_overwrite_allowed",
            "durable_writeback_min_state",
            "declared_destinations",
        },
        "contract.writeback_policy",
    )
    if writeback_policy.get("append_only") is not True:
        raise PolicyRefusal("writeback_policy.append_only must remain true")
    if writeback_policy.get("similarity_overwrite_allowed") is not False:
        raise PolicyRefusal(
            "writeback_policy.similarity_overwrite_allowed must remain false"
        )
    if writeback_policy.get("durable_writeback_min_state") != "ADMITTED":
        raise PolicyRefusal(
            "writeback_policy.durable_writeback_min_state must remain ADMITTED"
        )

    destinations: set[str] = set()
    for index, item in enumerate(
        require_array(
            writeback_policy.get("declared_destinations"),
            "writeback_policy.declared_destinations",
        )
    ):
        destination = require_object(
            item, f"writeback_policy.declared_destinations[{index}]"
        )
        reject_unknown_keys(
            destination,
            {
                "destination_id",
                "scope",
                "durability",
                "allowed_states",
                "locator_prefix",
                "human_owned",
            },
            f"writeback destination[{index}]",
        )
        destination_id = require_text(
            destination.get("destination_id"), f"destination[{index}].destination_id"
        )
        if destination_id in destinations:
            raise PolicyRefusal(f"duplicate destination_id {destination_id}")
        destinations.add(destination_id)
        scope = require_text(destination.get("scope"), f"{destination_id}.scope")
        if scope not in {
            "SESSION",
            "SCRATCHPAD",
            "PR_METADATA",
            "EVIDENCE",
            "MODULE",
            "PROJECT",
            "ROOT_GLOBAL",
            "HISTORY",
        }:
            raise PolicyRefusal(f"{destination_id}.scope is invalid")
        durability = require_text(
            destination.get("durability"), f"{destination_id}.durability"
        )
        if durability not in {"TRANSIENT", "DURABLE"}:
            raise PolicyRefusal(f"{destination_id}.durability is invalid")
        allowed_states = require_array(
            destination.get("allowed_states"), f"{destination_id}.allowed_states"
        )
        if not allowed_states or not all(state in STATES for state in allowed_states):
            raise PolicyRefusal(
                f"{destination_id}.allowed_states must name declared states"
            )
        prefix = require_text(
            destination.get("locator_prefix"), f"{destination_id}.locator_prefix"
        )
        if prefix.startswith(("/", "~")) or re.match(r"^[A-Za-z]:[\\/]", prefix):
            raise PolicyRefusal(
                f"{destination_id}.locator_prefix must not be a machine-local absolute path"
            )
        human_owned = require_bool(
            destination.get("human_owned"), f"{destination_id}.human_owned"
        )
        if durability == "DURABLE":
            premature = set(allowed_states) & set(NON_DURABLE_STATES)
            if premature:
                raise PolicyRefusal(
                    f"durable destination {destination_id} admits non-durable states "
                    f"{sorted(premature)}"
                )
        if scope == "ROOT_GLOBAL":
            if set(allowed_states) != {"CANONICAL"}:
                raise PolicyRefusal(
                    f"root/global destination {destination_id} must allow CANONICAL only"
                )
            if durability != "DURABLE" or human_owned is not True:
                raise PolicyRefusal(
                    f"root/global destination {destination_id} must be durable and Human-owned"
                )

    approval = require_object(
        contract.get("approval_policy"), "contract.approval_policy"
    )
    expected_approval = {
        "agent_may_create_approval": False,
        "automation_may_create_approval": False,
        "caller_flag_may_request": True,
        "caller_flag_may_grant": False,
        "root_global_requires_human": True,
    }
    if approval != expected_approval:
        raise PolicyRefusal(
            "approval_policy must keep Agent/automation/flag grants disabled and "
            "root/global admission Human-owned"
        )

    supersession = require_object(
        contract.get("supersession_policy"), "contract.supersession_policy"
    )
    expected_supersession = {
        "append_only_history": True,
        "replacement_requires_supersedes": True,
        "similarity_match_is_authority": False,
        "terminal_projection_must_be_false": True,
    }
    if supersession != expected_supersession:
        raise PolicyRefusal(
            "supersession_policy must preserve append-only lineage and forbid "
            "similarity authority/current terminal projections"
        )

    completion = require_object(
        contract.get("completion_policy"), "contract.completion_policy"
    )
    expected_completion = {
        "stale_evidence_blocks": True,
        "evaluator_change_invalidates": True,
        "pr_open_is_non_authoritative": True,
        "ci_green_without_owning_receipt_is_non_authoritative": True,
        "deterministic_failure_vetoes_advisory": True,
        "private_chain_of_thought": "FORBIDDEN",
    }
    if completion != expected_completion:
        raise PolicyRefusal(
            "completion_policy must preserve freshness, exact evaluator identity, "
            "non-authoritative PR/foreign CI, deterministic veto, and reasoning privacy"
        )
    if contract.get("private_reasoning_persistence") != "FORBIDDEN":
        raise PolicyRefusal("private_reasoning_persistence must remain FORBIDDEN")

    if verify_external_bindings:
        if repository_root is None:
            raise PolicyRefusal("repository_root is required to verify bound contracts")
        relative = Path(bound_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise PolicyRefusal(
                "intent_bound_contract.path must be repository-relative"
            )
        bound_file = repository_root / relative
        bound_contract, bound_raw = load_object(bound_file)
        if git_blob_sha(bound_raw) != bound["git_blob_sha"]:
            raise PolicyRefusal(
                "intent_bound_contract.git_blob_sha does not match the exact bound bytes"
            )
        if bound_contract.get("schema_version") != "intent-bound-constraint/v1":
            raise PolicyRefusal("bound contract is not intent-bound-constraint/v1")
        if bound_contract.get("contract_id") != bound["contract_id"]:
            raise PolicyRefusal("bound intent contract_id does not match")
        if bound_contract.get("contract_version") != bound["contract_version"]:
            raise PolicyRefusal("bound intent contract_version does not match")
        bound_subject = require_object(
            bound_contract.get("subject_identity"), "bound.subject_identity"
        )
        if bound_subject.get("repository") != repository:
            raise PolicyRefusal("bound intent contract repository does not match")
