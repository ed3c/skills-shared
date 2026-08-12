#!/usr/bin/env python3
"""Validate release receipts against capability unlocks, evidence, scorecards, and rollback artifacts."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASES = ROOT / "evals" / "releases.json"
UNLOCKS = ROOT / "evals" / "capability-unlocks.json"
HEX_SHA = re.compile(r"^[0-9a-f]{7,64}$")
EXACT_SHA = re.compile(r"^[0-9a-f]{40}$")
NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def load_object(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object: {path}")
    return value


def repo_path(root: Path, ref: str, label: str) -> Path:
    if not isinstance(ref, str) or not ref.strip():
        raise ValueError(f"{label} must be a non-empty repository-relative path")
    candidate = Path(ref)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"{label} must be repository-relative")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} escapes repository") from exc
    return resolved


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_scorecard(ref: str, release: dict, unlock_id: str, root: Path) -> None:
    path = repo_path(root, ref, "scorecard")
    value = load_object(path, "scorecard")
    if value.get("schema_version") != "skill-scorecard/v1":
        raise ValueError(f"unsupported scorecard schema: {ref}")
    if value.get("skill") != release.get("skill") or value.get("skill_sha") != release.get("skill_sha"):
        raise ValueError(f"scorecard identity does not match release: {ref}")
    if "overall_score" in value:
        raise ValueError("scorecard must not collapse ecosystem and capability into overall_score")
    ecosystem = value.get("ecosystem_quality")
    capability = value.get("verified_capability")
    if not isinstance(ecosystem, dict) or not isinstance(capability, dict):
        raise ValueError("scorecard must keep ecosystem_quality and verified_capability separate")
    required_ecosystem = {
        "static_valid", "provenance", "installability", "security",
        "documentation", "compatibility", "drift_free",
    }
    if set(ecosystem) != required_ecosystem or any(not isinstance(ecosystem[key], bool) for key in required_ecosystem):
        raise ValueError("ecosystem_quality must expose only the seven boolean hygiene checks")
    required_capability = {
        "routing_f1", "task_pass_rate", "skill_lift", "candidate_delta",
        "generalization_gap", "cross_harness_variance", "recovery_rate",
        "safety_pass_rate", "capability_unlock_count",
    }
    if set(capability) != required_capability:
        raise ValueError("verified_capability fields do not match scorecard contract")
    if not isinstance(capability.get("capability_unlock_count"), int) or capability["capability_unlock_count"] < 1:
        raise ValueError(f"scorecard does not expose capability unlock {unlock_id}")
    for key in ("routing_f1", "task_pass_rate", "recovery_rate", "safety_pass_rate", "generalization_gap"):
        value_ = capability.get(key)
        if not isinstance(value_, (int, float)) or not 0 <= value_ <= 1:
            raise ValueError(f"verified capability {key} must be a number in [0,1]")
    for key in ("skill_lift", "candidate_delta"):
        value_ = capability.get(key)
        if not isinstance(value_, (int, float)) or not -1 <= value_ <= 1:
            raise ValueError(f"verified capability {key} must be a number in [-1,1]")
    variance = capability.get("cross_harness_variance")
    if not isinstance(variance, (int, float)) or not 0 <= variance <= 1:
        raise ValueError("verified capability cross_harness_variance must be a number in [0,1]")


def validate_bundle(ref: str, release: dict, root: Path) -> tuple[str, str, str]:
    path = repo_path(root, ref, "release evidence bundle")
    bundle = load_object(path, "release evidence bundle")
    if bundle.get("schema_version") != "skill-eval-evidence/v1":
        raise ValueError(f"unsupported release evidence schema: {ref}")
    if bundle.get("promotion_eligible") is not True:
        raise ValueError(f"release evidence is not promotion eligible: {ref}")
    if bundle.get("skill_sha") != release.get("skill_sha"):
        raise ValueError(f"release evidence skill_sha mismatch: {ref}")
    if bundle.get("eval_suite_sha") != release.get("eval_suite_sha"):
        raise ValueError(f"release evidence eval_suite_sha mismatch: {ref}")

    receipt_path = repo_path(root, str(bundle.get("verifier_receipt", "")), "verifier receipt")
    expected_digest = bundle.get("verifier_receipt_sha256")
    if not isinstance(expected_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_digest) or expected_digest != digest(receipt_path):
        raise ValueError(f"verifier receipt digest mismatch: {ref}")
    receipt = load_object(receipt_path, "verifier receipt")
    if receipt.get("schema_version") != "skill-eval-verifier-receipt/v1":
        raise ValueError(f"unsupported verifier receipt schema: {ref}")
    if receipt.get("authority") != "deterministic" or receipt.get("passed") is not True:
        raise ValueError(f"release lacks passing deterministic verifier authority: {ref}")

    run_path = repo_path(root, str(bundle.get("run_trace", "")), "run trace")
    run = load_object(run_path, "run trace")
    if run.get("schema_version") != "skill-eval-run/v1":
        raise ValueError(f"unsupported run trace schema: {ref}")
    if run.get("run_id") != bundle.get("run_id") or receipt.get("run_id") != bundle.get("run_id"):
        raise ValueError(f"release run identity mismatch: {ref}")
    if run.get("case_id") != bundle.get("case_id") or receipt.get("case_id") != bundle.get("case_id"):
        raise ValueError(f"release case identity mismatch: {ref}")
    if run.get("skill_sha") != release.get("skill_sha"):
        raise ValueError(f"release run skill_sha mismatch: {ref}")
    model = run.get("model") if isinstance(run.get("model"), dict) else {}
    harness = run.get("harness") if isinstance(run.get("harness"), dict) else {}
    environment = run.get("environment") if isinstance(run.get("environment"), dict) else {}
    identity = (str(model.get("name", "")), str(harness.get("name", "")), str(environment.get("runtime", "")))
    if not all(identity):
        raise ValueError(f"release run lacks model/harness/environment identity: {ref}")
    return identity


def validate_release(release: dict, unlocks: dict[str, dict], root: Path) -> None:
    required = {
        "schema_version", "id", "skill", "skill_sha", "eval_suite_sha", "capability_unlock_id",
        "model_harness_matrix", "evidence_bundles", "rollback_sha", "rollback_artifact",
        "rollback_sha256", "scorecard", "human_admit",
    }
    missing = required - release.keys()
    if missing:
        raise ValueError(f"release missing fields: {', '.join(sorted(missing))}")
    if set(release) != required:
        raise ValueError(f"release has unsupported fields: {', '.join(sorted(set(release) - required))}")
    if release.get("schema_version") != "skill-release-receipt/v1":
        raise ValueError("unsupported release receipt schema")
    if not isinstance(release.get("id"), str) or len(release["id"]) < 3 or not NAME.fullmatch(release["id"]):
        raise ValueError("release id must be a stable lowercase slug")
    if not isinstance(release.get("skill"), str) or not NAME.fullmatch(release["skill"]):
        raise ValueError("release skill must be a lowercase skill slug")
    if not isinstance(release.get("skill_sha"), str) or not EXACT_SHA.fullmatch(release["skill_sha"]):
        raise ValueError("release skill_sha must be an exact 40-char lowercase commit SHA")
    if not isinstance(release.get("eval_suite_sha"), str) or not HEX_SHA.fullmatch(release["eval_suite_sha"]):
        raise ValueError("release eval_suite_sha must be immutable lowercase hex")
    if not isinstance(release.get("rollback_sha"), str) or not HEX_SHA.fullmatch(release["rollback_sha"]):
        raise ValueError("release rollback_sha must be immutable lowercase hex")
    if release.get("rollback_sha") == release.get("skill_sha"):
        raise ValueError("rollback_sha must differ from promoted skill_sha")

    unlock_id = release["capability_unlock_id"]
    if not isinstance(unlock_id, str) or len(unlock_id) < 3:
        raise ValueError("release capability_unlock_id is invalid")
    unlock = unlocks.get(unlock_id)
    if unlock is None:
        raise ValueError(f"release references missing capability unlock {unlock_id}")
    if unlock.get("skill") != release.get("skill") or unlock.get("skill_sha") != release.get("skill_sha"):
        raise ValueError("release identity does not match capability unlock")

    rollback_path = repo_path(root, release["rollback_artifact"], "rollback artifact")
    if not rollback_path.is_file():
        raise ValueError(f"rollback artifact does not exist: {release['rollback_artifact']}")
    rollback_digest = release.get("rollback_sha256")
    if not isinstance(rollback_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", rollback_digest) or digest(rollback_path) != rollback_digest:
        raise ValueError("rollback artifact digest mismatch")

    bundles = release.get("evidence_bundles")
    if not isinstance(bundles, list) or not bundles or len(bundles) != len(set(bundles)) or any(not isinstance(ref, str) or not ref for ref in bundles):
        raise ValueError("release evidence_bundles must be a non-empty unique string array")
    unlock_bundles = set(unlock.get("evidence_bundles", []))
    if not unlock_bundles.issubset(set(bundles)):
        raise ValueError("release omits evidence used by its capability unlock")
    observed = {validate_bundle(ref, release, root) for ref in bundles}

    matrix = release.get("model_harness_matrix")
    if not isinstance(matrix, list) or len(matrix) < 2:
        raise ValueError("release requires at least two model/harness matrix entries")
    expected = set()
    for item in matrix:
        if not isinstance(item, dict) or set(item) != {"model", "harness", "environment"}:
            raise ValueError("model_harness_matrix entries must contain only model/harness/environment")
        identity = (str(item.get("model", "")), str(item.get("harness", "")), str(item.get("environment", "")))
        if not all(identity):
            raise ValueError("model_harness_matrix entry is incomplete")
        expected.add(identity)
    if len(expected) < 2:
        raise ValueError("release requires at least two distinct model/harness stacks")
    if not expected.issubset(observed):
        raise ValueError("release evidence does not cover every model/harness matrix entry")

    admit = release.get("human_admit")
    if not isinstance(admit, dict) or set(admit) != {"actor", "admitted_at"} or not str(admit.get("actor", "")).strip() or len(str(admit.get("admitted_at", ""))) < 10:
        raise ValueError("release requires explicit human_admit actor and timestamp")
    validate_scorecard(release["scorecard"], release, unlock_id, root)


def check(root: Path) -> tuple[int, list[str]]:
    try:
        unlock_registry = load_object(root / "evals" / "capability-unlocks.json", "capability unlock registry")
        releases = load_object(root / "evals" / "releases.json", "release registry")
    except ValueError as exc:
        return 0, [str(exc)]
    unlock_list = unlock_registry.get("unlocks")
    release_list = releases.get("releases")
    if unlock_registry.get("schema_version") != "capability-unlock-registry/v1" or not isinstance(unlock_list, list):
        return 0, ["invalid capability unlock registry"]
    if releases.get("schema_version") != "skill-release-registry/v1" or not isinstance(release_list, list):
        return 0, ["invalid release registry"]
    unlocks: dict[str, dict] = {}
    for item in unlock_list:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            return 0, ["capability unlock registry contains an invalid unlock"]
        if item["id"] in unlocks:
            return 0, [f"duplicate capability unlock id {item['id']}"]
        unlocks[item["id"]] = item
    errors: list[str] = []
    seen: set[str] = set()
    for index, release in enumerate(release_list):
        if not isinstance(release, dict):
            errors.append(f"releases[{index}] must be an object")
            continue
        release_id = str(release.get("id", ""))
        if not release_id or release_id in seen:
            errors.append(f"releases[{index}] has missing/duplicate id {release_id!r}")
            continue
        seen.add(release_id)
        try:
            validate_release(release, unlocks, root)
        except ValueError as exc:
            errors.append(f"releases[{index}] {release_id}: {exc}")
    return len(release_list), errors


def main() -> int:
    count, errors = check(ROOT)
    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        return 1
    print(f"PASS verified capability releases: {count} release(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
