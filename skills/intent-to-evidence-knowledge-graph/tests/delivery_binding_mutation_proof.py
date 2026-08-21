#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_case_delivery_binding.py"
SCHEMA = ROOT / "references" / "case-delivery-binding.schema.json"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
BASE_BINDING = json.loads((FIXTURES / "valid-case-delivery-binding.json").read_text(encoding="utf-8"))
BASE_TASK = json.loads((FIXTURES / "delivery-task-contract.json").read_text(encoding="utf-8"))
BASE_TRACE = json.loads((FIXTURES / "delivery-trace-graph.json").read_text(encoding="utf-8"))

EXPECTED = {
    "NC-04": "FALSE_GIT_ANCESTRY",
    "NC-05": "FALSE_SERIAL_DEPENDENCY",
    "NC-06": "CASE_UNOWNED",
    "NC-07": "REVERSE_TRACE_INCOMPLETE",
    "CASE-DUPLICATE": "DUPLICATE_CASE_OWNER",
    "CASE-CONVERGENCE": "MISSING_CONVERGENCE_OWNER",
    "PATH-OVERLAP": "PATH_LEASE_OVERLAP",
}


def run(binding: dict, task: dict, trace: dict) -> tuple[int, dict]:
    with tempfile.TemporaryDirectory() as temp_dir:
        directory = Path(temp_dir)
        for name, value in [("binding.json", binding), ("task.json", task), ("trace.json", trace)]:
            (directory / name).write_text(json.dumps(value), encoding="utf-8")
        process = subprocess.run(
            [
                sys.executable,
                str(CHECKER),
                str(directory / "binding.json"),
                "--task-contract",
                str(directory / "task.json"),
                "--trace-graph",
                str(directory / "trace.json"),
                "--schema",
                str(SCHEMA),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        try:
            report = json.loads(process.stdout)
        except Exception as exc:
            raise AssertionError(
                f"checker did not emit JSON: rc={process.returncode} stdout={process.stdout!r} stderr={process.stderr!r}"
            ) from exc
        return process.returncode, report


def main() -> int:
    cases: dict[str, tuple[dict, dict, dict]] = {}

    binding = copy.deepcopy(BASE_BINDING)
    core = next(node for node in binding["stack_nodes"] if node["branch"] == "feature/core")
    core["relation"] = "TRUE_CHILD"
    core["consumed_artifacts"] = []
    cases["NC-04"] = (binding, copy.deepcopy(BASE_TASK), copy.deepcopy(BASE_TRACE))

    binding = copy.deepcopy(BASE_BINDING)
    core = next(node for node in binding["stack_nodes"] if node["branch"] == "feature/core")
    core["relation"] = "TRUE_CHILD"
    core["consumed_artifacts"] = ["issue-order-placeholder"]
    cases["NC-05"] = (binding, copy.deepcopy(BASE_TASK), copy.deepcopy(BASE_TRACE))

    binding = copy.deepcopy(BASE_BINDING)
    binding["case_bindings"] = [item for item in binding["case_bindings"] if item["case_id"] != "CASE-CORE"]
    cases["NC-06"] = (binding, copy.deepcopy(BASE_TASK), copy.deepcopy(BASE_TRACE))

    trace = copy.deepcopy(BASE_TRACE)
    file_core = next(artifact for artifact in trace["artifacts"] if artifact["artifact_id"] == "file-core")
    file_core["trace"]["case_ids"] = ["CASE-CONTRACT"]
    cases["NC-07"] = (copy.deepcopy(BASE_BINDING), copy.deepcopy(BASE_TASK), trace)

    binding = copy.deepcopy(BASE_BINDING)
    binding["case_bindings"].append(copy.deepcopy(binding["case_bindings"][0]))
    cases["CASE-DUPLICATE"] = (binding, copy.deepcopy(BASE_TASK), copy.deepcopy(BASE_TRACE))

    binding = copy.deepcopy(BASE_BINDING)
    binding["convergence_owner"] = "feature/contract"
    cases["CASE-CONVERGENCE"] = (binding, copy.deepcopy(BASE_TASK), copy.deepcopy(BASE_TRACE))

    binding = copy.deepcopy(BASE_BINDING)
    core = next(node for node in binding["stack_nodes"] if node["branch"] == "feature/core")
    core["relation"] = "SIBLING"
    core["consumed_artifacts"] = []
    core["owns_paths"][0] = "feature/contracts.py"
    cases["PATH-OVERLAP"] = (binding, copy.deepcopy(BASE_TASK), copy.deepcopy(BASE_TRACE))

    failures: list[str] = []
    results: list[dict] = []
    for name, (binding, task, trace) in cases.items():
        return_code, report = run(binding, task, trace)
        codes = {error["code"] for error in report.get("errors", [])}
        expected = EXPECTED[name]
        passed = return_code == 2 and report.get("status") == "BLOCK" and expected in codes
        results.append({"control": name, "expected": expected, "codes": sorted(codes), "pass": passed})
        if not passed:
            failures.append(name)

    print(json.dumps({"status": "PASS" if not failures else "FAIL", "controls": results}, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
