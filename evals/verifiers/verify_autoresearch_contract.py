#!/usr/bin/env python3
"""Deterministically verify autoresearch-composer routing/outcome evidence.

The executor writes evidence/run.json in the case workspace. This verifier
checks the externally observable routing decision and, for capability/recovery
cases, the generated plan artifact. It does not inspect hidden chain-of-thought.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

EXPECTATIONS = {
    "autoresearch-metric-loop-plan": {
        "decision": "invoke",
        "selected_skill": "autoresearch-composer",
        "required_contract": ["Goal", "Scope", "Metric", "Direction", "Verify", "Guard", "Iterations"],
    },
    "autoresearch-yield-bug-diagnosis": {
        "decision": "delegate",
        "forbidden_skills": ["autoresearch-composer"],
        "allowed_delegates": ["diagnose", "diagnosing-bugs"],
    },
    "autoresearch-recover-compressed-context": {
        "decision": "recover",
        "selected_skill": "autoresearch-composer",
        "required_recovery": ["low_compression_context", "domain_terms", "known_unknowns"],
    },
    "autoresearch-holdout-no-verifier": {
        "decision": "delegate",
        "forbidden_skills": ["autoresearch-composer"],
        "required_reason": "no_numeric_verifier",
    },
}


def fail(message: str) -> int:
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True, choices=sorted(EXPECTATIONS))
    parser.add_argument("--evidence", default="evidence/run.json")
    args = parser.parse_args()

    try:
        evidence = load_json(Path(args.evidence))
    except ValueError as exc:
        return fail(str(exc))

    expected = EXPECTATIONS[args.case]
    if evidence.get("case_id") != args.case:
        return fail("evidence case_id does not match verifier case")
    if evidence.get("decision") != expected["decision"]:
        return fail(f"expected decision={expected['decision']!r}, got {evidence.get('decision')!r}")

    selected = evidence.get("selected_skill")
    if "selected_skill" in expected and selected != expected["selected_skill"]:
        return fail(f"expected selected_skill={expected['selected_skill']!r}, got {selected!r}")
    if selected in expected.get("forbidden_skills", []):
        return fail(f"forbidden skill selected: {selected}")
    if "allowed_delegates" in expected and selected not in expected["allowed_delegates"]:
        return fail(f"delegate {selected!r} is outside allowed native diagnostic skills")
    if evidence.get("reason") != expected.get("required_reason", evidence.get("reason")):
        return fail(f"required reason {expected['required_reason']!r} was not emitted")

    contract_fields = expected.get("required_contract", [])
    if contract_fields:
        artifact_path = evidence.get("plan_artifact")
        if not isinstance(artifact_path, str) or not artifact_path:
            return fail("plan_artifact path missing")
        try:
            artifact = load_json(Path(artifact_path))
        except ValueError as exc:
            return fail(str(exc))
        missing = [field for field in contract_fields if artifact.get(field) in (None, "", [])]
        if missing:
            return fail(f"iteration contract missing fields: {', '.join(missing)}")

    recovery_fields = expected.get("required_recovery", [])
    if recovery_fields:
        recovery = evidence.get("recovery")
        if not isinstance(recovery, dict):
            return fail("recovery object missing")
        missing = [field for field in recovery_fields if recovery.get(field) in (None, "", [])]
        if missing:
            return fail(f"recovery evidence missing fields: {', '.join(missing)}")

    print(f"PASS {args.case}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
