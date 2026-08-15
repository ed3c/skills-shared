"""Source, procedure-atom, and observation validation."""
from __future__ import annotations
from typing import Any
from procedural_grounding_common import *  # noqa: F403


def validate_sources(data: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    raw_items = require_list(data["skill_sources"], "$.skill_sources")
    require(bool(raw_items), "$.skill_sources must not be empty")
    sources: list[dict[str, Any]] = []
    fields = ["source_id", "name", "repository", "ref", "path", "blob_sha", "content_sha256", "license_state", "trust_state", "scripts_state", "dynamic_context_state"]
    for index, raw in enumerate(raw_items):
        path = f"$.skill_sources[{index}]"
        source = require_dict(raw, path)
        require_keys(source, fields, path)
        source["source_id"] = require_id(source["source_id"], "source", f"{path}.source_id")
        for field in ("name", "repository", "ref", "path"):
            require_str(source[field], f"{path}.{field}")
        require_hex(source["blob_sha"], HEX40, f"{path}.blob_sha")
        require_hex(source["content_sha256"], HEX64, f"{path}.content_sha256")
        source["license_state"] = require_enum(source["license_state"], {"ADMITTED", "ABSENT", "BLOCKED"}, f"{path}.license_state")
        source["trust_state"] = require_enum(source["trust_state"], {"REVIEWED", "UNREVIEWED", "DENIED"}, f"{path}.trust_state")
        source["scripts_state"] = require_enum(source["scripts_state"], {"NONE", "REVIEWED", "UNREVIEWED", "DENIED"}, f"{path}.scripts_state")
        source["dynamic_context_state"] = require_enum(source["dynamic_context_state"], {"NONE", "REVIEWED", "DENIED"}, f"{path}.dynamic_context_state")
        sources.append(source)
    require_unique(sources, "source_id", "$.skill_sources")
    return sources, {item["source_id"]: item for item in sources}


def validate_atoms(data: dict[str, Any], source_by_id: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    raw_items = require_list(data["procedure_atoms"], "$.procedure_atoms")
    require(bool(raw_items), "$.procedure_atoms must not be empty")
    atoms: list[dict[str, Any]] = []
    fields = ["procedure_id", "source_id", "source_span", "summary", "kind", "trigger", "action", "proof_mode", "criticality", "novelty", "required_now", "abstraction_level", "oracle", "negative_control", "weight"]
    for index, raw in enumerate(raw_items):
        path = f"$.procedure_atoms[{index}]"
        atom = require_dict(raw, path)
        require_keys(atom, fields, path)
        atom["procedure_id"] = require_id(atom["procedure_id"], "procedure", f"{path}.procedure_id")
        atom["source_id"] = require_id(atom["source_id"], "source", f"{path}.source_id")
        require(atom["source_id"] in source_by_id, f"{path}.source_id references an unknown source")
        for field in ("source_span", "summary", "trigger", "action", "oracle"):
            require_str(atom[field], f"{path}.{field}")
        atom["kind"] = require_enum(atom["kind"], ATOM_KINDS, f"{path}.kind")
        atom["proof_mode"] = require_enum(atom["proof_mode"], PROOF_MODES, f"{path}.proof_mode")
        atom["criticality"] = require_enum(atom["criticality"], CRITICALITIES, f"{path}.criticality")
        atom["novelty"] = require_enum(atom["novelty"], NOVELTIES, f"{path}.novelty")
        atom["required_now"] = require_bool(atom["required_now"], f"{path}.required_now")
        atom["abstraction_level"] = require_enum(atom["abstraction_level"], ABSTRACTION_LEVELS, f"{path}.abstraction_level")
        if atom["negative_control"] is not None:
            require_str(atom["negative_control"], f"{path}.negative_control")
        atom["weight"] = require_int(atom["weight"], f"{path}.weight", minimum=1)
        require(atom["weight"] <= 5, f"{path}.weight must be <= 5")
        if atom["proof_mode"] == "NEGATIVE_CONTROL_REQUIRED":
            require(isinstance(atom["negative_control"], str) and atom["negative_control"].strip(), f"{path}.negative_control is required")
        atoms.append(atom)
    require_unique(atoms, "procedure_id", "$.procedure_atoms")
    return atoms, {item["procedure_id"]: item for item in atoms}


def validate_observations(data: dict[str, Any], atom_by_id: dict[str, dict[str, Any]], current_sha: str, evidence_state: str) -> list[dict[str, Any]]:
    raw_items = require_list(data["observations"], "$.observations")
    observations: list[dict[str, Any]] = []
    fields = ["observation_id", "procedure_id", "uptake_state", "evidence_modality", "evidence_ref", "content_sha256", "subject_sha", "oracle", "expected", "observed", "exit_code", "timestamp", "fresh"]
    for index, raw in enumerate(raw_items):
        path = f"$.observations[{index}]"
        item = require_dict(raw, path)
        require_keys(item, fields, path)
        item["observation_id"] = require_id(item["observation_id"], "observation", f"{path}.observation_id")
        item["procedure_id"] = require_id(item["procedure_id"], "procedure", f"{path}.procedure_id")
        require(item["procedure_id"] in atom_by_id, f"{path}.procedure_id references an unknown atom")
        item["uptake_state"] = require_enum(item["uptake_state"], UPTAKE_STATES, f"{path}.uptake_state")
        item["evidence_modality"] = require_enum(item["evidence_modality"], MODALITIES, f"{path}.evidence_modality")
        require_str(item["evidence_ref"], f"{path}.evidence_ref")
        require_hex(item["content_sha256"], HEX64, f"{path}.content_sha256")
        require_hex(item["subject_sha"], HEX40, f"{path}.subject_sha")
        require(item["subject_sha"] == current_sha, f"{path}.subject_sha is stale for the current subject")
        for field in ("oracle", "expected", "observed"):
            require_str(item[field], f"{path}.{field}")
        if item["exit_code"] is not None:
            require_int(item["exit_code"], f"{path}.exit_code")
        require_timestamp(item["timestamp"], f"{path}.timestamp")
        item["fresh"] = require_bool(item["fresh"], f"{path}.fresh")
        if evidence_state == "PASS":
            require(item["fresh"], f"{path} must be fresh when the receipt is PASS")
        if item["uptake_state"] in EXECUTION_STATES and item["evidence_modality"] in {"MODEL_OUTPUT", "SOURCE_DIFF", "STATIC_ARTIFACT"}:
            fail(f"{path} claims execution from a non-runtime evidence modality")
        if item["uptake_state"] == "NEGATIVE_CONTROL_PASSED":
            require(atom_by_id[item["procedure_id"]]["proof_mode"] == "NEGATIVE_CONTROL_REQUIRED", f"{path} assigns negative-control proof to an atom that does not require it")
        observations.append(item)
    require_unique(observations, "observation_id", "$.observations")
    return observations
