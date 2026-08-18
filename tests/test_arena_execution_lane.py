"""The Arena lane must refuse the shapes that produce a confidently empty run.

The failure this guards against is specific: Arena destroys its disposable
worktree, so the produced artifacts exist only as blobs in the receipt store. A
collector that shrugged at a missing blob would emit executor evidence whose
rebuilt workspace is empty, the deterministic verifier would then fail for the
wrong reason, and the run would be counted as a measured skill failure rather
than as lost evidence.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "arena_execution_lane.py"
SHA = "a" * 40
CASE = "autoresearch-metric-loop-plan"


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


class ArenaExecutionLaneTests(unittest.TestCase):
    def run_script(self, *argv: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(SCRIPT), *argv], text=True, capture_output=True)

    def test_selftest_is_green(self):
        proc = self.run_script("--selftest")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def export(self, root: Path) -> tuple[dict, dict]:
        request, assertions = root / "request.json", root / "assertions.json"
        proc = self.run_script(
            "export", "--case", CASE, "--skill", "autoresearch-composer",
            "--condition", "candidate_skill", "--repository", "ed3c/skills-shared",
            "--commit", SHA, "--tree", "b" * 40, "--skill-sha", SHA,
            "--skill-root", str(ROOT / "skills" / "autoresearch-composer"),
            "--model-name", "model-a", "--repetition", "1",
            "--request-out", str(request), "--assertions-out", str(assertions),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(request.read_text()), json.loads(assertions.read_text())

    def test_export_binds_subject_skill_and_assertion_digest(self):
        with tempfile.TemporaryDirectory() as raw:
            request, assertions = self.export(Path(raw))
        self.assertEqual(request["schema_version"], "skill-execution-request/v1")
        self.assertFalse(request["promotion_authority"])
        self.assertEqual(request["subject"]["commit"], SHA)
        self.assertTrue(request["skill"]["content_digest"].startswith("sha256:"))
        self.assertEqual(request["assertion_set"]["id"], assertions["id"])
        # No credential-shaped name may reach the runner's environment allowlist.
        self.assertNotIn("ANTHROPIC_API_KEY", request["command"]["env_allowlist"])
        # Every expected artifact needs both the hard existence assertion the
        # runner demands and the content assertion that preserves its bytes.
        for relative in request["expected_artifacts"]:
            kinds = {a["type"] for a in assertions["assertions"] if a["expected"].get("path") == relative}
            self.assertEqual(kinds, {"file_exists", "file_content"}, relative)

    def collect(self, root: Path, receipt: dict, request: dict) -> subprocess.CompletedProcess[str]:
        receipt_dir = root / "receipt"
        (receipt_dir / "artifacts").mkdir(parents=True)
        (receipt_dir / "receipt.json").write_text(json.dumps(receipt))
        (receipt_dir / "request.json").write_text(json.dumps(request))
        for blob in self.blobs:
            (receipt_dir / "artifacts" / digest(blob).split(":", 1)[1]).write_bytes(blob)
        return self.run_script(
            "collect", "--receipt-dir", str(receipt_dir), "--case-id", CASE,
            "--condition", "candidate_skill", "--skill", "autoresearch-composer",
            "--skill-sha", SHA, "--eval-suite-sha", SHA, "--model-provider", "anthropic",
            "--model-name", "model-a", "--engine", "claude_code", "--harness-version", "c" * 40,
            "--repetition", "1", "--workspace-out", str(root / "ws"), "--output", str(root / "ev.json"),
        )

    def setUp(self):
        self.evidence_bytes = json.dumps({"case_id": CASE, "decision": "invoke"}).encode()
        self.contract_bytes = json.dumps({"Goal": "g"}).encode()
        self.blobs = [self.evidence_bytes, self.contract_bytes]

    def passing_receipt(self) -> tuple[dict, dict]:
        request = {
            "request_id": "r1",
            "subject": {"repository": "ed3c/skills-shared", "commit": SHA},
            "expected_artifacts": ["evidence/run.json", "artifacts/iteration-contract.json"],
        }
        receipt = {
            "schema_version": "skill-execution-receipt/v1",
            "request_id": "r1",
            "subject": request["subject"],
            "status": "PASS",
            "timing": {"duration_ms": 4200},
            "artifacts": {},
            "assertions": [
                {"id": "artifact-content-0", "status": "PASS", "evidence": [digest(self.evidence_bytes)]},
                {"id": "artifact-content-1", "status": "PASS", "evidence": [digest(self.contract_bytes)]},
            ],
        }
        return receipt, request

    def test_collect_rebuilds_the_workspace_and_never_claims_promotion(self):
        receipt, request = self.passing_receipt()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            proc = self.collect(root, receipt, request)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            value = json.loads((root / "ev.json").read_text())
            self.assertEqual((root / "ws" / "evidence" / "run.json").read_bytes(), self.evidence_bytes)
        self.assertEqual(value["schema_version"], "skill-eval-executor-evidence/v1")
        self.assertFalse(value["promotion"]["eligible"])
        self.assertFalse(value["sampling"]["seed_controlled"])
        self.assertIsNone(value["sampling"]["model_seed"])
        # Arena observes no token accounting, and a fabricated zero would read as
        # a measurement rather than an absence.
        self.assertEqual(value["outcome"]["token_accounting"], "ABSENT")

    def test_collect_refuses_a_receipt_whose_subject_drifted(self):
        receipt, request = self.passing_receipt()
        receipt["subject"] = {"repository": "ed3c/skills-shared", "commit": "d" * 40}
        with tempfile.TemporaryDirectory() as raw:
            proc = self.collect(Path(raw), receipt, request)
        self.assertNotEqual(proc.returncode, 0)

    def test_collect_refuses_lost_artifact_bytes_instead_of_emptying_the_workspace(self):
        receipt, request = self.passing_receipt()
        receipt["assertions"][1]["status"] = "FAIL"
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            proc = self.collect(root, receipt, request)
            self.assertNotEqual(proc.returncode, 0)
            self.assertFalse((root / "ev.json").exists())


if __name__ == "__main__":
    unittest.main()
