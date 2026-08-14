#!/usr/bin/env python3
"""Re-run the repo-agent-native deterministic scorer from a Git bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "repo-agent-native"
SCORER = SKILL / "scripts" / "score-ab-output.ts"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must be an object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--subject-bundle", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    receipt_path, report_path, bundle = map(Path, (args.receipt, args.report, args.subject_bundle))
    failures: list[str] = []
    try:
        receipt = load(receipt_path)
        if receipt.get("schema") != "repo-agent-native/ab-run-receipt/v1":
            raise ValueError("unsupported physical receipt")
        if digest(bundle) != receipt.get("subject_bundle", {}).get("sha256"):
            failures.append("subject bundle digest mismatch")
        expected = SKILL / "evals" / "fixtures" / "retry-service" / "expected.json"
        config = SKILL / "evals" / "evals.json"
        evaluator = receipt.get("evaluator", {})
        schema = SKILL / "evals" / "fixtures" / "invariant-report.schema.json"
        predicate_evaluator = SKILL / "scripts" / "evaluate-retry-predicates.ts"
        for key, path in (
            ("schema_sha256", schema),
            ("ground_truth_sha256", expected),
            ("eval_config_sha256", config),
            ("scorer_sha256", SCORER),
            ("predicate_evaluator_sha256", predicate_evaluator),
        ):
            if evaluator.get(key) != digest(path):
                failures.append(f"{key} mismatch")
        with tempfile.TemporaryDirectory(prefix="repo-agent-native-verify-") as temp:
            repo, score = Path(temp) / "repo", Path(temp) / "score.json"
            clone = subprocess.run(["git", "clone", "-q", str(bundle.resolve()), str(repo)], capture_output=True, text=True, timeout=30)
            if clone.returncode != 0:
                failures.append(f"bundle clone failed: {clone.stderr.strip()}")
            else:
                head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
                if head.returncode != 0 or head.stdout.strip() != receipt.get("fixture_commit"):
                    failures.append("exact subject commit mismatch")
                scored = subprocess.run([
                    "bun", str(SCORER), "--repo", str(repo), "--report", str(report_path.resolve()),
                    "--expected", str(expected), "--evals", str(config), "--output", str(score),
                ], capture_output=True, text=True, timeout=30)
                if scored.returncode not in (0, 2) or not score.is_file():
                    failures.append(f"scorer mechanism failed: {scored.stderr.strip()}")
                elif load(score).get("hard_gate") != "PASS":
                    failures.append("deterministic hard gate failed")
        execution = receipt.get("execution", {})
        if execution.get("exit") != 0 or execution.get("timed_out") is not False or execution.get("parse_error") is not None:
            failures.append("carrier execution was not clean")
        input_digest = hashlib.sha256(receipt_path.read_bytes() + report_path.read_bytes() + bundle.read_bytes()).hexdigest()
        result = {
            "schema_version": "skill-eval-verifier-receipt/v1",
            "run_id": receipt["run_id"],
            "case_id": receipt["scenario"],
            "authority": "deterministic",
            "verifier": {"kind": "repo-agent-native-source-replay/v1", "implementation_sha256": digest(Path(__file__))},
            "passed": not failures,
            "input_digest": input_digest,
            "replay_command": None,
            "notes": None if not failures else "; ".join(failures),
        }
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 0 if not failures else 2
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 70


if __name__ == "__main__":
    raise SystemExit(main())
