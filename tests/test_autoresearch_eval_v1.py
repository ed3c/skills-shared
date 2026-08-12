from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.summarize_skill_eval_matrix import summarize

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "evals" / "verifiers" / "verify_autoresearch_contract.py"


class AutoresearchVerifierTests(unittest.TestCase):
    def run_case(self, case_id: str, evidence: dict, artifact: dict | None = None) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "evidence").mkdir()
            if artifact is not None:
                (root / "artifacts").mkdir()
                artifact_path = root / "artifacts" / "iteration-contract.json"
                artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
                evidence = dict(evidence)
                evidence["plan_artifact"] = str(artifact_path)
            (root / "evidence" / "run.json").write_text(json.dumps(evidence), encoding="utf-8")
            return subprocess.run(
                ["python3", str(VERIFIER), "--case", case_id],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

    def test_metric_loop_requires_complete_contract(self):
        evidence = {
            "case_id": "autoresearch-metric-loop-plan",
            "decision": "invoke",
            "selected_skill": "autoresearch-composer",
        }
        artifact = {
            "Goal": "raise lint pass rate",
            "Scope": "src",
            "Metric": "lint_pass_rate",
            "Direction": "higher_is_better",
            "Verify": "./lint-score.sh",
            "Guard": "pytest -q",
            "Iterations": 5,
        }
        self.assertEqual(self.run_case("autoresearch-metric-loop-plan", evidence, artifact).returncode, 0)
        del artifact["Guard"]
        failed = self.run_case("autoresearch-metric-loop-plan", evidence, artifact)
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn("Guard", failed.stderr)

    def test_debug_case_must_yield(self):
        good = {
            "case_id": "autoresearch-yield-bug-diagnosis",
            "decision": "delegate",
            "selected_skill": "diagnose",
        }
        self.assertEqual(self.run_case("autoresearch-yield-bug-diagnosis", good).returncode, 0)
        bad = dict(good, selected_skill="autoresearch-composer")
        self.assertNotEqual(self.run_case("autoresearch-yield-bug-diagnosis", bad).returncode, 0)

    def test_recovery_requires_semantic_evidence(self):
        good = {
            "case_id": "autoresearch-recover-compressed-context",
            "decision": "recover",
            "selected_skill": "autoresearch-composer",
            "recovery": {
                "low_compression_context": "original task semantics",
                "domain_terms": ["lint pass rate"],
                "known_unknowns": ["metric command location"],
            },
        }
        self.assertEqual(self.run_case("autoresearch-recover-compressed-context", good).returncode, 0)

    def test_holdout_near_miss_requires_explicit_block_reason(self):
        good = {
            "case_id": "autoresearch-holdout-no-verifier",
            "decision": "delegate",
            "selected_skill": "grilling",
            "reason": "no_numeric_verifier",
        }
        self.assertEqual(self.run_case("autoresearch-holdout-no-verifier", good).returncode, 0)
        bad = dict(good, reason="generic")
        self.assertNotEqual(self.run_case("autoresearch-holdout-no-verifier", bad).returncode, 0)


class MatrixSummaryTests(unittest.TestCase):
    def test_reports_f1_lift_and_candidate_delta(self):
        rows = [
            {"case_id": "p", "condition": "no_skill", "should_invoke": True, "did_invoke": False, "passed": False},
            {"case_id": "n", "condition": "no_skill", "should_invoke": False, "did_invoke": True, "passed": False},
            {"case_id": "p", "condition": "current_skill", "should_invoke": True, "did_invoke": True, "passed": True},
            {"case_id": "n", "condition": "current_skill", "should_invoke": False, "did_invoke": True, "passed": False},
            {"case_id": "p", "condition": "candidate_skill", "should_invoke": True, "did_invoke": True, "passed": True},
            {"case_id": "n", "condition": "candidate_skill", "should_invoke": False, "did_invoke": False, "passed": True},
        ]
        result = summarize(rows)
        self.assertEqual(result["by_condition"]["candidate_skill"]["routing"]["f1"], 1.0)
        self.assertEqual(result["candidate_vs_no_skill_lift"], 1.0)
        self.assertEqual(result["candidate_vs_current_delta"], 0.5)


if __name__ == "__main__":
    unittest.main()
