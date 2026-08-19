#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_trace_graph.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID_GRAPH = FIXTURES / "valid-trace-graph.json"
VALID_AUTHORITY = FIXTURES / "authority-snapshot.json"

EXPECTED = {
    "NC-01": "DUPLICATE_ICPG_AUTHORITY",
    "NC-02": "STALE_MUTABLE_SUBJECT",
    "NC-03": "PROSE_OVER_RECEIPT",
    "NC-17": "FABRICATED_ARTIFACT_IDENTITY",
}


def run(graph: dict, authority: dict) -> tuple[int, dict]:
    with tempfile.TemporaryDirectory() as temp_dir:
        directory = Path(temp_dir)
        graph_path = directory / "graph.json"
        authority_path = directory / "authority.json"
        graph_path.write_text(json.dumps(graph), encoding="utf-8")
        authority_path.write_text(json.dumps(authority), encoding="utf-8")
        process = subprocess.run(
            [
                sys.executable,
                str(CHECKER),
                str(graph_path),
                "--authority-snapshot",
                str(authority_path),
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
    valid = json.loads(VALID_GRAPH.read_text(encoding="utf-8"))
    authority = json.loads(VALID_AUTHORITY.read_text(encoding="utf-8"))

    cases: dict[str, tuple[dict, dict]] = {}

    graph = copy.deepcopy(valid)
    graph["intents"][0]["case_denominator"] = [{"case_id": "CASE-001", "truth": "copied"}]
    cases["NC-01"] = (graph, copy.deepcopy(authority))

    graph = copy.deepcopy(valid)
    pr = next(artifact for artifact in graph["artifacts"] if artifact["artifact_type"] == "PR")
    pr["observed_subject"]["sha"] = "2" * 40
    cases["NC-02"] = (graph, copy.deepcopy(authority))

    graph = copy.deepcopy(valid)
    readme = next(artifact for artifact in graph["artifacts"] if artifact["artifact_type"] == "README")
    readme["evidence_ceiling"] = "L3"
    cases["NC-03"] = (graph, copy.deepcopy(authority))

    graph = copy.deepcopy(valid)
    pr = next(artifact for artifact in graph["artifacts"] if artifact["artifact_type"] == "PR")
    pr["external_identity"] = "pr:other/repo#999"
    cases["NC-17"] = (graph, copy.deepcopy(authority))

    failures: list[str] = []
    results: list[dict] = []
    for control, (graph, authority_snapshot) in cases.items():
        return_code, report = run(graph, authority_snapshot)
        codes = {error["code"] for error in report.get("errors", [])}
        expected = EXPECTED[control]
        passed = return_code == 2 and report.get("status") == "BLOCK" and expected in codes
        results.append({
            "control": control,
            "expected": expected,
            "codes": sorted(codes),
            "pass": passed,
        })
        if not passed:
            failures.append(control)

    print(json.dumps({
        "status": "PASS" if not failures else "FAIL",
        "controls": results,
    }, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
