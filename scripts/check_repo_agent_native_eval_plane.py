#!/usr/bin/env python3
"""Positive/hollow calibration for the repo-agent-native canonical eval plane."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "repo-agent-native"


def run(argv: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=40)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def record(identifier: str, predicate: str, value: object, path: str, *, negative: bool = False) -> dict:
    item = {
        "id": identifier, "class": "fixture-contract", "claim": identifier,
        "predicate": {"id": predicate, "operator": "equals", "value": value},
        "evidence_level": "A", "source_refs": [{"path": path, "start_line": 1, "end_line": 8}],
        "verification": ["source-read"],
    }
    if negative:
        item.update({"search_boundary": [path], "counterexample_sought": "opposite implementation"})
    return item


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="repo-agent-native-eval-selftest-") as temp_value:
        temp = Path(temp_value)
        repo = temp / "repo"
        shutil.copytree(SKILL / "evals" / "fixtures" / "retry-service", repo)
        for argv in (["git", "init", "-q"], ["git", "add", "src"], ["git", "-c", "user.name=Eval", "-c", "user.email=eval@example.invalid", "commit", "-qm", "fixture"]):
            result = run(argv, cwd=repo)
            if result.returncode:
                print(result.stderr, file=sys.stderr); return 1
        head = run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
        bundle = temp / "subject.bundle"
        if run(["git", "bundle", "create", str(bundle), "HEAD"], cwd=repo).returncode:
            return 1
        report = {
            "schema": "repo-agent-native/invariant-report/v2",
            "subject": {"repository": "eval/retry-service", "observed_commit": head, "observed_tree": None, "scope": ["src"], "task": "AB-RETRY-01"},
            "routes": [], "tools": ["direct source read"],
            "facts": [
                record("INV-1", "retry.result_contract", "discriminated-success-failure-attempts", "src/retry-policy.ts"),
                record("INV-2", "retry.max_attempts", 3, "src/retry-policy.ts"),
                record("INV-3", "retry.delay_ms", 25, "src/retry-policy.ts"),
            ],
            "negative_invariants": [
                record("NEG-1", "metrics.failure_mode", "swallowed", "src/api-client.ts", negative=True),
                record("NEG-2", "retry.delay_strategy", "fixed", "src/retry-policy.ts", negative=True),
            ],
            "implicit_dependencies": [record("DEP-1", "metrics.observability_sink", "none", "src/metrics.ts")],
            "open_questions": [], "named_exclusions": [], "state": "PASS",
        }
        report_path = temp / "report.json"; write(report_path, report)
        paths = {
            "schema_sha256": SKILL / "evals" / "fixtures" / "invariant-report.schema.json",
            "ground_truth_sha256": SKILL / "evals" / "fixtures" / "retry-service" / "expected.json",
            "eval_config_sha256": SKILL / "evals" / "evals.json",
            "scorer_sha256": SKILL / "scripts" / "score-ab-output.ts",
            "predicate_evaluator_sha256": SKILL / "scripts" / "evaluate-retry-predicates.ts",
        }
        receipt = {
            "schema": "repo-agent-native/ab-run-receipt/v1", "run_id": "selftest-candidate-r1",
            "carrier": {"id": "codex", "version": "selftest"}, "model": {"provider": "openai", "name": "selftest"},
            "condition": "candidate_skill", "scenario": "AB-RETRY-01", "repetition": 1,
            "fixture_commit": head, "subject_bundle": {"path": "subject.bundle", "sha256": sha(bundle)},
            "skill": {"name": "repo-agent-native", "instruction_digest": "a" * 64},
            "evaluator": {key: sha(path) for key, path in paths.items()},
            "execution": {"exit": 0, "timed_out": False, "duration_ms": 100, "parse_error": None},
            "operational": {"tool_calls": 3, "input_tokens": 100, "output_tokens": 50},
            "limits": {"retries": 0}, "state": "PASS",
        }
        receipt_path = temp / "receipt.json"; write(receipt_path, receipt)
        verifier = temp / "verifier.json"
        verify_argv = [sys.executable, str(ROOT / "evals/verifiers/verify_repo_agent_native_output.py"), "--receipt", str(receipt_path), "--report", str(report_path), "--subject-bundle", str(bundle), "--output", str(verifier)]
        if run(verify_argv).returncode != 0:
            print("FAIL positive verifier calibration", file=sys.stderr); return 1
        trace = temp / "trace.json"
        normalize_argv = [sys.executable, str(ROOT / "evals/adapters/normalize_repo_agent_native.py"), "--receipt", str(receipt_path), "--verifier-receipt", str(verifier), "--output", str(trace)]
        if run(normalize_argv).returncode != 0 or json.loads(trace.read_text())["outcome"]["passed"] is not True:
            print("FAIL positive normalization", file=sys.stderr); return 1
        receipt["subject_bundle"]["sha256"] = "0" * 64; write(receipt_path, receipt)
        if run(verify_argv).returncode != 2:
            print("FAIL bundle-digest mutation survived", file=sys.stderr); return 1
        receipt["subject_bundle"]["sha256"] = sha(bundle); receipt["operational"]["input_tokens"] = None; write(receipt_path, receipt)
        if run(normalize_argv).returncode == 0:
            print("FAIL absent-telemetry mutation survived", file=sys.stderr); return 1
        rows = []
        quality = {"candidate_skill": 0.9, "current_skill": 0.7, "no_skill": 0.5, "wrong_skill": 0.6}
        for carrier in ("codex", "claude"):
            for condition, value in quality.items():
                for repetition in (1, 2, 3):
                    row = json.loads(json.dumps(receipt))
                    row.update({"carrier": {"id": carrier, "version": "selftest"}, "condition": condition, "repetition": repetition, "state": "PASS"})
                    row["score"] = {"hard_gate": "PASS", "admission_quality": value}
                    rows.append(row)
        matrix = temp / "matrix.jsonl"
        matrix.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        matrix_argv = [sys.executable, str(ROOT / "evals/adapters/summarize_repo_agent_native_matrix.py"), str(matrix)]
        if run(matrix_argv).returncode != 0:
            print("FAIL complete matrix calibration", file=sys.stderr); return 1
        matrix.write_text("".join(json.dumps(row) + "\n" for row in rows[:-1]), encoding="utf-8")
        if run(matrix_argv).returncode == 0:
            print("FAIL incomplete-matrix mutation survived", file=sys.stderr); return 1
    print("PASS repo-agent-native canonical eval plane: positive=3 mutations=3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
