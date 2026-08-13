#!/usr/bin/env python3
"""Verify repo-agent-native output artifacts with case-specific hard gates."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCHEMA = "repo-agent-native-output/v2"
CASES = {
    "repo-agent-source-anchored-invariants",
    "repo-agent-degraded-provider-fallback",
    "repo-agent-memory-conflict",
    "repo-agent-graph-impact-readback",
}
EVIDENCE_LEVELS = {"A", "A-", "B+", "B", "C", "D"}
CONFIRMED_LEVELS = {"A", "A-"}
PROVIDER_STATES = {
    "PASS",
    "FAIL",
    "ABSENT",
    "NOT_IMPLEMENTED",
    "NOT_EXERCISED",
    "SKIPPED_BY_POLICY",
}


def load_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def source_refs(record: dict) -> list[str]:
    value = record.get("source_refs")
    if not isinstance(value, list):
        return []
    return [item for item in value if nonempty_string(item)]


def validate_common(output: dict) -> list[str]:
    errors: list[str] = []
    if output.get("schema_version") != SCHEMA:
        errors.append(f"schema_version must be {SCHEMA}")
    if output.get("selected_skill") != "repo-agent-native":
        errors.append("selected_skill must be repo-agent-native")

    subject = output.get("subject")
    if not isinstance(subject, dict):
        errors.append("subject must be an object")
    else:
        if not nonempty_string(subject.get("root")):
            errors.append("subject.root is required")
        commit = subject.get("commit")
        if not nonempty_string(commit) or len(commit.strip()) < 7:
            errors.append("subject.commit must be an immutable-looking identity")

    routes = output.get("routes")
    if not isinstance(routes, list):
        errors.append("routes must be an array")

    invariants = output.get("invariants")
    if not isinstance(invariants, list) or not invariants:
        errors.append("invariants must be a non-empty array")
        invariants = []
    for index, record in enumerate(invariants):
        label = f"invariants[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label} must be an object")
            continue
        for field in ("id", "claim", "status", "evidence_level"):
            if not nonempty_string(record.get(field)):
                errors.append(f"{label}.{field} is required")
        level = record.get("evidence_level")
        status = record.get("status")
        if level not in EVIDENCE_LEVELS:
            errors.append(f"{label}.evidence_level is unsupported")
        if status == "confirmed":
            if level not in CONFIRMED_LEVELS:
                errors.append(f"{label}: confirmed claim exceeds evidence ceiling {level}")
            if not source_refs(record):
                errors.append(f"{label}: confirmed claim requires source_refs")
        if level == "D":
            errors.append(f"{label}: unsupported D-level assumption must not enter output")

    observations = output.get("provider_observations")
    if not isinstance(observations, list):
        errors.append("provider_observations must be an array")
        observations = []
    for index, record in enumerate(observations):
        label = f"provider_observations[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label} must be an object")
            continue
        if not nonempty_string(record.get("capability")):
            errors.append(f"{label}.capability is required")
        state = record.get("state")
        if state not in PROVIDER_STATES:
            errors.append(f"{label}.state is unsupported")
        if not nonempty_string(record.get("evidence_ceiling")):
            errors.append(f"{label}.evidence_ceiling is required")
        if state != "PASS" and not nonempty_string(record.get("fallback")):
            errors.append(f"{label}: non-PASS provider state requires fallback")

    if not isinstance(output.get("unresolved"), list):
        errors.append("unresolved must be an array")
    if not isinstance(output.get("assertions"), dict):
        errors.append("assertions must be an object")
    handoff = output.get("handoff")
    if not isinstance(handoff, dict):
        errors.append("handoff must be an object")
    else:
        if not nonempty_string(handoff.get("human_admit")):
            errors.append("handoff.human_admit is required")
        if not nonempty_string(handoff.get("rollback_subject")):
            errors.append("handoff.rollback_subject is required")
    return errors


def validate_source_case(output: dict) -> list[str]:
    errors: list[str] = []
    confirmed = [
        record
        for record in output.get("invariants", [])
        if isinstance(record, dict) and record.get("status") == "confirmed"
    ]
    if not confirmed:
        errors.append("source case requires at least one confirmed source invariant")
    negatives = output.get("negative_invariants")
    if not isinstance(negatives, list) or not negatives:
        errors.append("source case requires negative_invariants")
    else:
        for index, record in enumerate(negatives):
            if not isinstance(record, dict):
                errors.append(f"negative_invariants[{index}] must be an object")
                continue
            if not nonempty_string(record.get("search_boundary")):
                errors.append(f"negative_invariants[{index}].search_boundary is required")
            if not nonempty_string(record.get("claim")):
                errors.append(f"negative_invariants[{index}].claim is required")
    return errors


def validate_degraded_case(output: dict) -> list[str]:
    observations = output.get("provider_observations", [])
    degraded = [
        record
        for record in observations
        if isinstance(record, dict) and record.get("state") != "PASS"
    ]
    if not degraded:
        return ["degraded-provider case requires at least one explicit non-PASS provider observation"]
    return []


def validate_memory_case(output: dict) -> list[str]:
    conflicts = output.get("memory_conflicts")
    if not isinstance(conflicts, list) or not conflicts:
        return ["memory case requires at least one memory_conflict"]
    errors: list[str] = []
    for index, conflict in enumerate(conflicts):
        if not isinstance(conflict, dict):
            errors.append(f"memory_conflicts[{index}] must be an object")
            continue
        if conflict.get("resolution") != "current_authority_wins":
            errors.append(f"memory_conflicts[{index}]: current authority must win")
        if not source_refs(conflict):
            errors.append(f"memory_conflicts[{index}]: winning authority requires source_refs")
    return errors


def validate_graph_case(output: dict) -> list[str]:
    edges = output.get("impact_edges")
    if not isinstance(edges, list) or not edges:
        return ["graph case requires impact_edges"]
    errors: list[str] = []
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            errors.append(f"impact_edges[{index}] must be an object")
            continue
        if not nonempty_string(edge.get("from")) or not nonempty_string(edge.get("to")):
            errors.append(f"impact_edges[{index}]: from and to are required")
        if edge.get("status") == "confirmed" and not source_refs(edge):
            errors.append(f"impact_edges[{index}]: confirmed edge requires source readback refs")
        if edge.get("status") not in {"candidate", "confirmed", "unresolved"}:
            errors.append(f"impact_edges[{index}].status is unsupported")
    return errors


def validate(case_id: str, output: dict) -> list[str]:
    if case_id not in CASES:
        return [f"unsupported case: {case_id}"]
    errors = validate_common(output)
    if case_id == "repo-agent-source-anchored-invariants":
        errors.extend(validate_source_case(output))
    elif case_id == "repo-agent-degraded-provider-fallback":
        errors.extend(validate_degraded_case(output))
    elif case_id == "repo-agent-memory-conflict":
        errors.extend(validate_memory_case(output))
    elif case_id == "repo-agent-graph-impact-readback":
        errors.extend(validate_graph_case(output))
    return sorted(set(errors))


def emit_report(case_id: str, output_path: Path, errors: list[str], report_path: Path | None) -> None:
    report = {
        "schema_version": "repo-agent-native-verifier-report/v1",
        "case_id": case_id,
        "output": str(output_path),
        "state": "PASS" if not errors else "FAIL",
        "errors": errors,
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(text, encoding="utf-8")
    stream = sys.stdout if not errors else sys.stderr
    print(text, end="", file=stream)


def fixture_output(root: Path) -> Path:
    return root / "artifacts" / "repo-analysis.json"


def selftest(repo_root: Path) -> int:
    fixture_root = repo_root / "evals" / "fixtures" / "repo-agent-native"
    positive = fixture_output(fixture_root / "positive")
    negatives = {
        "repo-agent-source-anchored-invariants": fixture_output(fixture_root / "unsupported-claim"),
        "repo-agent-degraded-provider-fallback": fixture_output(fixture_root / "missing-fallback"),
        "repo-agent-memory-conflict": fixture_output(fixture_root / "memory-wins"),
        "repo-agent-graph-impact-readback": fixture_output(fixture_root / "graph-no-readback"),
    }
    for case_id in sorted(CASES):
        positive_errors = validate(case_id, load_object(positive))
        if positive_errors:
            print(f"SELFTEST positive failed for {case_id}: {positive_errors}", file=sys.stderr)
            return 1
        negative_errors = validate(case_id, load_object(negatives[case_id]))
        if not negative_errors:
            print(f"SELFTEST planted negative unexpectedly passed for {case_id}", file=sys.stderr)
            return 1
    print("PASS repo-agent-native output verifier selftest: 4 positive + 4 planted negatives")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=sorted(CASES))
    parser.add_argument("--output", type=Path, default=Path("artifacts/repo-analysis.json"))
    parser.add_argument("--report", type=Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    repo_root = Path(__file__).resolve().parents[2]
    if args.selftest:
        return selftest(repo_root)
    if not args.case:
        parser.error("--case is required unless --selftest is used")
    try:
        output = load_object(args.output)
        errors = validate(args.case, output)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors = [str(exc)]
    emit_report(args.case, args.output, errors, args.report)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
