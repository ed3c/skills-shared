#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
SKILL_ROOT = TEST_DIR.parent.parent
CHECKER = SKILL_ROOT / "scripts" / "check_multi_agent_runtime.py"
SCHEMA_ROOT = SKILL_ROOT / "references"
GOOD = TEST_DIR / "fixtures" / "valid-multi.json"


def run(document: dict) -> tuple[int, str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "contract.json"
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        process = subprocess.run(
            [sys.executable, str(CHECKER), str(path), "--schema-root", str(SCHEMA_ROOT)],
            text=True,
            capture_output=True,
            check=False,
        )
        return process.returncode, process.stdout, process.stderr


def mutate(name: str, document: dict) -> None:
    if name == "admission-false":
        document["admission"]["independent_oracles"] = False
    elif name == "path-overlap":
        document["tasks"][1]["allowed_paths"] = ["src/parser/generated"]
    elif name == "dependency-cycle":
        document["tasks"][0]["dependencies"] = ["worker-b"]
        document["tasks"][1]["dependencies"] = ["worker-a"]
    elif name == "duplicate-attempt":
        document["tasks"][1]["attempt_id"] = document["tasks"][0]["attempt_id"]
        document["results"][1]["attempt_id"] = document["results"][0]["attempt_id"]
    elif name == "budget-exceeded":
        document["budget"]["consumed"]["tokens"] = 50001
    elif name == "missing-profile-fanout":
        document["budget"]["profile_state"] = "ABSENT"
        document["budget"]["limits"]["active_workers"] = 1
        document["budget"]["limits"]["total_workers"] = 1
    elif name == "shadow-overclaim":
        document["shadow"]["execution"] = "IN_PROCESS_LOGICAL"
        document["shadow"]["independent_state"] = "PASS"
    elif name == "l3-bypass":
        document["shadow"]["checkpoint_outcome"] = "BLOCKED_AT_MATERIAL_BOUNDARY_L3"
        document["shadow"]["enforcement_state"] = "NOT_IMPLEMENTED"
    elif name == "agent-merge-enabled":
        document["merge_boundary"]["agent_merge_action"] = "ALLOW"
    elif name == "stale-result":
        document["results"][0]["base_subject_sha"] = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
    elif name == "outside-lease":
        document["results"][0]["owned_paths"] = ["src/runtime"]
    elif name == "verified-fail":
        document["results"][0]["negative_controls"][0]["state"] = "FAIL"
    elif name == "missing-result":
        document["results"].pop(0)
        document["budget"]["consumed"]["tool_calls"] = 10
        document["budget"]["consumed"]["tokens"] = 2000
        document["budget"]["consumed"]["wall_clock_seconds"] = 110
    elif name == "duplicate-branch":
        document["tasks"][1]["branch"] = document["tasks"][0]["branch"]
    elif name == "unknown-dependency":
        document["tasks"][0]["dependencies"] = ["worker-z"]
    elif name == "invalid-evidence-state":
        document["states"]["evidence_state"] = "EXTERNAL_AUTHORITY_REQUIRED"
    elif name == "budget-ledger-mismatch":
        document["budget"]["consumed"]["tool_calls"] = 20
    elif name == "single-builder-cardinality":
        document["topology"] = "SINGLE_BUILDER"
    elif name == "resource-overlap":
        document["tasks"][1]["external_resource_leases"] = ["fixture-set-parser"]
    elif name == "merged-without-observation":
        document["states"]["delivery_state"] = "MERGED"
    elif name == "unknown-runtime-published":
        document["runtime"]["identity"] = "UNKNOWN"
    else:
        raise AssertionError(f"unknown mutation: {name}")


def main() -> int:
    good = json.loads(GOOD.read_text(encoding="utf-8"))
    code, stdout, stderr = run(good)
    failures: list[str] = []
    if code != 0 or "RUNTIME-CONTRACT-GREEN" not in stdout or stderr:
        failures.append(f"positive multi fixture: code={code} stdout={stdout!r} stderr={stderr!r}")

    single = copy.deepcopy(good)
    single["topology"] = "SINGLE_BUILDER"
    single["budget"]["profile_state"] = "ABSENT"
    single["budget"]["limits"]["active_workers"] = 1
    single["budget"]["limits"]["total_workers"] = 1
    single["budget"]["consumed"]["active_workers"] = 1
    single["budget"]["consumed"]["total_workers"] = 1
    single["budget"]["consumed"]["tool_calls"] = 9
    single["budget"]["consumed"]["tokens"] = 1500
    single["budget"]["consumed"]["wall_clock_seconds"] = 80
    single["tasks"] = single["tasks"][:1]
    single["results"] = single["results"][:1]
    code, stdout, stderr = run(single)
    if code != 0 or "topology=SINGLE_BUILDER" not in stdout or stderr:
        failures.append(f"positive fallback fixture: code={code} stdout={stdout!r} stderr={stderr!r}")

    cases = [
        ("admission-false", 2, "parallelism-not-admitted"),
        ("path-overlap", 2, "path-lease-overlap"),
        ("dependency-cycle", 2, "dependency-cycle"),
        ("duplicate-attempt", 2, "duplicate-attempt-id"),
        ("budget-exceeded", 2, "budget-exceeded:tokens"),
        ("missing-profile-fanout", 2, "missing-profile-fanout"),
        ("shadow-overclaim", 2, "shadow-independence-overclaim"),
        ("l3-bypass", 2, "shadow-l3-unenforced"),
        ("agent-merge-enabled", 64, "schema-invalid"),
        ("stale-result", 2, "stale-result-base"),
        ("outside-lease", 2, "result-outside-path-lease"),
        ("verified-fail", 2, "verified-result-nonpass"),
        ("missing-result", 2, "verified-task-missing-result"),
        ("duplicate-branch", 2, "duplicate-branch"),
        ("unknown-dependency", 2, "unknown-dependency"),
        ("invalid-evidence-state", 64, "schema-invalid"),
        ("budget-ledger-mismatch", 2, "budget-ledger-mismatch"),
        ("single-builder-cardinality", 2, "single-builder-cardinality"),
        ("resource-overlap", 2, "resource-lease-overlap"),
        ("merged-without-observation", 2, "merged-without-external-observation"),
        ("unknown-runtime-published", 2, "unknown-runtime-published"),
    ]

    for name, expected_code, marker in cases:
        document = copy.deepcopy(good)
        mutate(name, document)
        code, stdout, stderr = run(document)
        if code != expected_code or marker not in stderr:
            failures.append(
                f"{name}: expected code={expected_code} marker={marker!r}; "
                f"got code={code} stdout={stdout!r} stderr={stderr!r}"
            )

    process = subprocess.run(
        [sys.executable, str(CHECKER), str(TEST_DIR / "fixtures" / "absent.json")],
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != 64 or "absent-input" not in process.stderr:
        failures.append(
            f"absent input: expected 64/absent-input, got {process.returncode} {process.stderr!r}"
        )

    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        return 1

    print(
        "PASS multi-agent-runtime: positive multi-worker and single-builder fallback fixtures admitted; "
        f"{len(cases)} planted topology, lease, budget, Shadow, evidence, result, "
        "and merge-boundary defects refused; absent input stayed distinct"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
