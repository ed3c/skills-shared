from __future__ import annotations

import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CANARY_ROOT = ROOT / "evals" / "canaries"
SCHEMA = CANARY_ROOT / "golden-refactor-corpus.schema.json"
INDEX = CANARY_ROOT / "golden-refactor-corpus.index.json"
TRACE = ROOT / "references" / "ucr-program-trace.json"


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

    def test_program_trace_is_acyclic_and_has_one_current_convergence_owner(self) -> None:
        trace = json.loads(TRACE.read_text(encoding="utf-8"))
        self.assertEqual("universal-refactor/program-trace/v1", trace["schema_version"])
        ids = [node["id"] for node in trace["nodes"]]
        self.assertEqual(len(ids), len(set(ids)))
        known = set(ids)
        graph: dict[str, list[str]] = {node_id: [] for node_id in ids}
        for edge in trace["edges"]:
            self.assertIn(edge["from"], known)
            self.assertIn(edge["to"], known)
            graph[edge["from"]].append(edge["to"])

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> None:
            self.assertNotIn(node, visiting, f"cycle through {node}")
            if node in visited:
                return
            visiting.add(node)
            for child in graph[node]:
                visit(child)
            visiting.remove(node)
            visited.add(node)

        for node_id in ids:
            visit(node_id)

        current = [
            node for node in trace["nodes"]
            if node["stack_class"] == "CONVERGENCE_DOCUMENTATION"
            and node["evidence_state"] == "IMPLEMENTING"
        ]
        self.assertEqual(["UCR-X-D"], [node["id"] for node in current])

    def test_program_trace_has_no_mutable_open_head_sha_fields(self) -> None:
        trace = json.loads(TRACE.read_text(encoding="utf-8"))
        forbidden = {"head", "head_sha", "candidate_head_sha", "open_pr_head_sha"}
        for node in trace["nodes"]:
            self.assertTrue(forbidden.isdisjoint(node), node["id"])


if __name__ == "__main__":
    unittest.main()
