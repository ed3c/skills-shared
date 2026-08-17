#!/usr/bin/env python3
"""Perturbation declarations must be decided by the committed schemas.

A perturbation axis that nothing validates is decoration: a typo'd axis, a
perturbation with no stated expected effect, or a run trace claiming a
perturbation that no case declares would all ride into the eval corpus looking
green. These tests execute the committed schemas over the committed cases and
over a run trace produced by the real normalizer, then plant one defect per
constraint so the schemas are shown to go RED rather than merely parse.

The run-trace side keeps three states distinct on purpose: the normalizer today
emits no `perturbation` key at all (it cannot yet be told about one), an
explicit null means an undisturbed baseline run, and an object means a named
perturbation was applied.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "evals" / "schema"
CONTRACT_SCHEMA = SCHEMAS / "skill-eval-contract.schema.json"
RUN_TRACE_SCHEMA = SCHEMAS / "run-trace.schema.json"
NORMALIZER = ROOT / "evals" / "adapters" / "normalize_run.py"
WORKED_EXAMPLE = ROOT / "evals" / "cases" / "autoresearch-composer" / "autoresearch-metric-loop-plan.json"
AXES = {"context", "tool", "state", "task"}


def validator(schema_path: Path):
    from jsonschema import Draft202012Validator

    return Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def case_paths() -> list[Path]:
    roots = [ROOT / "evals" / "cases", ROOT / "evals" / "holdout"]
    return sorted(p for root in roots if root.exists() for p in root.rglob("*.json"))


class CasePerturbationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = validator(CONTRACT_SCHEMA)
        self.case = load(WORKED_EXAMPLE)

    def assert_rejected(self, case: dict, keyword: str) -> None:
        errors = list(self.validator.iter_errors(case))
        self.assertTrue(errors, "schema accepted a planted defect")
        self.assertIn(keyword, {error.validator for error in errors})

    def test_committed_cases_satisfy_the_contract_schema(self) -> None:
        paths = case_paths()
        self.assertTrue(paths, "no committed eval cases to validate")
        for path in paths:
            with self.subTest(case=str(path.relative_to(ROOT))):
                errors = [error.message for error in self.validator.iter_errors(load(path))]
                self.assertEqual(errors, [])

    def test_worked_example_declares_every_perturbation_axis(self) -> None:
        perturbations = self.case.get("perturbations")
        self.assertIsInstance(perturbations, list)
        self.assertEqual({item["axis"] for item in perturbations}, AXES)
        ids = [item["id"] for item in perturbations]
        self.assertEqual(len(ids), len(set(ids)), "perturbation ids must be unique for run binding")

    def test_unknown_axis_is_rejected(self) -> None:
        self.case["perturbations"][0]["axis"] = "network"
        self.assert_rejected(self.case, "enum")

    def test_perturbation_without_expected_effect_is_rejected(self) -> None:
        self.case["perturbations"][0].pop("expected_effect")
        self.assert_rejected(self.case, "required")

    def test_unnamed_perturbation_is_rejected(self) -> None:
        self.case["perturbations"][0]["id"] = "Context Drop"
        self.assert_rejected(self.case, "pattern")

    def test_extra_perturbation_property_is_rejected(self) -> None:
        self.case["perturbations"][0]["applied"] = True
        self.assert_rejected(self.case, "additionalProperties")

    def test_empty_perturbations_array_is_rejected(self) -> None:
        self.case["perturbations"] = []
        self.assert_rejected(self.case, "minItems")


class RunTracePerturbationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = validator(RUN_TRACE_SCHEMA)
        self.trace = self.normalized_run()

    def normalized_run(self) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            source, out = tmp / "raw.json", tmp / "run.json"
            source.write_text(json.dumps({"passed": True, "verifier": "script"}), encoding="utf-8")
            proc = subprocess.run(
                [
                    "python3", str(NORMALIZER), "--adapter", "generic", "--input", str(source),
                    "--case-id", "autoresearch-metric-loop-plan", "--condition", "candidate_skill",
                    "--skill-sha", "abcdef0123456789", "--eval-suite-sha", "1234567abcdef",
                    "--model-provider", "test", "--model-name", "model-a",
                    "--harness-name", "arena", "--harness-version", "1",
                    "--runtime", "docker", "--network-policy", "no-network",
                    "--fresh-workspace", "--seed", "7", "--output", str(out),
                ],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            return json.loads(out.read_text(encoding="utf-8"))

    def assert_rejected(self, trace: dict, keyword: str) -> None:
        errors = list(self.validator.iter_errors(trace))
        self.assertTrue(errors, "schema accepted a planted defect")
        self.assertIn(keyword, {error.validator for error in errors})

    def test_emitted_run_trace_stays_valid(self) -> None:
        self.assertEqual([error.message for error in self.validator.iter_errors(self.trace)], [])

    def test_absent_null_and_named_perturbation_are_all_accepted(self) -> None:
        states = {
            "absent": dict(self.trace),
            "baseline": dict(self.trace, perturbation=None),
            "applied": dict(self.trace, perturbation={"id": "context-drop-metric-definition", "axis": "context"}),
        }
        for label, trace in states.items():
            with self.subTest(state=label):
                self.assertEqual([error.message for error in self.validator.iter_errors(trace)], [])

    def test_run_trace_perturbation_axis_is_enumerated(self) -> None:
        self.trace["perturbation"] = {"id": "context-drop-metric-definition", "axis": "vibes"}
        self.assert_rejected(self.trace, "enum")

    def test_run_trace_perturbation_must_be_identified(self) -> None:
        self.trace["perturbation"] = {"axis": "context"}
        self.assert_rejected(self.trace, "required")

    def test_run_trace_perturbation_rejects_extra_properties(self) -> None:
        self.trace["perturbation"] = {
            "id": "context-drop-metric-definition", "axis": "context", "promoted": True,
        }
        self.assert_rejected(self.trace, "additionalProperties")

    def test_every_declared_perturbation_projects_into_a_valid_run_trace(self) -> None:
        for declared in load(WORKED_EXAMPLE)["perturbations"]:
            with self.subTest(perturbation=declared["id"]):
                trace = dict(self.trace, perturbation={"id": declared["id"], "axis": declared["axis"]})
                self.assertEqual([error.message for error in self.validator.iter_errors(trace)], [])


class SchemaHealthTests(unittest.TestCase):
    def test_committed_schemas_are_valid_draft_2020_12(self) -> None:
        from jsonschema import Draft202012Validator

        for path in (CONTRACT_SCHEMA, RUN_TRACE_SCHEMA):
            Draft202012Validator.check_schema(load(path))


if __name__ == "__main__":
    unittest.main()
