from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_held_out_corpus.py"
SCHEMA_ROOT = ROOT / "references"


def digest(seed: str) -> str:
    return (seed * 64)[:64]


def repository(name: str, language: str, shape: str, boundary: str,
               commit_seed: str, tree_seed: str, **overrides) -> dict:
    base = {
        "repository_id": f"example/{name}",
        "commit_sha": commit_seed * 40,
        "tree_sha": tree_seed * 40,
        "language": language,
        "build_shape": shape,
        "capability_boundary": boundary,
        "license_state": "MIT, redistribution permitted",
        "authorization_state": "PUBLIC",
        "used_to_design_fixtures": False,
        "prerequisites": ["python3"],
        "cleanup_policy": "discard the worktree after the run",
    }
    base.update(overrides)
    return base


def family(family_id: str, repository_id: str, seed: str, **overrides) -> dict:
    base = {
        "family_id": family_id,
        "repository_id": repository_id,
        "hidden_task_digest": digest(seed),
        "ground_truth_digest": digest(seed.upper() if seed.isalpha() else seed + "f"),
        "required_evidence_levels": ["L2"],
        "forbidden_evidence_levels": ["L5"],
        "expected_non_claims": ["no cross-model generalization"],
    }
    base.update(overrides)
    return base


def corpus() -> dict:
    return {
        "schema": "held-out-corpus/v1",
        "corpus_id": "rca-holdout-fixture",
        "frozen_at_commit": "a" * 40,
        "repositories": [
            repository("alpha", "python", "poetry", "local-cli", "a", "b"),
            repository("bravo", "typescript", "npm-workspace", "browser-runtime", "c", "d"),
            repository("charlie", "go", "go-modules", "network-service", "e", "f"),
        ],
        "task_families": [
            family("real-capability-with-evidence", "example/alpha", "1"),
            family("overstated-readme-claim", "example/bravo", "2"),
            family("skipped-or-absent-integration", "example/charlie", "3"),
            family("failure-path-evidence-loss", "example/alpha", "4"),
            family("text-only-non-trigger", "example/bravo", "5"),
            family("metadata-only-control", "example/charlie", "6"),
            family("wrong-skill-control", "example/alpha", "7"),
        ],
        "evaluator": {
            "evaluator_id": "deterministic-audit-evaluator",
            "version": "1.0.0",
            "digest": digest("e"),
            "owner": "INDEPENDENT_DETERMINISTIC",
            "hard_gates": [
                "exact-subject-continuity",
                "required-command-runtime-arrival",
                "evidence-packet-digest-continuity",
                "valid-positive-and-negative-controls",
                "false-pass-detection",
                "explicit-non-claim-bounds",
            ],
        },
        "sealed_material": {
            "location": "sealed://rca-holdout/2026-08",
            "visible_to_evaluated_agent": False,
            "resolved_in": "TRUSTED_EVALUATION_RUNTIME",
        },
    }


def run(document: dict) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "corpus.json"
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        process = subprocess.run(
            [sys.executable, str(CHECKER), str(path), "--schema-root", str(SCHEMA_ROOT)],
            capture_output=True, text=True, check=False,
        )
        return process.returncode, process.stderr


class HeldOutCorpusTests(unittest.TestCase):
    def test_a_separated_corpus_is_admissible(self):
        code, stderr = run(corpus())
        self.assertEqual(code, 0, stderr)

    def test_a_tuning_repository_is_not_held_out(self):
        document = corpus()
        document["repositories"][1]["used_to_design_fixtures"] = True
        code, stderr = run(document)
        self.assertEqual(code, 2)
        self.assertIn("not-held-out", stderr)

    def test_unauthorized_private_repository_is_refused(self):
        document = corpus()
        document["repositories"][0]["authorization_state"] = "PRIVATE_UNAUTHORIZED"
        code, stderr = run(document)
        self.assertEqual(code, 2)
        self.assertIn("unauthorized-repository", stderr)

    def test_one_repository_listed_three_times_is_not_a_set(self):
        document = corpus()
        document["repositories"][1]["repository_id"] = "example/alpha"
        document["repositories"][2]["repository_id"] = "example/alpha"
        code, stderr = run(document)
        self.assertEqual(code, 2)
        self.assertIn("duplicate-repository", stderr)

    def test_corpus_must_vary_across_each_declared_dimension(self):
        for dimension, value in (("language", "python"), ("build_shape", "poetry"),
                                 ("capability_boundary", "local-cli")):
            with self.subTest(dimension=dimension):
                document = corpus()
                for repo in document["repositories"]:
                    repo[dimension] = value
                code, stderr = run(document)
                self.assertEqual(code, 2)
                self.assertIn(f"corpus-not-varied:{dimension}", stderr)

    def test_a_family_cannot_name_an_unlisted_repository(self):
        document = corpus()
        document["task_families"][0]["repository_id"] = "example/absent"
        code, stderr = run(document)
        self.assertEqual(code, 2)
        self.assertIn("family-unknown-repository", stderr)

    def test_required_and_forbidden_evidence_cannot_overlap(self):
        document = corpus()
        document["task_families"][0]["forbidden_evidence_levels"] = ["L2"]
        code, stderr = run(document)
        self.assertEqual(code, 2)
        self.assertIn("evidence-level-contradiction", stderr)

    def test_task_digest_equal_to_ground_truth_shows_the_answer(self):
        document = corpus()
        family_entry = document["task_families"][0]
        family_entry["ground_truth_digest"] = family_entry["hidden_task_digest"]
        code, stderr = run(document)
        self.assertEqual(code, 2)
        self.assertIn("task-equals-ground-truth", stderr)

    def test_non_trigger_families_are_required(self):
        document = corpus()
        document["task_families"] = [
            f for f in document["task_families"] if f["family_id"] != "wrong-skill-control"
        ]
        code, stderr = run(document)
        self.assertEqual(code, 2)
        self.assertIn("non-trigger-families-absent", stderr)

    def test_a_corpus_of_only_defects_is_refused(self):
        document = corpus()
        document["task_families"] = [
            f for f in document["task_families"]
            if f["family_id"] != "real-capability-with-evidence"
        ]
        code, stderr = run(document)
        self.assertEqual(code, 2)
        self.assertIn("positive-family-absent", stderr)

    def test_too_few_defect_families_is_refused(self):
        document = corpus()
        document["task_families"] = [
            f for f in document["task_families"]
            if f["family_id"] not in {"overstated-readme-claim", "skipped-or-absent-integration"}
        ]
        code, stderr = run(document)
        self.assertEqual(code, 2)
        self.assertIn("too-few-defect-families", stderr)

    def test_families_sharing_one_ground_truth_are_refused(self):
        document = corpus()
        shared = document["task_families"][0]["ground_truth_digest"]
        document["task_families"][1]["ground_truth_digest"] = shared
        code, stderr = run(document)
        self.assertEqual(code, 2)
        self.assertIn("shared-ground-truth-digest", stderr)

    def test_the_evaluated_agent_cannot_be_named_as_evaluator(self):
        document = corpus()
        document["evaluator"]["owner"] = "EVALUATED_AGENT"
        code, stderr = run(document)
        self.assertEqual(code, 64)
        self.assertIn("schema-invalid", stderr)

    def test_visible_sealed_material_is_not_sealed(self):
        document = corpus()
        document["sealed_material"]["visible_to_evaluated_agent"] = True
        code, stderr = run(document)
        self.assertEqual(code, 64)
        self.assertIn("schema-invalid", stderr)

    def test_fewer_than_three_repositories_is_refused(self):
        document = corpus()
        document["repositories"] = document["repositories"][:2]
        code, stderr = run(document)
        self.assertEqual(code, 64)
        self.assertIn("schema-invalid", stderr)

    def test_the_committed_corpus_is_admissible(self):
        # Zero network: the corpus is a static file and the checker reads only it.
        # Resolving ground truth needs the pinned trees; checking separation does not.
        corpus_path = ROOT / "evals" / "held-out-corpus.json"
        self.assertTrue(corpus_path.is_file(), "the committed corpus is missing")
        process = subprocess.run(
            [sys.executable, str(CHECKER), str(corpus_path), "--schema-root", str(SCHEMA_ROOT)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(process.returncode, 0, process.stderr)

    def test_the_committed_corpus_covers_every_declared_family(self):
        document = json.loads((ROOT / "evals" / "held-out-corpus.json").read_text(encoding="utf-8"))
        schema = json.loads(
            (SCHEMA_ROOT / "held-out-corpus.schema.json").read_text(encoding="utf-8")
        )
        declared = set(schema["$defs"]["family_id"]["enum"])
        present = {family["family_id"] for family in document["task_families"]}
        # A corpus covering nine of eleven families reads as complete once the
        # count is summarised, so the gap is asserted rather than eyeballed.
        self.assertEqual(present, declared, f"families not covered: {sorted(declared - present)}")

    def test_absent_input_stays_distinct(self):
        process = subprocess.run(
            [sys.executable, str(CHECKER), str(ROOT / "tests" / "fixtures" / "absent.json")],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(process.returncode, 64)
        self.assertIn("absent-input", process.stderr)


if __name__ == "__main__":
    unittest.main()
