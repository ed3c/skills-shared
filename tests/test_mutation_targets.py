from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.check_mutation_targets import check


class MutationTargetVisibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "evals" / "cases" / "demo").mkdir(parents=True)
        (self.root / "evals" / "holdout" / "demo").mkdir(parents=True)
        (self.root / "mutations" / "demo-skill").mkdir(parents=True)
        (self.root / "mutations" / "receipts").mkdir(parents=True)
        self.write_case("target-case", "demo-skill", "dev", holdout=False)
        self.write_case("control-case", "demo-skill", "gold-replay", holdout=False)
        self.write_case("sealed-case", "demo-skill", "holdout", holdout=True)
        self.write_record(["target-case"])

    def tearDown(self) -> None:
        self.tmp.cleanup()

    @property
    def mutation_path(self) -> Path:
        return self.root / "mutations" / "demo-skill" / "lineage.jsonl"

    def write_case(self, case_id: str, skill: str, split: str, *, holdout: bool) -> None:
        base = self.root / "evals" / ("holdout" if holdout else "cases") / "demo"
        base.mkdir(parents=True, exist_ok=True)
        (base / f"{case_id}.json").write_text(
            json.dumps({"id": case_id, "skill": skill, "split": split}),
            encoding="utf-8",
        )

    def write_record(self, targets: list[str], *, receipt: str | None = None) -> None:
        value = {
            "skill": "demo-skill",
            "expected_effect": {"case_ids": targets},
            "evaluation_receipt": receipt,
        }
        self.mutation_path.write_text(json.dumps(value) + "\n", encoding="utf-8")

    def write_receipt(self, *, targets: list[str], controls: list[str]) -> str:
        path = self.root / "mutations" / "receipts" / "decision.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": "skill-mutation-eval/v1",
                    "target_case_ids": targets,
                    "non_target_case_ids": controls,
                }
            ),
            encoding="utf-8",
        )
        return path.relative_to(self.root).as_posix()

    def assert_fails_with(self, needle: str) -> None:
        count, errors = check(self.root)
        self.assertEqual(count, 1)
        self.assertTrue(errors, "mutation target gate unexpectedly passed")
        self.assertIn(needle, "\n".join(errors))

    def test_visible_same_skill_target_passes(self) -> None:
        count, errors = check(self.root)
        self.assertEqual(count, 1)
        self.assertEqual(errors, [])

    def test_missing_target_case_fails(self) -> None:
        self.write_record(["does-not-exist"])
        self.assert_fails_with("references missing eval case")

    def test_cross_skill_target_fails(self) -> None:
        self.write_case("other-case", "other-skill", "dev", holdout=False)
        self.write_record(["other-case"])
        self.assert_fails_with("belongs to other-skill, not demo-skill")

    def test_optimizer_cannot_target_sealed_holdout(self) -> None:
        self.write_record(["sealed-case"])
        self.assert_fails_with("must not be sealed holdout")

    def test_terminal_receipt_target_cannot_be_holdout(self) -> None:
        receipt = self.write_receipt(targets=["sealed-case"], controls=["control-case"])
        self.write_record(["target-case"], receipt=receipt)
        self.assert_fails_with("mutation receipt target_case_ids")

    def test_holdout_may_be_non_target_control(self) -> None:
        receipt = self.write_receipt(targets=["target-case"], controls=["sealed-case"])
        self.write_record(["target-case"], receipt=receipt)
        count, errors = check(self.root)
        self.assertEqual(count, 1)
        self.assertEqual(errors, [])

    def test_terminal_control_must_exist_and_match_skill(self) -> None:
        receipt = self.write_receipt(targets=["target-case"], controls=["missing-control"])
        self.write_record(["target-case"], receipt=receipt)
        self.assert_fails_with("mutation receipt non_target_case_ids references missing eval case")

    def test_duplicate_eval_case_ids_fail_closed(self) -> None:
        self.write_case("target-case", "demo-skill", "gold-replay", holdout=True)
        with self.assertRaisesRegex(ValueError, "duplicate eval case id"):
            check(self.root)


if __name__ == "__main__":
    unittest.main()
