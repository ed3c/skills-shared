"""Fork, capsule, and assertion/probe obligation validation."""
from __future__ import annotations
from collections import defaultdict
from typing import Any
from procedural_grounding_common import *  # noqa: F403


def validate_forks(data: dict[str, Any], atom_by_id: dict[str, dict[str, Any]], checkpoint: str, context_digest: str, policy: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    raw_items = require_list(data["forks"], "$.forks")
    require(len(raw_items) <= policy["max_forks"], "fork count exceeds $.policy.max_forks")
    forks: list[dict[str, Any]] = []
    total_tokens = 0
    fields = ["fork_id", "checkpoint", "execution_mode", "context_provenance", "model_provenance", "parent_context_digest", "spawn_depth", "input_procedure_ids", "abstraction_levels", "token_budget", "tokens_used", "progress_epochs", "stop_reason", "independence_state"]
    for index, raw in enumerate(raw_items):
        path = f"$.forks[{index}]"
        fork = require_dict(raw, path)
        require_keys(fork, fields, path)
        fork["fork_id"] = require_id(fork["fork_id"], "fork", f"{path}.fork_id")
        fork["checkpoint"] = require_enum(fork["checkpoint"], CHECKPOINTS, f"{path}.checkpoint")
        require(CHECKPOINT_RANK[fork["checkpoint"]] <= CHECKPOINT_RANK[checkpoint], f"{path}.checkpoint is later than the receipt checkpoint")
        fork["execution_mode"] = require_enum(fork["execution_mode"], FORK_MODES, f"{path}.execution_mode")
        require_str(fork["context_provenance"], f"{path}.context_provenance", nonempty=False)
        if fork["model_provenance"] is not None:
            require_str(fork["model_provenance"], f"{path}.model_provenance")
        require_hex(fork["parent_context_digest"], HEX64, f"{path}.parent_context_digest")
        require(fork["parent_context_digest"] == context_digest, f"{path}.parent_context_digest must match the subject context digest")
        fork["spawn_depth"] = require_int(fork["spawn_depth"], f"{path}.spawn_depth", minimum=0)
        require(fork["spawn_depth"] <= policy["max_spawn_depth"], f"{path}.spawn_depth exceeds policy")
        ids = require_list(fork["input_procedure_ids"], f"{path}.input_procedure_ids")
        require(bool(ids), f"{path}.input_procedure_ids must not be empty")
        require(len(ids) == len(set(ids)), f"{path}.input_procedure_ids contains duplicates")
        for item_index, proc_id in enumerate(ids):
            proc_id = require_id(proc_id, "procedure", f"{path}.input_procedure_ids[{item_index}]")
            require(proc_id in atom_by_id, f"{path}.input_procedure_ids references unknown atom {proc_id}")
        levels = require_list(fork["abstraction_levels"], f"{path}.abstraction_levels")
        require(bool(levels), f"{path}.abstraction_levels must not be empty")
        require(len(levels) == len(set(levels)), f"{path}.abstraction_levels contains duplicates")
        for item_index, level in enumerate(levels):
            require_enum(level, ABSTRACTION_LEVELS, f"{path}.abstraction_levels[{item_index}]")
        budget = require_int(fork["token_budget"], f"{path}.token_budget", minimum=1)
        used = require_int(fork["tokens_used"], f"{path}.tokens_used", minimum=0)
        require(used <= budget, f"{path}.tokens_used exceeds token_budget")
        total_tokens += used
        epochs = require_list(fork["progress_epochs"], f"{path}.progress_epochs")
        no_progress = max_no_progress = 0
        previous: float | None = None
        for epoch_index, raw_epoch in enumerate(epochs):
            epoch_path = f"{path}.progress_epochs[{epoch_index}]"
            epoch = require_dict(raw_epoch, epoch_path)
            require_keys(epoch, ["epoch", "coverage_gain"], epoch_path)
            require_int(epoch["epoch"], f"{epoch_path}.epoch", minimum=1)
            gain = require_number(epoch["coverage_gain"], f"{epoch_path}.coverage_gain", minimum=0, maximum=1)
            no_progress = no_progress + 1 if previous is not None and approx_equal(gain, previous) else 0
            max_no_progress = max(max_no_progress, no_progress)
            previous = gain
        require(max_no_progress <= policy["max_no_progress_epochs"], f"{path} exceeds max consecutive no-progress epochs")
        fork["stop_reason"] = require_enum(fork["stop_reason"], STOP_REASONS, f"{path}.stop_reason")
        fork["independence_state"] = require_enum(fork["independence_state"], EVIDENCE_VOCABULARY, f"{path}.independence_state")
        if fork["execution_mode"] == "IN_PROCESS_LOGICAL":
            require(fork["independence_state"] == "NOT_EXERCISED", f"{path} cannot claim context independence in-process")
        elif fork["execution_mode"] == "SEPARATE_CONTEXT" and fork["independence_state"] == "PASS":
            require(bool(fork["context_provenance"].strip()), f"{path} requires context provenance for PASS")
        elif fork["execution_mode"] == "SEPARATE_MODEL" and fork["independence_state"] == "PASS":
            require(bool(fork["context_provenance"].strip()), f"{path} requires context provenance for PASS")
            require(isinstance(fork["model_provenance"], str) and fork["model_provenance"].strip(), f"{path} requires model provenance for PASS")
        forks.append(fork)
    require_unique(forks, "fork_id", "$.forks")
    require(total_tokens <= policy["max_total_tokens"], "fork tokens exceed $.policy.max_total_tokens")
    return forks, {item["fork_id"]: item for item in forks}


def validate_capsules(data: dict[str, Any], fork_by_id: dict[str, dict[str, Any]], source_by_id: dict[str, dict[str, Any]], atom_by_id: dict[str, dict[str, Any]], checkpoint: str, current_sha: str, policy: dict[str, Any]) -> list[dict[str, Any]]:
    raw_items = require_list(data["capsules"], "$.capsules")
    capsules: list[dict[str, Any]] = []
    fields = ["capsule_id", "fork_id", "checkpoint", "payload_kind", "source_ids", "procedure_ids", "why_now", "required_action", "assertion_or_probe", "expected_observation", "required_evidence_level", "source_groundedness", "procedure_fidelity", "runtime_relevance", "predicted_coverage_gain", "closes_critical_gap", "token_count", "fresh_for_subject_sha", "expires_after_checkpoint", "authority_conflict", "injection_decision"]
    for index, raw in enumerate(raw_items):
        path = f"$.capsules[{index}]"
        item = require_dict(raw, path)
        require_keys(item, fields, path)
        item["capsule_id"] = require_id(item["capsule_id"], "capsule", f"{path}.capsule_id")
        item["fork_id"] = require_id(item["fork_id"], "fork", f"{path}.fork_id")
        require(item["fork_id"] in fork_by_id, f"{path}.fork_id references an unknown fork")
        item["checkpoint"] = require_enum(item["checkpoint"], CHECKPOINTS, f"{path}.checkpoint")
        require(item["checkpoint"] == fork_by_id[item["fork_id"]]["checkpoint"], f"{path}.checkpoint must match its fork")
        item["payload_kind"] = require_enum(item["payload_kind"], PAYLOAD_KINDS, f"{path}.payload_kind")
        source_ids = require_list(item["source_ids"], f"{path}.source_ids")
        proc_ids = require_list(item["procedure_ids"], f"{path}.procedure_ids")
        require(bool(source_ids) and bool(proc_ids), f"{path} must bind source and procedure ids")
        require(len(source_ids) == len(set(source_ids)), f"{path}.source_ids contains duplicates")
        require(len(proc_ids) == len(set(proc_ids)), f"{path}.procedure_ids contains duplicates")
        normalized_sources = []
        for item_index, source_id in enumerate(source_ids):
            source_id = require_id(source_id, "source", f"{path}.source_ids[{item_index}]")
            require(source_id in source_by_id, f"{path}.source_ids references unknown source {source_id}")
            normalized_sources.append(source_id)
        for item_index, proc_id in enumerate(proc_ids):
            proc_id = require_id(proc_id, "procedure", f"{path}.procedure_ids[{item_index}]")
            require(proc_id in atom_by_id, f"{path}.procedure_ids references unknown atom {proc_id}")
            require(atom_by_id[proc_id]["source_id"] in normalized_sources, f"{path} omits the source for {proc_id}")
        for field in ("why_now", "required_action", "assertion_or_probe", "expected_observation", "required_evidence_level"):
            require_str(item[field], f"{path}.{field}")
        for field in ("source_groundedness", "procedure_fidelity", "runtime_relevance", "predicted_coverage_gain"):
            item[field] = require_number(item[field], f"{path}.{field}", minimum=0, maximum=1)
        item["closes_critical_gap"] = require_bool(item["closes_critical_gap"], f"{path}.closes_critical_gap")
        item["token_count"] = require_int(item["token_count"], f"{path}.token_count", minimum=1)
        require(item["token_count"] <= policy["max_capsule_tokens"], f"{path}.token_count exceeds the capsule budget")
        require_hex(item["fresh_for_subject_sha"], HEX40, f"{path}.fresh_for_subject_sha")
        item["expires_after_checkpoint"] = require_enum(item["expires_after_checkpoint"], CHECKPOINTS, f"{path}.expires_after_checkpoint")
        require(CHECKPOINT_RANK[item["expires_after_checkpoint"]] >= CHECKPOINT_RANK[item["checkpoint"]], f"{path}.expires_after_checkpoint precedes its creation checkpoint")
        item["authority_conflict"] = require_bool(item["authority_conflict"], f"{path}.authority_conflict")
        item["injection_decision"] = require_enum(item["injection_decision"], INJECTION_DECISIONS, f"{path}.injection_decision")
        if item["injection_decision"] == "INJECTED":
            require(item["fresh_for_subject_sha"] == current_sha, f"{path} is stale for the current subject")
            require(CHECKPOINT_RANK[item["checkpoint"]] <= CHECKPOINT_RANK[checkpoint] <= CHECKPOINT_RANK[item["expires_after_checkpoint"]], f"{path} is outside its checkpoint validity window")
            require(not item["authority_conflict"], f"{path} cannot inject through an authority conflict")
            for field in ("source_groundedness", "procedure_fidelity", "runtime_relevance"):
                require(item[field] >= policy[f"min_{field}"], f"{path}.{field} is below policy")
            require(item["closes_critical_gap"] or item["predicted_coverage_gain"] >= policy["min_predicted_coverage_gain"], f"{path} neither closes a critical gap nor meets the coverage-gain threshold")
            for source_id in normalized_sources:
                source = source_by_id[source_id]
                require(source["license_state"] == "ADMITTED", f"{path} cannot inject a source with unadmitted license state")
                require(source["trust_state"] == "REVIEWED", f"{path} cannot inject an unreviewed source")
                require(source["scripts_state"] in {"NONE", "REVIEWED"}, f"{path} cannot inject unreviewed or denied scripts")
                require(source["dynamic_context_state"] in {"NONE", "REVIEWED"}, f"{path} cannot inject denied dynamic context")
        capsules.append(item)
    require_unique(capsules, "capsule_id", "$.capsules")
    return capsules


def validate_obligations(data: dict[str, Any], atom_by_id: dict[str, dict[str, Any]], current_sha: str) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    raw_items = require_list(data["obligations"], "$.obligations")
    obligations: list[dict[str, Any]] = []
    fields = ["obligation_id", "procedure_id", "reason", "required_action", "assertion_or_probe", "expected_observation", "status", "evidence_ref", "subject_sha"]
    for index, raw in enumerate(raw_items):
        path = f"$.obligations[{index}]"
        item = require_dict(raw, path)
        require_keys(item, fields, path)
        item["obligation_id"] = require_id(item["obligation_id"], "obligation", f"{path}.obligation_id")
        item["procedure_id"] = require_id(item["procedure_id"], "procedure", f"{path}.procedure_id")
        require(item["procedure_id"] in atom_by_id, f"{path}.procedure_id references an unknown atom")
        for field in ("reason", "required_action", "assertion_or_probe", "expected_observation"):
            require_str(item[field], f"{path}.{field}")
        item["status"] = require_enum(item["status"], OBLIGATION_STATES, f"{path}.status")
        if item["evidence_ref"] is not None:
            require_str(item["evidence_ref"], f"{path}.evidence_ref")
        require_hex(item["subject_sha"], HEX40, f"{path}.subject_sha")
        require(item["subject_sha"] == current_sha, f"{path}.subject_sha is stale")
        if item["status"] == "SATISFIED":
            require(isinstance(item["evidence_ref"], str) and item["evidence_ref"].strip(), f"{path} requires evidence when satisfied")
        obligations.append(item)
    require_unique(obligations, "obligation_id", "$.obligations")
    by_proc: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in obligations:
        by_proc[item["procedure_id"]].append(item)
    return obligations, by_proc
