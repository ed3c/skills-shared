from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.check_release_receipts import validate_release


class ReleaseReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.skill_sha = "a" * 40
        self.eval_sha = "b" * 40
        self.refs = [
            self.land_bundle("case-a", "model-a", "codex", "sandbox-a", "a"),
            self.land_bundle("case-b", "model-b", "claude-code", "sandbox-b", "b"),
        ]
        self.unlock = {
            "id": "unlock-demo",
            "skill": "demo-skill",
            "skill_sha": self.skill_sha,
            "evidence_bundles": list(self.refs),
        }
        rollback = self.root / "rollback" / "SKILL.md"
        rollback.parent.mkdir(parents=True)
        rollback.write_text("previous canonical skill\n", encoding="utf-8")
        scorecard = self.root / "scorecards" / "demo.json"
        scorecard.parent.mkdir(parents=True)
        scorecard.write_text(json.dumps(self.scorecard()), encoding="utf-8")
        self.release = {
            "schema_version": "skill-release-receipt/v1",
            "id": "release-demo-v1",
            "skill": "demo-skill",
            "skill_sha": self.skill_sha,
            "eval_suite_sha": self.eval_sha,
            "capability_unlock_id": "unlock-demo",
            "model_harness_matrix": [
                {"model": "model-a", "harness": "codex", "environment": "sandbox-a"},
                {"model": "model-b", "harness": "claude-code", "environment": "sandbox-b"},
            ],
            "evidence_bundles": list(self.refs),
            "rollback_sha": "c" * 40,
            "rollback_artifact": rollback.relative_to(self.root).as_posix(),
            "rollback_sha256": hashlib.sha256(rollback.read_bytes()).hexdigest(),
            "scorecard": scorecard.relative_to(self.root).as_posix(),
            "human_admit": {"actor": "owner", "admitted_at": "2026-08-12T08:00:00Z"},
        }

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def scorecard(self) -> dict:
        return {
            "schema_version": "skill-scorecard/v1",
            "skill": "demo-skill",
            "skill_sha": self.skill_sha,
            "ecosystem_quality": {
                "static_valid": True,
                "provenance": True,
                "installability": True,
                "security": True,
                "documentation": True,
                "compatibility": True,
                "drift_free": True,
            },
            "verified_capability": {
                "routing_f1": 0.9,
                "task_pass_rate": 0.8,
                "skill_lift": 0.6,
                "candidate_delta": 0.5,
                "generalization_gap": 0.1,
                "cross_harness_variance": 0.02,
                "recovery_rate": 0.8,
                "safety_pass_rate": 1.0,
                "capability_unlock_count": 1,
            },
        }

    def land_bundle(self, case_id: str, model: str, harness: str, runtime: str, suffix: str) -> str:
        run_id = f"run-{suffix}-12345678"
        run = self.root / "runs" / f"{suffix}.json"
        receipt = self.root / "receipts" / f"{suffix}.json"
        bundle = self.root / "bundles" / f"{suffix}.json"
        for path in (run, receipt, bundle):
            path.parent.mkdir(parents=True, exist_ok=True)
        run.write_text(json.dumps({
            "schema_version": "skill-eval-run/v1",
            "run_id": run_id,
            "case_id": case_id,
            "skill_sha": self.skill_sha,
            "model": {"name": model},
            "harness": {"name": harness},
            "environment": {"runtime": runtime},
        }), encoding="utf-8")
        receipt.write_text(json.dumps({
            "schema_version": "skill-eval-verifier-receipt/v1",
            "run_id": run_id,
            "case_id": case_id,
            "authority": "deterministic",
            "passed": True,
        }), encoding="utf-8")
        bundle.write_text(json.dumps({
            "schema_version": "skill-eval-evidence/v1",
            "run_id": run_id,
            "case_id": case_id,
            "skill_sha": self.skill_sha,
            "eval_suite_sha": self.eval_sha,
            "promotion_eligible": True,
            "verifier_receipt": receipt.relative_to(self.root).as_posix(),
            "verifier_receipt_sha256": hashlib.sha256(receipt.read_bytes()).hexdigest(),
            "run_trace": run.relative_to(self.root).as_posix(),
        }), encoding="utf-8")
        return bundle.relative_to(self.root).as_posix()

    def validate(self) -> None:
        validate_release(self.release, {"unlock-demo": self.unlock}, self.root)

    def test_good_release_passes(self) -> None:
        self.validate()

    def test_missing_unlock_cannot_be_compensated_by_scorecard(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing capability unlock"):
            validate_release(self.release, {}, self.root)

    def test_eval_suite_sha_is_bound_to_evidence(self) -> None:
        self.release["eval_suite_sha"] = "d" * 40
        with self.assertRaisesRegex(ValueError, "eval_suite_sha mismatch"):
            self.validate()

    def test_tampered_verifier_receipt_fails_digest(self) -> None:
        bundle = json.loads((self.root / self.refs[0]).read_text())
        receipt = self.root / bundle["verifier_receipt"]
        value = json.loads(receipt.read_text())
        value["passed"] = False
        receipt.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            self.validate()

    def test_release_matrix_must_be_physically_observed(self) -> None:
        self.release["model_harness_matrix"][1]["harness"] = "unseen-harness"
        with self.assertRaisesRegex(ValueError, "cover every model/harness"):
            self.validate()

    def test_rollback_artifact_is_content_bound(self) -> None:
        (self.root / self.release["rollback_artifact"]).write_text("tampered\n")
        with self.assertRaisesRegex(ValueError, "rollback artifact digest"):
            self.validate()

    def test_scorecard_cannot_collapse_to_overall_score(self) -> None:
        path = self.root / self.release["scorecard"]
        value = json.loads(path.read_text())
        value["overall_score"] = 0.99
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "overall_score"):
            self.validate()

    def test_scorecard_must_expose_cross_harness_risk(self) -> None:
        path = self.root / self.release["scorecard"]
        value = json.loads(path.read_text())
        value["verified_capability"]["generalization_gap"] = None
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "generalization_gap"):
            self.validate()

    def test_skill_sha_must_be_exact_lowercase_commit_sha(self) -> None:
        self.release["skill_sha"] = "abc123"
        with self.assertRaisesRegex(ValueError, "40-char"):
            self.validate()

    def test_eval_suite_sha_must_be_exact_lowercase_commit_sha(self) -> None:
        self.release["eval_suite_sha"] = "B" * 40
        with self.assertRaisesRegex(ValueError, "eval_suite_sha"):
            self.validate()

    def test_rollback_sha_must_be_exact_lowercase_commit_sha(self) -> None:
        self.release["rollback_sha"] = "not-a-sha"
        with self.assertRaisesRegex(ValueError, "rollback_sha"):
            self.validate()

    def test_generalization_gap_cannot_be_negative(self) -> None:
        path = self.root / self.release["scorecard"]
        value = json.loads(path.read_text())
        value["verified_capability"]["generalization_gap"] = -0.01
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "generalization_gap"):
            self.validate()

    def test_cross_harness_variance_cannot_be_negative(self) -> None:
        path = self.root / self.release["scorecard"]
        value = json.loads(path.read_text())
        value["verified_capability"]["cross_harness_variance"] = -0.01
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "cross_harness_variance"):
            self.validate()

    def test_unknown_release_fields_fail_closed(self) -> None:
        self.release["overall_score"] = 0.99
        with self.assertRaisesRegex(ValueError, "unexpected fields"):
            self.validate()


if __name__ == "__main__":
    unittest.main()
