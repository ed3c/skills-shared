from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.check_mutation_promotions import check

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "check_mutation_promotions.py"


class MutationPromotionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "mutations" / "demo").mkdir(parents=True)
        (self.root / "mutations" / "receipts").mkdir(parents=True)
        self.parent = "abcdef0123456789"
        self.candidate = "1234567abcdef890"
        self.receipt_ref = self.write_decision_receipt()
        self.record = {
            "schema_version": "skill-mutation/v1",
            "skill": "demo-skill",
            "parent_sha": self.parent,
            "candidate_sha": self.candidate,
            "hypothesis": "Candidate improves the target task without regressing controls.",
            "mutation_class": "verification",
            "target_failures": ["target-failure"],
            "changed_sections": ["verification contract"],
            "expected_effect": {
                "metric": "task_pass_rate",
                "minimum_delta": 0.5,
                "case_ids": ["target-case"],
            },
            "regression_budget": 0.0,
            "status": "won",
            "evaluation_receipt": self.receipt_ref,
            "rollback_sha": self.parent,
        }
        self.lineage = self.root / "mutations" / "demo" / "lineage.jsonl"
        self.write_lineage(self.record)
        self.write_registry(self.promotion())

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_bundle(self, case_id: str, skill_sha: str | None, passed: bool, name: str) -> str:
        run_id = f"run-{name}-12345678"
        run_dir = self.root / "evidence" / "runs"
        receipt_dir = self.root / "evidence" / "receipts"
        bundle_dir = self.root / "evidence" / "bundles"
        run_dir.mkdir(parents=True, exist_ok=True)
        receipt_dir.mkdir(parents=True, exist_ok=True)
        bundle_dir.mkdir(parents=True, exist_ok=True)
        run = run_dir / f"{name}.json"
        receipt = receipt_dir / f"{name}.json"
        bundle = bundle_dir / f"{name}.json"
        run.write_text(json.dumps({
            "schema_version": "skill-eval-run/v1",
            "run_id": run_id,
            "case_id": case_id,
            "skill_sha": skill_sha,
            "outcome": {"passed": passed},
        }), encoding="utf-8")
        receipt.write_text(json.dumps({
            "schema_version": "skill-eval-verifier-receipt/v1",
            "authority": "deterministic",
            "passed": passed,
            "run_id": run_id,
            "case_id": case_id,
        }), encoding="utf-8")
        bundle.write_text(json.dumps({
            "schema_version": "skill-eval-evidence/v1",
            "run_id": run_id,
            "case_id": case_id,
            "skill_sha": skill_sha,
            "run_trace": run.relative_to(self.root).as_posix(),
            "verifier_receipt": receipt.relative_to(self.root).as_posix(),
            "verifier_receipt_sha256": hashlib.sha256(receipt.read_bytes()).hexdigest(),
            "promotion_eligible": passed,
        }), encoding="utf-8")
        return bundle.relative_to(self.root).as_posix()

    def write_decision_receipt(self) -> str:
        refs = [
            self.write_bundle("target-case", self.parent, False, "target-parent"),
            self.write_bundle("target-case", self.candidate, True, "target-candidate"),
            self.write_bundle("target-case", None, False, "target-no-skill"),
            self.write_bundle("control-case", self.parent, True, "control-parent"),
            self.write_bundle("control-case", self.candidate, True, "control-candidate"),
            self.write_bundle("control-case", None, False, "control-no-skill"),
        ]
        path = self.root / "mutations" / "receipts" / "decision.json"
        path.write_text(json.dumps({
            "schema_version": "skill-mutation-eval/v1",
            "skill": "demo-skill",
            "parent_sha": self.parent,
            "candidate_sha": self.candidate,
            "metric": "task_pass_rate",
            "target_case_ids": ["target-case"],
            "non_target_case_ids": ["control-case"],
            "evidence_bundles": refs,
        }), encoding="utf-8")
        return path.relative_to(self.root).as_posix()

    def write_lineage(self, record: dict) -> None:
        self.lineage.write_text(json.dumps(record) + "\n", encoding="utf-8")

    def promotion(self) -> dict:
        return {
            "skill": "demo-skill",
            "candidate_sha": self.candidate,
            "lineage_ref": self.lineage.relative_to(self.root).as_posix(),
            "line_number": 1,
            "evaluation_receipt": self.receipt_ref,
        }

    def write_registry(self, *entries: dict) -> None:
        (self.root / "mutations" / "promotions.json").write_text(json.dumps({
            "schema_version": "skill-mutation-promotion-registry/v1",
            "promotions": list(entries),
        }), encoding="utf-8")

    def assert_fails(self, needle: str) -> None:
        _, errors = check(self.root)
        self.assertTrue(errors)
        self.assertIn(needle, "\n".join(errors))

    def test_recomputed_winner_is_admitted(self) -> None:
        count, errors = check(self.root)
        self.assertEqual(count, 1)
        self.assertEqual(errors, [])

    def test_direct_cli_entrypoint_imports_cleanly(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS mutation promotion registry", result.stdout)

    def test_lost_candidate_cannot_be_promoted(self) -> None:
        self.record["status"] = "lost"
        self.write_lineage(self.record)
        self.assert_fails("not won")

    def test_candidate_identity_must_match_lineage(self) -> None:
        entry = self.promotion()
        entry["candidate_sha"] = "9999999abcdef000"
        self.write_registry(entry)
        self.assert_fails("candidate_sha does not match")

    def test_receipt_identity_must_match_lineage(self) -> None:
        entry = self.promotion()
        entry["evaluation_receipt"] = "mutations/receipts/other.json"
        self.write_registry(entry)
        self.assert_fails("evaluation_receipt does not match")

    def test_won_string_cannot_override_failing_evidence(self) -> None:
        receipt = json.loads((self.root / self.receipt_ref).read_text())
        candidate_bundle = self.root / receipt["evidence_bundles"][1]
        candidate = json.loads(candidate_bundle.read_text())
        verifier = self.root / candidate["verifier_receipt"]
        verifier_value = json.loads(verifier.read_text())
        verifier_value["passed"] = False
        verifier.write_text(json.dumps(verifier_value))
        candidate["verifier_receipt_sha256"] = hashlib.sha256(verifier.read_bytes()).hexdigest()
        candidate["promotion_eligible"] = False
        candidate_bundle.write_text(json.dumps(candidate))
        run = self.root / candidate["run_trace"]
        run_value = json.loads(run.read_text())
        run_value["outcome"]["passed"] = False
        run.write_text(json.dumps(run_value))
        self.assert_fails("fails admission")

    def test_duplicate_promotion_is_rejected(self) -> None:
        entry = self.promotion()
        self.write_registry(entry, dict(entry))
        self.assert_fails("duplicates promoted candidate")


if __name__ == "__main__":
    unittest.main()
