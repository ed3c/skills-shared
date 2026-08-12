#!/usr/bin/env python3
"""Fail closed on mutation lineage and recompute terminal outcomes from evidence."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MUTATIONS = ROOT / "mutations"
SHA_RE = re.compile(r"^[0-9a-f]{7,64}$")
CLASSES = {"trigger", "routing", "knowledge", "tool-contract", "verification", "recovery", "context-management", "example", "negative-instruction"}
STATUSES = {"proposed", "running", "won", "lost", "tie", "reverted"}
TERMINAL = {"won", "lost", "tie", "reverted"}
METRICS = {"task_pass_rate", "routing_f1", "recovery_rate", "safety_pass_rate", "capability_unlock_count"}
ARMS = ("parent", "candidate", "no_skill")


def nonempty_list(value, name):
    if not isinstance(value, list) or not value or len(value) != len(set(value)) or any(not isinstance(x, str) or not x.strip() for x in value):
        raise ValueError(f"{name} must be a non-empty unique string array")


def _load_object(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object: {path}")
    return value


def _repo_path(root: Path, ref: str, label: str) -> Path:
    if not isinstance(ref, str) or not ref.strip():
        raise ValueError(f"{label} must be a non-empty repository-relative path")
    candidate = Path(ref)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"{label} must be a repository-relative path")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} escapes repository root") from exc
    return resolved


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bundle_observation(ref: str, record: dict, receipt: dict, root: Path) -> tuple[str, str, bool]:
    bundle_path = _repo_path(root, ref, "mutation evidence bundle")
    bundle = _load_object(bundle_path, "mutation evidence bundle")
    if bundle.get("schema_version") != "skill-eval-evidence/v1":
        raise ValueError(f"unsupported mutation evidence bundle schema: {ref}")
    case_id = bundle.get("case_id")
    allowed_cases = set(receipt["target_case_ids"]) | set(receipt["non_target_case_ids"])
    if case_id not in allowed_cases:
        raise ValueError(f"mutation evidence case is outside receipt case set: {ref}")

    verifier_path = _repo_path(root, str(bundle.get("verifier_receipt", "")), "verifier receipt")
    verifier = _load_object(verifier_path, "verifier receipt")
    if verifier.get("schema_version") != "skill-eval-verifier-receipt/v1" or verifier.get("authority") != "deterministic":
        raise ValueError(f"mutation evidence lacks deterministic verifier authority: {ref}")
    passed = verifier.get("passed")
    if not isinstance(passed, bool):
        raise ValueError(f"verifier receipt must carry boolean passed: {ref}")
    expected_receipt_hash = bundle.get("verifier_receipt_sha256")
    if not isinstance(expected_receipt_hash, str) or expected_receipt_hash != _sha256(verifier_path):
        raise ValueError(f"verifier receipt digest mismatch: {ref}")

    run_path = _repo_path(root, str(bundle.get("run_trace", "")), "run trace")
    run = _load_object(run_path, "run trace")
    if run.get("schema_version") != "skill-eval-run/v1":
        raise ValueError(f"unsupported mutation run trace schema: {ref}")
    if run.get("run_id") != bundle.get("run_id") or verifier.get("run_id") != bundle.get("run_id"):
        raise ValueError(f"mutation run identity mismatch: {ref}")
    if run.get("case_id") != case_id or verifier.get("case_id") != case_id:
        raise ValueError(f"mutation case identity mismatch: {ref}")
    outcome = run.get("outcome") if isinstance(run.get("outcome"), dict) else {}
    if outcome.get("passed") is not passed:
        raise ValueError(f"run/verifier outcome disagreement: {ref}")
    if bundle.get("promotion_eligible") is not passed:
        raise ValueError(f"bundle promotion flag disagrees with deterministic outcome: {ref}")
    if bundle.get("skill_sha") != run.get("skill_sha"):
        raise ValueError(f"bundle/run skill SHA mismatch: {ref}")

    skill_sha = run.get("skill_sha")
    if skill_sha == record["parent_sha"]:
        arm = "parent"
    elif skill_sha == record["candidate_sha"]:
        arm = "candidate"
    elif skill_sha is None:
        arm = "no_skill"
    else:
        raise ValueError(f"mutation evidence belongs to neither parent, candidate, nor no-skill baseline: {ref}")
    return str(case_id), arm, passed


def _macro_rate(observations: dict[tuple[str, str], list[bool]], cases: list[str], arm: str) -> float:
    rates = []
    for case_id in cases:
        values = observations[(case_id, arm)]
        rates.append(sum(values) / len(values))
    return sum(rates) / len(rates)


def evaluate_receipt(record: dict, root: Path) -> tuple[float, float]:
    ref = record.get("evaluation_receipt")
    receipt_path = _repo_path(root, ref, "mutation evaluation receipt")
    receipt = _load_object(receipt_path, "mutation evaluation receipt")
    if receipt.get("schema_version") != "skill-mutation-eval/v1":
        raise ValueError("unsupported mutation evaluation receipt schema")
    for field in ("skill", "parent_sha", "candidate_sha"):
        if receipt.get(field) != record.get(field):
            raise ValueError(f"mutation evaluation receipt {field} mismatch")
    effect = record["expected_effect"]
    if receipt.get("metric") != effect.get("metric"):
        raise ValueError("mutation evaluation receipt metric mismatch")
    if receipt.get("metric") != "task_pass_rate":
        raise ValueError("terminal mutation admission currently supports only task_pass_rate")

    targets = receipt.get("target_case_ids")
    non_targets = receipt.get("non_target_case_ids")
    bundles = receipt.get("evidence_bundles")
    nonempty_list(targets, "mutation receipt target_case_ids")
    nonempty_list(non_targets, "mutation receipt non_target_case_ids")
    nonempty_list(bundles, "mutation receipt evidence_bundles")
    if set(targets) != set(effect.get("case_ids", [])):
        raise ValueError("mutation receipt target cases do not match expected_effect.case_ids")
    overlap = set(targets) & set(non_targets)
    if overlap:
        raise ValueError(f"target and non-target mutation cases overlap: {', '.join(sorted(overlap))}")

    observations: dict[tuple[str, str], list[bool]] = defaultdict(list)
    for bundle_ref in bundles:
        case_id, arm, passed = _bundle_observation(bundle_ref, record, receipt, root)
        observations[(case_id, arm)].append(passed)

    for case_id in [*targets, *non_targets]:
        counts = {arm: len(observations[(case_id, arm)]) for arm in ARMS}
        if any(count == 0 for count in counts.values()):
            raise ValueError(
                f"mutation evidence lacks paired current/candidate/no-skill observations for {case_id}: "
                + ", ".join(f"{arm}={counts[arm]}" for arm in ARMS)
            )
        if len(set(counts.values())) != 1:
            raise ValueError(
                f"mutation evidence denominator mismatch for {case_id}: "
                + ", ".join(f"{arm}={counts[arm]}" for arm in ARMS)
            )

    parent_target = _macro_rate(observations, targets, "parent")
    candidate_target = _macro_rate(observations, targets, "candidate")
    target_delta = candidate_target - parent_target
    parent_non_target = _macro_rate(observations, non_targets, "parent")
    candidate_non_target = _macro_rate(observations, non_targets, "candidate")
    regression = max(0.0, parent_non_target - candidate_non_target)

    # No-skill is deliberately not part of the win formula. It is an experiment
    # baseline that must be observed with the same cases/repetitions so future
    # analysis can distinguish skill lift from task/model drift.
    _macro_rate(observations, targets, "no_skill")
    _macro_rate(observations, non_targets, "no_skill")
    return target_delta, regression


def validate(record: dict, root: Path | None = None) -> None:
    required = {"schema_version", "skill", "parent_sha", "candidate_sha", "hypothesis", "mutation_class", "target_failures", "changed_sections", "expected_effect", "regression_budget", "status", "rollback_sha"}
    missing = sorted(required - record.keys())
    if missing:
        raise ValueError(f"missing fields: {', '.join(missing)}")
    if record["schema_version"] != "skill-mutation/v1":
        raise ValueError("unsupported schema_version")
    if not isinstance(record["skill"], str) or not record["skill"]:
        raise ValueError("skill required")
    if not SHA_RE.fullmatch(str(record["parent_sha"])) or not SHA_RE.fullmatch(str(record["candidate_sha"])) or not SHA_RE.fullmatch(str(record["rollback_sha"])):
        raise ValueError("parent/candidate/rollback SHA must be immutable lowercase hex")
    if record["parent_sha"] == record["candidate_sha"]:
        raise ValueError("candidate_sha must differ from parent_sha")
    if record["rollback_sha"] != record["parent_sha"]:
        raise ValueError("rollback_sha must pin the parent candidate was derived from")
    if not isinstance(record["hypothesis"], str) or len(record["hypothesis"].strip()) < 10:
        raise ValueError("one explicit hypothesis is required")
    if record["mutation_class"] not in CLASSES:
        raise ValueError("invalid mutation_class")
    if record["status"] not in STATUSES:
        raise ValueError("invalid status")
    nonempty_list(record["target_failures"], "target_failures")
    nonempty_list(record["changed_sections"], "changed_sections")
    effect = record["expected_effect"]
    if not isinstance(effect, dict) or effect.get("metric") not in METRICS or not isinstance(effect.get("minimum_delta"), (int, float)):
        raise ValueError("expected_effect metric/minimum_delta invalid")
    if effect["minimum_delta"] <= 0:
        raise ValueError("expected_effect.minimum_delta must be positive for an optimization mutation")
    nonempty_list(effect.get("case_ids"), "expected_effect.case_ids")
    if not isinstance(record["regression_budget"], (int, float)) or record["regression_budget"] < 0:
        raise ValueError("regression_budget must be non-negative")

    status = record["status"]
    evaluation_receipt = record.get("evaluation_receipt")
    if status in TERMINAL and not evaluation_receipt:
        raise ValueError("terminal mutation status requires evaluation_receipt")
    if status not in TERMINAL and evaluation_receipt:
        raise ValueError("proposed/running mutation must not claim a terminal evaluation_receipt")
    if status in TERMINAL and root is not None:
        delta, regression = evaluate_receipt(record, root)
        qualifies = delta >= float(effect["minimum_delta"]) and regression <= float(record["regression_budget"])
        if status == "won" and not qualifies:
            raise ValueError(
                f"mutation marked won but evidence fails admission: target_delta={delta:.6f}, regression={regression:.6f}"
            )
        if status == "lost" and qualifies:
            raise ValueError("mutation marked lost but deterministic evidence meets win thresholds")
        if status == "tie" and abs(delta) > 1e-12:
            raise ValueError(f"mutation marked tie but target_delta is {delta:.6f}, not zero")


def main() -> int:
    errors, count = [], 0
    for path in sorted(MUTATIONS.rglob("*.jsonl")) if MUTATIONS.exists() else []:
        if "schema" in path.parts:
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            count += 1
            try:
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError("record must be object")
                validate(value, ROOT)
            except (json.JSONDecodeError, ValueError) as exc:
                errors.append(f"{path.relative_to(ROOT)}:{number}: {exc}")
    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        return 1
    print(f"PASS mutation lineage: {count} records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
