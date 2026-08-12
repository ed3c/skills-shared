from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.check_mutation_lineage import validate


class MutationLineageTests(unittest.TestCase):
    def good(self):
        return {
            "schema_version": "skill-mutation/v1",
            "skill": "autoresearch-composer",
            "parent_sha": "abcdef0123456789",
            "candidate_sha": "1234567abcdef890",
            "hypothesis": "Explicit recovery before generation improves target task pass rate.",
            "mutation_class": "recovery",
            "target_failures": ["context-loss"],
            "changed_sections": ["S5 recover"],
            "expected_effect": {
                "metric": "task_pass_rate",
                "minimum_delta": 0.5,
                "case_ids": ["target-case"],
            },
            "regression_budget": 0.0,
            "status": "proposed",
            "evaluation_receipt": None,
            "rollback_sha": "abcdef0123456789",
        }

    def write_evidence(self, root: Path, *, case_id: str, skill_sha: str | None, passed: bool, name: str) -> str:
        run_id = f"run-{name}-12345678"
        runs = root / "evidence" / "runs"
        receipts = root / "evidence" / "receipts"
        bundles = root / "evidence" / "bundles"
        runs.mkdir(parents=True, exist_ok=True)
        receipts.mkdir(parents=True, exist_ok=True)
        bundles.mkdir(parents=True, exist_ok=True)
        run = runs / f"{name}.json"
        verifier = receipts / f"{name}.json"
        bundle = bundles / f"{name}.json"
        run.write_text(
            json.dumps(
                {
                    "schema_version": "skill-eval-run/v1",
                    "run_id": run_id,
                    "case_id": case_id,
                    "skill_sha": skill_sha,
                    "outcome": {"passed": passed},
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        verifier.write_text(
            json.dumps(
                {
                    "schema_version": "skill-eval-verifier-receipt/v1",
                    "authority": "deterministic",
                    "passed": passed,
                    "run_id": run_id,
                    "case_id": case_id,
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        bundle.write_text(
            json.dumps(
                {
                    "schema_version": "skill-eval-evidence/v1",
                    "run_id": run_id,
                    "case_id": case_id,
                    "skill_sha": skill_sha,
                    "run_trace": run.relative_to(root).as_posix(),
                    "verifier_receipt": verifier.relative_to(root).as_posix(),
                    "verifier_receipt_sha256": hashlib.sha256(verifier.read_bytes()).hexdigest(),
                    "promotion_eligible": passed,
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return bundle.relative_to(root).as_posix()

    def winning_receipt(
        self,
        root: Path,
        value: dict,
        *,
        regress: bool = False,
        extra_candidate: bool = False,
        extra_no_skill: bool = False,
        omit_no_skill: bool = False,
        foreign: bool = False,
    ) -> str:
        refs = [
            self.write_evidence(root, case_id="target-case", skill_sha=value["parent_sha"], passed=False, name="target-parent"),
            self.write_evidence(root, case_id="target-case", skill_sha=value["candidate_sha"], passed=True, name="target-candidate"),
            self.write_evidence(root, case_id="control-case", skill_sha=value["parent_sha"], passed=True, name="control-parent"),
            self.write_evidence(root, case_id="control-case", skill_sha=value["candidate_sha"], passed=not regress, name="control-candidate"),
        ]
        if not omit_no_skill:
            refs.extend(
                [
                    self.write_evidence(root, case_id="target-case", skill_sha=None, passed=False, name="target-no-skill"),
                    self.write_evidence(root, case_id="control-case", skill_sha=None, passed=False, name="control-no-skill"),
                ]
            )
        if extra_candidate:
            refs.append(
                self.write_evidence(root, case_id="target-case", skill_sha=value["candidate_sha"], passed=True, name="target-candidate-extra")
            )
        if extra_no_skill:
            refs.append(
                self.write_evidence(root, case_id="target-case", skill_sha=None, passed=False, name="target-no-skill-extra")
            )
        if foreign:
            refs[1] = self.write_evidence(root, case_id="target-case", skill_sha="9999999abcdef000", passed=True, name="target-foreign")
        receipt = root / "mutations" / "receipts" / "decision.json"
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(
            json.dumps(
                {
                    "schema_version": "skill-mutation-eval/v1",
                    "skill": value["skill"],
                    "parent_sha": value["parent_sha"],
                    "candidate_sha": value["candidate_sha"],
                    "metric": "task_pass_rate",
                    "target_case_ids": ["target-case"],
                    "non_target_case_ids": ["control-case"],
                    "evidence_bundles": refs,
                }
            ),
            encoding="utf-8",
        )
        return receipt.relative_to(root).as_posix()

    def test_good_proposed_record_passes(self):
        validate(self.good())

    def test_candidate_must_differ_from_parent(self):
        value = self.good()
        value["candidate_sha"] = value["parent_sha"]
        with self.assertRaisesRegex(ValueError, "differ"):
            validate(value)

    def test_rollback_must_pin_parent(self):
        value = self.good()
        value["rollback_sha"] = "fedcba0987654321"
        with self.assertRaisesRegex(ValueError, "rollback"):
            validate(value)

    def test_terminal_status_requires_evaluation_receipt(self):
        value = self.good()
        value["status"] = "won"
        with self.assertRaisesRegex(ValueError, "evaluation_receipt"):
            validate(value)

    def test_won_is_recomputed_from_three_arm_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            value = self.good()
            value["status"] = "won"
            value["evaluation_receipt"] = self.winning_receipt(root, value)
            validate(value, root)

    def test_won_rejects_non_target_regression(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            value = self.good()
            value["status"] = "won"
            value["evaluation_receipt"] = self.winning_receipt(root, value, regress=True)
            with self.assertRaisesRegex(ValueError, "fails admission"):
                validate(value, root)

    def test_terminal_requires_no_skill_baseline(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            value = self.good()
            value["status"] = "won"
            value["evaluation_receipt"] = self.winning_receipt(root, value, omit_no_skill=True)
            with self.assertRaisesRegex(ValueError, "current/candidate/no-skill"):
                validate(value, root)

    def test_won_rejects_candidate_denominator_cherry_pick(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            value = self.good()
            value["status"] = "won"
            value["evaluation_receipt"] = self.winning_receipt(root, value, extra_candidate=True)
            with self.assertRaisesRegex(ValueError, "denominator mismatch"):
                validate(value, root)

    def test_won_rejects_no_skill_denominator_drift(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            value = self.good()
            value["status"] = "won"
            value["evaluation_receipt"] = self.winning_receipt(root, value, extra_no_skill=True)
            with self.assertRaisesRegex(ValueError, "denominator mismatch"):
                validate(value, root)

    def test_won_rejects_foreign_skill_sha(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            value = self.good()
            value["status"] = "won"
            value["evaluation_receipt"] = self.winning_receipt(root, value, foreign=True)
            with self.assertRaisesRegex(ValueError, "neither parent, candidate, nor no-skill"):
                validate(value, root)

    def test_lost_cannot_hide_winning_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            value = self.good()
            value["status"] = "lost"
            value["evaluation_receipt"] = self.winning_receipt(root, value)
            with self.assertRaisesRegex(ValueError, "marked lost"):
                validate(value, root)

    def test_running_record_cannot_claim_terminal_receipt(self):
        value = self.good()
        value["status"] = "running"
        value["evaluation_receipt"] = "mutations/receipts/fake.json"
        with self.assertRaisesRegex(ValueError, "must not claim"):
            validate(value)

    def test_terminal_non_replayable_metric_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            value = self.good()
            value["status"] = "won"
            value["expected_effect"]["metric"] = "recovery_rate"
            value["evaluation_receipt"] = self.winning_receipt(root, value)
            receipt_path = root / value["evaluation_receipt"]
            receipt = json.loads(receipt_path.read_text())
            receipt["metric"] = "recovery_rate"
            receipt_path.write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError, "supports only task_pass_rate"):
                validate(value, root)

    def test_mutation_class_is_controlled(self):
        value = self.good()
        value["mutation_class"] = "rewrite-everything"
        with self.assertRaisesRegex(ValueError, "mutation_class"):
            validate(value)


if __name__ == "__main__":
    unittest.main()
