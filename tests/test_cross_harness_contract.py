from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NORMALIZER = ROOT / "evals" / "adapters" / "normalize_run.py"
BUNDLER = ROOT / "evals" / "adapters" / "build_evidence_bundle.py"


class CrossHarnessContractTests(unittest.TestCase):
    def test_generic_and_skill_up_normalize_to_same_identity_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            generic = tmp / "generic.json"
            skill_up = tmp / "skillup.json"
            generic.write_text(json.dumps({
                "passed": True,
                "verifier": "script",
                "selected_skill": "autoresearch-composer",
                "did_invoke": True,
                "wall_seconds": 2.5,
                "tool_calls": 3,
                "input_tokens": 100,
                "output_tokens": 20,
                "retries": 0,
            }), encoding="utf-8")
            skill_up.write_text(json.dumps({
                "result": {
                    "status": "passed",
                    "judge_type": "script",
                    "selected_skill": "autoresearch-composer",
                    "metrics": {"total_tool_calls": 4, "input_tokens": 110, "output_tokens": 25},
                    "timing": {"total_duration_seconds": 3.0},
                }
            }), encoding="utf-8")

            outputs = []
            for adapter, source, harness in (("generic", generic, "arena"), ("skill-up", skill_up, "skill-up")):
                out = tmp / f"{adapter}.run.json"
                cmd = [
                    "python3", str(NORMALIZER), "--adapter", adapter, "--input", str(source),
                    "--case-id", "autoresearch-metric-loop-plan", "--condition", "candidate_skill",
                    "--skill-sha", "abcdef0123456789", "--eval-suite-sha", "1234567abcdef",
                    "--model-provider", "test", "--model-name", "model-a",
                    "--harness-name", harness, "--harness-version", "1",
                    "--runtime", "docker", "--network-policy", "no-network",
                    "--fresh-workspace", "--seed", "7", "--should-invoke", "--output", str(out),
                ]
                proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                value = json.loads(out.read_text(encoding="utf-8"))
                self.assertEqual(value["schema_version"], "skill-eval-run/v1")
                self.assertEqual(value["case_id"], "autoresearch-metric-loop-plan")
                self.assertEqual(value["condition"], "candidate_skill")
                self.assertEqual(value["skill_sha"], "abcdef0123456789")
                self.assertTrue(value["outcome"]["passed"])
                self.assertTrue(value["routing"]["did_invoke"])
                outputs.append(value)
            self.assertNotEqual(outputs[0]["run_id"], outputs[1]["run_id"], "harness is part of run identity")

    def test_no_skill_run_must_not_require_skill_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            source = tmp / "raw.json"
            out = tmp / "run.json"
            source.write_text('{"passed": false}', encoding="utf-8")
            proc = subprocess.run([
                "python3", str(NORMALIZER), "--adapter", "generic", "--input", str(source),
                "--case-id", "case-001", "--condition", "no_skill", "--eval-suite-sha", "1234567",
                "--model-provider", "test", "--model-name", "m", "--harness-name", "arena",
                "--harness-version", "1", "--runtime", "none", "--network-policy", "no-network",
                "--output", str(out),
            ], text=True, capture_output=True, check=False)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIsNone(json.loads(out.read_text())["skill_sha"])

    def test_evidence_bundle_hashes_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            run = tmp / "run.json"
            receipt = tmp / "receipt.txt"
            artifact = tmp / "artifact.txt"
            bundle = tmp / "bundle.json"
            run.write_text(json.dumps({"run_id": "run-12345678", "case_id": "case-001", "skill_sha": "abcdef0"}), encoding="utf-8")
            receipt.write_text("PASS\n", encoding="utf-8")
            artifact.write_text("immutable result\n", encoding="utf-8")
            proc = subprocess.run([
                "python3", str(BUNDLER), "--run-trace", str(run), "--verifier-receipt", str(receipt),
                "--eval-suite-sha", "1234567", "--artifact", str(artifact),
                "--replay-command", "python3 verify.py", "--output", str(bundle),
            ], text=True, capture_output=True, check=False)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            value = json.loads(bundle.read_text())
            expected = hashlib.sha256(artifact.read_bytes()).hexdigest()
            self.assertEqual(value["artifact_hashes"][str(artifact)], expected)
            self.assertTrue(value["replay"]["offline_capable"])


if __name__ == "__main__":
    unittest.main()
