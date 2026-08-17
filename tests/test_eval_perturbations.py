#!/usr/bin/env python3
"""Perturbation declarations must be decided by the committed schemas.

A perturbation axis that nothing validates is decoration: a typo'd axis, a
perturbation with no stated expected effect, or a run trace claiming a
perturbation that no case declares would all ride into the eval corpus looking
green. These tests execute the committed schemas over the committed cases and
over a run trace produced by the real normalizer, then plant one defect per
constraint so the schemas are shown to go RED rather than merely parse.

The run-trace side keeps three states distinct on purpose, and the normalizer
now emits all three: passing no perturbation flag omits the key (the harness
invocation does not record perturbation identity), `--no-perturbation` writes an
explicit null (measured undisturbed baseline), and an id plus axis writes the
named object.

Run identity is checked on both edges. An applied perturbation must change
run_id -- otherwise two runs differing only by which disturbance was applied
collide into one -- while an undisturbed run must reproduce the committed
fixture byte for byte, because a run_id formula that silently rewrites itself
invalidates every id an earlier revision emitted.
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
RUN_IDENTITY_FIXTURES = ROOT / "evals" / "fixtures" / "run-identity"
COMMITTED_BASELINE = RUN_IDENTITY_FIXTURES / "baseline-absent.json"
COMMITTED_PERTURBED = RUN_IDENTITY_FIXTURES / "perturbed-context-drop.json"
AXES = {"context", "tool", "state", "task"}

# The exact argv that produced the committed baseline fixture. Keeping it here
# rather than in the fixture keeps the fixture a pure artifact; the identity
# test replays this and compares bytes.
FIXTURE_RAW = {
    "passed": True, "verifier": "script", "selected_skill": "autoresearch-composer",
    "did_invoke": True, "wall_seconds": 2.5, "tool_calls": 3, "input_tokens": 100,
    "output_tokens": 20, "retries": 0,
}
FIXTURE_ARGS = [
    "--adapter", "generic", "--case-id", "autoresearch-metric-loop-plan",
    "--condition", "candidate_skill", "--skill-sha", "abcdef0123456789",
    "--eval-suite-sha", "1234567abcdef", "--model-provider", "test",
    "--model-name", "model-a", "--harness-name", "arena", "--harness-version", "1",
    "--runtime", "docker", "--network-policy", "no-network", "--fresh-workspace",
    "--seed", "7", "--should-invoke",
]


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


def run_normalizer(tmp: Path, *extra: str) -> tuple[subprocess.CompletedProcess[str], Path]:
    source, out = tmp / "raw.json", tmp / "run.json"
    source.write_text(json.dumps(FIXTURE_RAW), encoding="utf-8")
    proc = subprocess.run(
        ["python3", str(NORMALIZER), *FIXTURE_ARGS, "--input", str(source), "--output", str(out), *extra],
        text=True, capture_output=True, check=False,
    )
    return proc, out


class RunTracePerturbationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = validator(RUN_TRACE_SCHEMA)
        self.trace = self.normalized_run()

    def normalized_run(self, *extra: str) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            proc, out = run_normalizer(Path(tmp), *extra)
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


class EmittedPerturbationStateTests(unittest.TestCase):
    """The production emitter must be able to reach all three states itself."""

    def setUp(self) -> None:
        self.validator = validator(RUN_TRACE_SCHEMA)

    def normalized_run(self, *extra: str) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            proc, out = run_normalizer(Path(tmp), *extra)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            return json.loads(out.read_text(encoding="utf-8"))

    def test_no_flag_omits_perturbation_identity(self) -> None:
        self.assertNotIn("perturbation", self.normalized_run())

    def test_explicit_baseline_emits_null(self) -> None:
        trace = self.normalized_run("--no-perturbation")
        self.assertIn("perturbation", trace)
        self.assertIsNone(trace["perturbation"])
        self.assertEqual([error.message for error in self.validator.iter_errors(trace)], [])

    def test_named_perturbation_emits_the_declared_pair(self) -> None:
        for declared in load(WORKED_EXAMPLE)["perturbations"]:
            with self.subTest(perturbation=declared["id"]):
                trace = self.normalized_run(
                    "--perturbation-id", declared["id"], "--perturbation-axis", declared["axis"]
                )
                self.assertEqual(trace["perturbation"], {"id": declared["id"], "axis": declared["axis"]})
                self.assertEqual([error.message for error in self.validator.iter_errors(trace)], [])

    def assert_normalizer_refuses(self, *extra: str) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            proc, out = run_normalizer(Path(tmp), *extra)
            self.assertNotEqual(proc.returncode, 0, proc.stdout)
            self.assertFalse(out.exists(), "a refused run must not leave a trace behind")
            return proc.stderr

    def test_perturbation_id_without_axis_is_refused(self) -> None:
        self.assertIn("must be provided together", self.assert_normalizer_refuses(
            "--perturbation-id", "context-drop-metric-definition"))

    def test_perturbation_axis_without_id_is_refused(self) -> None:
        self.assertIn("must be provided together", self.assert_normalizer_refuses(
            "--perturbation-axis", "context"))

    def test_baseline_and_named_perturbation_cannot_be_claimed_at_once(self) -> None:
        self.assertIn("cannot be combined", self.assert_normalizer_refuses(
            "--no-perturbation", "--perturbation-id", "context-drop-metric-definition",
            "--perturbation-axis", "context"))

    def test_undeclarable_perturbation_id_is_refused(self) -> None:
        self.assertIn("not a declarable case id", self.assert_normalizer_refuses(
            "--perturbation-id", "Context Drop", "--perturbation-axis", "context"))

    def test_unknown_axis_is_refused_at_the_boundary(self) -> None:
        self.assertIn("invalid choice", self.assert_normalizer_refuses(
            "--perturbation-id", "context-drop-metric-definition", "--perturbation-axis", "network"))


class RunIdentityTests(unittest.TestCase):
    """run_id must move with the perturbation and stand still without one."""

    def emitted(self, *extra: str) -> tuple[str, str]:
        with tempfile.TemporaryDirectory() as tmp:
            proc, out = run_normalizer(Path(tmp), *extra)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            text = out.read_text(encoding="utf-8")
            return text, json.loads(text)["run_id"]

    def test_undisturbed_run_reproduces_the_committed_fixture_byte_for_byte(self) -> None:
        text, _ = self.emitted()
        self.assertEqual(text, COMMITTED_BASELINE.read_text(encoding="utf-8"))

    def test_explicit_baseline_shares_the_undisturbed_run_id_by_design(self) -> None:
        # Pinning the documented ceiling of appending the identity component only
        # when a perturbation is present: absent and explicit-null describe the
        # same world, so only the trace field keeps them apart, not the run_id.
        _, baseline = self.emitted()
        _, declared = self.emitted("--no-perturbation")
        self.assertEqual(declared, baseline)

    def test_committed_perturbed_fixture_reproduces(self) -> None:
        text, _ = self.emitted(
            "--perturbation-id", "context-drop-metric-definition", "--perturbation-axis", "context")
        self.assertEqual(text, COMMITTED_PERTURBED.read_text(encoding="utf-8"))

    def test_distinct_perturbations_get_distinct_run_ids(self) -> None:
        _, baseline = self.emitted()
        ids = {"none": baseline}
        for declared in load(WORKED_EXAMPLE)["perturbations"]:
            _, run_id = self.emitted(
                "--perturbation-id", declared["id"], "--perturbation-axis", declared["axis"])
            ids[declared["id"]] = run_id
        self.assertEqual(len(set(ids.values())), len(ids), f"run_id collision across perturbations: {ids}")

    def test_committed_run_identity_fixtures_satisfy_the_run_trace_schema(self) -> None:
        checker = validator(RUN_TRACE_SCHEMA)
        paths = sorted(RUN_IDENTITY_FIXTURES.glob("*.json"))
        self.assertTrue(paths, "no committed run-identity fixtures to pin the formula")
        for path in paths:
            with self.subTest(fixture=path.name):
                self.assertEqual([error.message for error in checker.iter_errors(load(path))], [])


class SchemaHealthTests(unittest.TestCase):
    def test_committed_schemas_are_valid_draft_2020_12(self) -> None:
        from jsonschema import Draft202012Validator

        for path in (CONTRACT_SCHEMA, RUN_TRACE_SCHEMA):
            Draft202012Validator.check_schema(load(path))


if __name__ == "__main__":
    unittest.main()
