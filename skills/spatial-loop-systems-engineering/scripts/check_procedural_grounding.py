#!/usr/bin/env python3
"""Deterministic semantic checker for procedural-grounding-receipt/v1."""
from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Any
from procedural_grounding_common import *  # noqa: F403
from procedural_grounding_inputs import validate_atoms, validate_observations, validate_sources
from procedural_grounding_metrics import validate_attribution, validate_proofs_and_metrics
from procedural_grounding_runtime import validate_capsules, validate_forks, validate_obligations

TOP_FIELDS = ["schema", "receipt_id", "subject", "policy", "skill_sources", "procedure_atoms", "observations", "forks", "capsules", "obligations", "declared_metrics", "attribution", "evidence_state"]


def validate(data: dict[str, Any]) -> dict[str, Any]:
    require_keys(data, TOP_FIELDS, "$")
    require(data["schema"] == SCHEMA, f"$.schema must equal {SCHEMA}")
    require_str(data["receipt_id"], "$.receipt_id")
    evidence_state = require_enum(data["evidence_state"], EVIDENCE_VOCABULARY, "$.evidence_state")

    subject = require_dict(data["subject"], "$.subject")
    require_keys(subject, ["repository", "base_sha", "current_sha", "runtime", "checkpoint", "context_digest"], "$.subject")
    require_str(subject["repository"], "$.subject.repository")
    require_hex(subject["base_sha"], HEX40, "$.subject.base_sha")
    current_sha = require_hex(subject["current_sha"], HEX40, "$.subject.current_sha")
    runtime = require_enum(subject["runtime"], RUNTIMES, "$.subject.runtime")
    checkpoint = require_enum(subject["checkpoint"], CHECKPOINTS, "$.subject.checkpoint")
    context_digest = require_hex(subject["context_digest"], HEX64, "$.subject.context_digest")
    if evidence_state == "PASS":
        require(runtime != "UNKNOWN", "PASS is forbidden for UNKNOWN runtime identity")

    policy = require_dict(data["policy"], "$.policy")
    policy_fields = ["max_forks", "max_spawn_depth", "max_total_tokens", "max_capsule_tokens", "max_no_progress_epochs", "min_source_groundedness", "min_procedure_fidelity", "min_runtime_relevance", "min_predicted_coverage_gain"]
    require_keys(policy, policy_fields, "$.policy")
    for field, minimum in (("max_forks", 1), ("max_spawn_depth", 0), ("max_total_tokens", 1), ("max_capsule_tokens", 1), ("max_no_progress_epochs", 0)):
        policy[field] = require_int(policy[field], f"$.policy.{field}", minimum=minimum)
    for field in ("min_source_groundedness", "min_procedure_fidelity", "min_runtime_relevance", "min_predicted_coverage_gain"):
        policy[field] = require_number(policy[field], f"$.policy.{field}", minimum=0, maximum=1)

    sources, source_by_id = validate_sources(data)
    atoms, atom_by_id = validate_atoms(data, source_by_id)
    observations = validate_observations(data, atom_by_id, current_sha, evidence_state)
    forks, fork_by_id = validate_forks(data, atom_by_id, checkpoint, context_digest, policy)
    capsules = validate_capsules(data, fork_by_id, source_by_id, atom_by_id, checkpoint, current_sha, policy)
    obligations, obligations_by_proc = validate_obligations(data, atom_by_id, current_sha)
    metrics, _ = validate_proofs_and_metrics(data, atoms, observations, source_by_id, obligations, obligations_by_proc, evidence_state)
    attribution_state = validate_attribution(data)
    return {"receipt_id": data["receipt_id"], "checkpoint": checkpoint, "runtime": runtime, "metrics": metrics, "fork_count": len(forks), "capsule_count": len(capsules), "evidence_state": evidence_state, "attribution_state": attribution_state}


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: check_procedural_grounding.py <receipt.json>", file=sys.stderr)
        return 64
    data = parse_contract(Path(argv[1]))
    try:
        result = validate(data)
    except ContractError as exc:
        print(f"CONTRACT FAIL: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
