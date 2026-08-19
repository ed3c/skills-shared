#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_graph_traversal.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

BASE_PLAN = json.loads((FIXTURES / "traversal-plan.json").read_text(encoding="utf-8"))
BASE_TRACE = json.loads((FIXTURES / "traversal-trace-graph.json").read_text(encoding="utf-8"))
BASE_AUTHORITY = json.loads((FIXTURES / "traversal-authority-snapshot.json").read_text(encoding="utf-8"))
BASE_BINDING = json.loads((FIXTURES / "valid-traversal-binding.json").read_text(encoding="utf-8"))
BASE_TASK = json.loads((FIXTURES / "traversal-task-contract.json").read_text(encoding="utf-8"))

EXPECTED = {
    "NC-08": "CONNECTIVITY_INFLATION",
    "NC-09": "EVIDENCE_LAUNDERING",
    "NC-10": "AUTHORITY_INVERSION",
    "NC-12": "STALE_DECISION_SUBJECT",
    "FALSE-DEPENDS-ON": "FALSE_DEPENDS_ON_ANCESTRY",
}


def run(plan: dict, trace: dict, authority: dict, binding: dict, task: dict) -> tuple[int, dict]:
    with tempfile.TemporaryDirectory() as temp_dir:
        directory = Path(temp_dir)
        files = {
            "plan.json": plan,
            "trace.json": trace,
            "authority.json": authority,
            "binding.json": binding,
            "task.json": task,
        }
        for name, value in files.items():
            (directory / name).write_text(json.dumps(value), encoding="utf-8")
        process = subprocess.run(
            [
                sys.executable,
                str(CHECKER),
                str(directory / "plan.json"),
                "--case-graph",
                str(FIXTURES / "traversal-case-graph.json"),
                "--task-contract",
                str(directory / "task.json"),
                "--delivery-binding",
                str(directory / "binding.json"),
                "--trace-graph",
                str(directory / "trace.json"),
                "--authority-snapshot",
                str(directory / "authority.json"),
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
    cases: dict[str, tuple[dict, dict, dict, dict, dict]] = {}

    trace = copy.deepcopy(BASE_TRACE)
    touches = next(edge for edge in trace["edges"] if edge["relation"] == "TOUCHES")
    touches["utility"] = "EVIDENCE"
    cases["NC-08"] = (copy.deepcopy(BASE_PLAN), trace, copy.deepcopy(BASE_AUTHORITY), copy.deepcopy(BASE_BINDING), copy.deepcopy(BASE_TASK))

    plan = copy.deepcopy(BASE_PLAN)
    why = next(query for query in plan["queries"] if query["query_id"] == "q-why-proof")
    why["claimed_evidence_ceiling"] = "L4"
    cases["NC-09"] = (plan, copy.deepcopy(BASE_TRACE), copy.deepcopy(BASE_AUTHORITY), copy.deepcopy(BASE_BINDING), copy.deepcopy(BASE_TASK))

    plan = copy.deepcopy(BASE_PLAN)
    why = next(query for query in plan["queries"] if query["query_id"] == "q-why-proof")
    why["expected_terminal"] = "artifact|readme-core"
    why["claimed_evidence_ceiling"] = "L1"
    cases["NC-10"] = (plan, copy.deepcopy(BASE_TRACE), copy.deepcopy(BASE_AUTHORITY), copy.deepcopy(BASE_BINDING), copy.deepcopy(BASE_TASK))

    authority = copy.deepcopy(BASE_AUTHORITY)
    authority["artifacts"]["pr-core"]["observed_at"] = "2026-08-19T11:59:59Z"
    cases["NC-12"] = (copy.deepcopy(BASE_PLAN), copy.deepcopy(BASE_TRACE), authority, copy.deepcopy(BASE_BINDING), copy.deepcopy(BASE_TASK))

    trace = copy.deepcopy(BASE_TRACE)
    trace["edges"].append({"from": "pr-contract", "relation": "DEPENDS_ON", "to": "pr-core", "utility": "IMPLEMENTATION"})
    cases["FALSE-DEPENDS-ON"] = (copy.deepcopy(BASE_PLAN), trace, copy.deepcopy(BASE_AUTHORITY), copy.deepcopy(BASE_BINDING), copy.deepcopy(BASE_TASK))

    failures: list[str] = []
    results: list[dict] = []
    for control, (plan, trace, authority, binding, task) in cases.items():
        rc, report = run(plan, trace, authority, binding, task)
        codes = {item["code"] for item in report.get("errors", [])}
        expected = EXPECTED[control]
        passed = rc == 2 and report.get("status") == "BLOCK" and expected in codes
        results.append({"control": control, "expected": expected, "codes": sorted(codes), "pass": passed})
        if not passed:
            failures.append(control)

    print(json.dumps({"status": "PASS" if not failures else "FAIL", "controls": results}, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
