#!/usr/bin/env python3
"""Generated binding and subject-bound bootstrap receipt checks."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from consumer_bootstrap_common import (
    BINDING_REL, BootstrapError, HEX40, HEX64, RECEIPT_REL,
    REQUIREMENTS_REL, PROFILE_REL, SOURCE_REL, SharedIdentity, canonical,
    git_out, read_json, reject_unsafe, sha256,
)


def validate_binding(root: Path, identity: SharedIdentity, skills: list[str]) -> dict[str, Any]:
    binding = read_json(root / BINDING_REL)
    if binding.get("schema") != "shared-skills/consumer-binding/v1":
        raise BootstrapError("unsupported generated binding schema")
    if binding.get("source") != {
        "repository": identity.repository, "commit": identity.commit, "tree": identity.tree
    }:
        raise BootstrapError("generated binding source differs from immutable source pin")
    rows = binding.get("skills")
    if not isinstance(rows, list) or [row.get("name") for row in rows if isinstance(row, dict)] != sorted(skills):
        raise BootstrapError("generated binding Skill closure drifted")
    for row in rows:
        if set(row) != {"name", "content_sha256", "entrypoint"}:
            raise BootstrapError("generated binding Skill fields drifted")
        if not HEX64.fullmatch(row["content_sha256"]):
            raise BootstrapError("generated binding Skill digest is invalid")
        if row["entrypoint"] != f"skills/{row['name']}/SKILL.md":
            raise BootstrapError("generated binding entrypoint drifted")
    unsigned = dict(binding)
    claimed = unsigned.pop("content_sha256", None)
    if claimed != sha256(canonical(unsigned)):
        raise BootstrapError("generated binding aggregate digest is stale")
    return binding


def artifact_records(root: Path, route_records: list[dict[str, str]]) -> list[dict[str, str]]:
    records = list(route_records)
    for relative in (SOURCE_REL, PROFILE_REL, REQUIREMENTS_REL, BINDING_REL):
        path = root / relative
        if not path.is_file() or path.is_symlink():
            raise BootstrapError(f"generated artifact missing or non-regular: {relative}")
        records.append({"path": relative.as_posix(), "sha256": sha256(path.read_bytes()), "state": "GENERATED"})
    return sorted(records, key=lambda row: row["path"])


def build_receipt(
    repository_id: str,
    identity: SharedIdentity,
    rollback: dict[str, str],
    artifacts: list[dict[str, str]],
    binding: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    subject = {
        "consumer_repository": repository_id,
        "rollback": rollback,
        "shared_commit": identity.commit,
        "shared_tree": identity.tree,
        "artifacts": artifacts,
    }
    receipt: dict[str, Any] = {
        "schema": "shared-skills/consumer-bootstrap-receipt/v1",
        "consumer": {
            "repository": repository_id,
            "generated_subject_sha256": sha256(canonical(subject)),
        },
        "shared_source": identity.source_document(),
        "profile": {
            "id": profile["profile"], "sha256": sha256(canonical(profile)),
            "skills": profile["skills"],
        },
        "binding": {
            "path": BINDING_REL.as_posix(),
            "semantic_sha256": sha256(canonical(binding)),
            "content_sha256": binding["content_sha256"],
        },
        "artifacts": artifacts,
        "evidence": {
            "route_scaffold": "PASS",
            "immutable_source_binding": "PASS",
            "consumer_binding_generation": "PASS",
            "byte_readback": "PASS",
            "host_skill_discovery": "NOT_EXERCISED",
            "agent_runtime_execution": "NOT_EXERCISED",
            "provider_execution": "NOT_EXERCISED",
            "merge": "HUMAN_ADMIT_REQUIRED",
            "release": "HUMAN_ADMIT_REQUIRED",
            "rollback_execution": "NOT_EXERCISED",
        },
        "authority": {
            "automatic_merge": False,
            "automatic_conflict_resolution": False,
            "visibility_change": False,
            "credential_values": False,
            "provider_activation": False,
            "production_writeback": False,
        },
        "rollback": rollback,
        "decision_record_policy": "OBSERVATIONS_AND_DECISIONS_ONLY",
    }
    receipt["receipt_sha256"] = sha256(canonical(receipt))
    return receipt


def validate_receipt_shape(receipt: dict[str, Any]) -> None:
    required = {
        "schema", "consumer", "shared_source", "profile", "binding", "artifacts",
        "evidence", "authority", "rollback", "decision_record_policy", "receipt_sha256",
    }
    if set(receipt) != required or receipt.get("schema") != "shared-skills/consumer-bootstrap-receipt/v1":
        raise BootstrapError("bootstrap receipt schema or fields drifted")
    reject_unsafe(receipt)
    unsigned = dict(receipt)
    claimed = unsigned.pop("receipt_sha256", None)
    if claimed != sha256(canonical(unsigned)):
        raise BootstrapError("bootstrap receipt self digest is stale")
    if receipt.get("decision_record_policy") != "OBSERVATIONS_AND_DECISIONS_ONLY":
        raise BootstrapError("bootstrap receipt attempted to persist private reasoning")
    authority = receipt.get("authority")
    if not isinstance(authority, dict) or any(value is not False for value in authority.values()):
        raise BootstrapError("bootstrap receipt widened automatic authority")
    evidence = receipt.get("evidence")
    expected = {
        "route_scaffold": "PASS", "immutable_source_binding": "PASS",
        "consumer_binding_generation": "PASS", "byte_readback": "PASS",
        "host_skill_discovery": "NOT_EXERCISED", "agent_runtime_execution": "NOT_EXERCISED",
        "provider_execution": "NOT_EXERCISED", "merge": "HUMAN_ADMIT_REQUIRED",
        "release": "HUMAN_ADMIT_REQUIRED", "rollback_execution": "NOT_EXERCISED",
    }
    if evidence != expected:
        raise BootstrapError("bootstrap receipt promoted an unexercised or Human-owned lane")
    rollback = receipt.get("rollback")
    if not isinstance(rollback, dict) or set(rollback) != {"commit", "tree"}:
        raise BootstrapError("bootstrap receipt rollback subject is absent")
    if not HEX40.fullmatch(rollback["commit"]) or not HEX40.fullmatch(rollback["tree"]):
        raise BootstrapError("bootstrap receipt rollback identity is mutable")


def validate_rollback(root: Path, rollback: dict[str, str]) -> None:
    if git_out(root, "rev-parse", f"{rollback['commit']}^{{tree}}") != rollback["tree"]:
        raise BootstrapError("rollback commit/tree mismatch")
    from consumer_bootstrap_common import run_git
    current = git_out(root, "rev-parse", "HEAD")
    if run_git(root, "merge-base", "--is-ancestor", rollback["commit"], current, check=False).returncode:
        raise BootstrapError("rollback subject is not an ancestor of current consumer HEAD")


def validate_receipt(root: Path, expected: dict[str, Any]) -> None:
    path = root / RECEIPT_REL
    if not path.is_file() or path.is_symlink():
        raise BootstrapError("bootstrap receipt missing or non-regular")
    observed = read_json(path)
    validate_receipt_shape(observed)
    validate_rollback(root, observed["rollback"])
    if observed != expected:
        raise BootstrapError("bootstrap receipt is stale or substituted")
    from consumer_bootstrap_routes import observed_block
    for row in observed["artifacts"]:
        relative = row["path"]
        artifact = root / relative
        if not artifact.is_file() or artifact.is_symlink():
            raise BootstrapError(f"bootstrap receipt artifact is stale: {relative}")
        observed_digest = (
            sha256(observed_block(artifact).encode("utf-8"))
            if row["state"] == "MANAGED_BLOCK"
            else sha256(artifact.read_bytes())
        )
        expected_digest = row.get("managed_block_sha256") or row.get("sha256")
        if observed_digest != expected_digest:
            raise BootstrapError(f"bootstrap receipt artifact is stale: {relative}")
