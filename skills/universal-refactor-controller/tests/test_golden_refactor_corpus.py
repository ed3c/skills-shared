from __future__ import annotations

import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CANARY_ROOT = ROOT / "evals" / "canaries"
SCHEMA = CANARY_ROOT / "golden-refactor-corpus.schema.json"
INDEX = CANARY_ROOT / "golden-refactor-corpus.index.json"


class GoldenRefactorCorpusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.index = json.loads(INDEX.read_text(encoding="utf-8"))

    def test_index_is_schema_valid(self) -> None:
        errors = sorted(
            Draft202012Validator(self.schema).iter_errors(self.index),
            key=lambda item: list(item.absolute_path),
        )
        self.assertEqual([], errors, [error.message for error in errors])

    def test_open_canaries_are_not_promoted_to_golden(self) -> None:
        self.assertGreaterEqual(len(self.index["cases"]), 2)
        for case in self.index["cases"]:
            self.assertEqual("HOLD_UNMERGED", case["promotion_state"], case["id"])
            self.assertEqual("PASS", case["verification"]["state"], case["id"])

    def test_every_case_has_strict_non_loc_reduction(self) -> None:
        for case in self.index["cases"]:
            delta = case["complexity_delta"]
            self.assertNotIn(delta["dimension"], {"lines", "loc", "files"})
            self.assertLess(delta["after"], delta["before"], case["id"])
            self.assertTrue(delta["protected_non_regression"], case["id"])

    def test_open_pr_head_sha_is_not_durable_corpus_state(self) -> None:
        forbidden = {"head_sha", "candidate_head_sha", "open_pr_head_sha"}
        for case in self.index["cases"]:
            self.assertTrue(forbidden.isdisjoint(case), case["id"])
            serialized = json.dumps(case, sort_keys=True)
            self.assertNotIn("candidate_head_sha", serialized)

    def test_two_materially_different_target_classes_are_present(self) -> None:
        self.assertEqual({"SKILL", "REPOSITORY"}, {case["target_kind"] for case in self.index["cases"]})


if __name__ == "__main__":
    unittest.main()
