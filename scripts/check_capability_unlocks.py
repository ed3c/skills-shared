#!/usr/bin/env python3
"""Validate capability-unlock registry against landed promotion evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "evals" / "capability-unlocks.json"


def _load_object(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object: {path}")
    return value


def _repo_path(root: Path, ref: str, label: str) -> Path:
    candidate = Path(ref)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"{label} must be a repository-relative path")
    resolved = (root / candidate).resolve()
    if root.resolve() not in resolved.parents and resolved != root.resolve():
        raise ValueError(f"{label} escapes repository root")
    return resolved


def validate_bundle_ref(ref: str, unlock: dict, root: Path) -> tuple[str, tuple[str, str]]:
    path = _repo_path(root, ref, "evidence bundle")
    bundle = _load_object(path, "evidence bundle")
    if bundle.get("schema_version") != "skill-eval-evidence/v1":
        raise ValueError(f"unsupported evidence bundle schema: {ref}")
    if bundle.get("promotion_eligible") is not True:
        raise ValueError(f"evidence bundle is not promotion eligible: {ref}")
    if bundle.get("skill_sha") != unlock.get("skill_sha"):
        raise ValueError(f"evidence bundle skill_sha mismatch: {ref}")
    case_id = bundle.get("case_id")
    if case_id not in unlock.get("case_ids", []):
        raise ValueError(f"evidence bundle case is outside unlock case set: {ref}")

    receipt_path = _repo_path(root, str(bundle.get("verifier_receipt", "")), "verifier receipt")
    receipt = _load_object(receipt_path, "verifier receipt")
    if receipt.get("schema_version") != "skill-eval-verifier-receipt/v1":
        raise ValueError(f"unsupported verifier receipt schema: {ref}")
    if receipt.get("authority") != "deterministic" or receipt.get("passed") is not True:
        raise ValueError(f"bundle lacks passing deterministic verifier authority: {ref}")
    if receipt.get("run_id") != bundle.get("run_id") or receipt.get("case_id") != case_id:
        raise ValueError(f"verifier receipt identity mismatch: {ref}")

    run_path = _repo_path(root, str(bundle.get("run_trace", "")), "run trace")
    run = _load_object(run_path, "run trace")
    if run.get("schema_version") != "skill-eval-run/v1":
        raise ValueError(f"unsupported run trace schema: {ref}")
    if run.get("run_id") != bundle.get("run_id") or run.get("case_id") != case_id:
        raise ValueError(f"run trace identity mismatch: {ref}")
    if run.get("skill_sha") != unlock.get("skill_sha"):
        raise ValueError(f"run trace skill_sha mismatch: {ref}")
    model = run.get("model") if isinstance(run.get("model"), dict) else {}
    harness = run.get("harness") if isinstance(run.get("harness"), dict) else {}
    stack = (str(model.get("name", "")), str(harness.get("name", "")))
    return str(case_id), stack


def validate_unlock(value: dict, root: Path | None = None) -> None:
    required = {"schema_version", "id", "skill", "skill_sha", "case_ids", "baseline", "candidate", "supported_stacks", "evidence_bundles"}
    missing = required - value.keys()
    if missing:
        raise ValueError(f"missing fields: {', '.join(sorted(missing))}")
    if value["schema_version"] != "capability-unlock/v1":
        raise ValueError("unsupported unlock schema")
    skill_sha = value["skill_sha"]
    if not isinstance(skill_sha, str) or len(skill_sha) != 40 or any(c not in "0123456789abcdef" for c in skill_sha):
        raise ValueError("unlock skill_sha must be an exact lowercase 40-char commit SHA")
    cases = value["case_ids"]
    if not isinstance(cases, list) or len(set(cases)) < 6:
        raise ValueError("unlock requires at least six distinct held-out cases")
    baseline, candidate = value["baseline"], value["candidate"]
    total = int(baseline.get("total", 0))
    if total < 6 or int(candidate.get("total", 0)) != total:
        raise ValueError("baseline/candidate totals must match and be >= 6")
    if int(baseline.get("no_skill_passes", total)) > total / 6:
        raise ValueError("no-skill baseline is too capable for unlock claim")
    if int(baseline.get("current_skill_passes", total)) > total / 6:
        raise ValueError("current-skill baseline is too capable for unlock claim")
    if int(candidate.get("passes", 0)) < (2 * total) / 3:
        raise ValueError("candidate does not meet >= 2/3 held-out pass threshold")
    stacks = value["supported_stacks"]
    identities = {(s.get("model"), s.get("harness")) for s in stacks if isinstance(s, dict)}
    if len(identities) < 2:
        raise ValueError("unlock requires at least two distinct model/harness stacks")
    bundles = value["evidence_bundles"]
    if not isinstance(bundles, list) or not bundles:
        raise ValueError("unlock requires evidence bundles")
    for ref in bundles:
        if not isinstance(ref, str) or not ref.strip():
            raise ValueError("invalid evidence bundle reference")

    if root is not None:
        observed_cases: set[str] = set()
        observed_stacks: set[tuple[str, str]] = set()
        for ref in bundles:
            case_id, stack = validate_bundle_ref(ref, value, root)
            observed_cases.add(case_id)
            observed_stacks.add(stack)
        missing_cases = set(cases) - observed_cases
        if missing_cases:
            raise ValueError(f"evidence bundles do not cover unlock cases: {', '.join(sorted(missing_cases))}")
        if not identities.issubset(observed_stacks):
            raise ValueError("evidence bundles do not cover every supported model/harness stack")


def main() -> int:
    try:
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        if registry.get("schema_version") != "capability-unlock-registry/v1":
            raise ValueError("unsupported registry schema")
        unlocks = registry.get("unlocks")
        if not isinstance(unlocks, list):
            raise ValueError("unlocks must be an array")
        ids = set()
        for unlock in unlocks:
            if not isinstance(unlock, dict):
                raise ValueError("unlock must be object")
            validate_unlock(unlock, ROOT)
            if unlock["id"] in ids:
                raise ValueError(f"duplicate unlock id {unlock['id']}")
            ids.add(unlock["id"])
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"PASS capability unlock registry: {len(unlocks)} verified unlocks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
