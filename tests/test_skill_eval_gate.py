#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_GATE = REPO_ROOT / "scripts" / "check_skill_evals.py"


class SkillEvalGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "scripts").mkdir()
        (self.root / "evals" / "cases" / "demo").mkdir(parents=True)
        (self.root / "evals" / "fixtures").mkdir(parents=True)
        (self.root / "evals" / "verifiers").mkdir(parents=True)
        (self.root / "skills" / "demo-skill").mkdir(parents=True)
        (self.root / "skills" / "other-skill").mkdir(parents=True)
        shutil.copy2(SOURCE_GATE, self.root / "scripts" / "check_skill_evals.py")
        (self.root / "evals" / "fixtures" / "input.txt").write_text("fixture\n", encoding="utf-8")
        (self.root / "evals" / "verifiers" / "verify.py").write_text(
            "raise SystemExit(0)\n", encoding="utf-8"
        )
        (self.root / "skills" / "demo-skill" / "runtime.py").write_text(
            "# legacy_anchor exists only in a comment\n\n"
            "def live_contract() -> bool:\n"
            "    return True\n",
            encoding="utf-8",
        )
        (self.root / "skills" / "other-skill" / "runtime.py").write_text(
            "def foreign_contract() -> bool:\n    return True\n",
            encoding="utf-8",
        )
        self.write_good_case()
        self.write_good_coverage()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    @property
    def case_path(self) -> Path:
        return self.root / "evals" / "cases" / "demo" / "case-one.json"

    @property
    def coverage_path(self) -> Path:
        return self.root / "evals" / "coverage.json"

    def write_good_case(self) -> None:
        case = {
            "schema_version": "skill-eval/v1",
            "id": "case-one",
            "skill": "demo-skill",
            "kind": "capability",
            "split": "dev",
            "claims": ["does-real-work"],
            "task": {
                "prompt": "Complete the realistic task and write evidence.",
                "fixture": "evals/fixtures/input.txt",
            },
            "conditions": ["no_skill", "candidate_skill"],
            "verifier": {
                "type": "script",
                "command": "python3 evals/verifiers/verify.py",
                "outcome_assertions": ["artifact is correct"],
            },
        }
        self.case_path.write_text(json.dumps(case), encoding="utf-8")

    def write_good_coverage(self) -> None:
        coverage = {
            "schema_version": "skill-eval-coverage/v1",
            "claims": {
                "demo-skill:does-real-work": {"cases": ["case-one"]}
            },
        }
        self.coverage_path.write_text(json.dumps(coverage), encoding="utf-8")

    def make_real_incident(self, *, path="skills/demo-skill/runtime.py", anchor="def live_contract(") -> None:
        self.mutate_case(
            lambda case: case.update(
                {
                    "source": {"kind": "github_issue", "ref": "demo/repo#1"},
                    "implementation_targets": [{"path": path, "anchor": anchor}],
                }
            )
        )

    def run_gate(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(self.root / "scripts" / "check_skill_evals.py")],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )

    def mutate_case(self, fn) -> None:
        value = json.loads(self.case_path.read_text(encoding="utf-8"))
        fn(value)
        self.case_path.write_text(json.dumps(value), encoding="utf-8")

    def mutate_coverage(self, fn) -> None:
        value = json.loads(self.coverage_path.read_text(encoding="utf-8"))
        fn(value)
        self.coverage_path.write_text(json.dumps(value), encoding="utf-8")

    def declare_perturbations(self, *entries: dict) -> None:
        declared = list(entries) or [
            {
                "id": "context-drop-spec",
                "axis": "context",
                "description": "Remove the written spec from the working context.",
                "expected_effect": "The gap is surfaced instead of guessed at.",
            }
        ]
        self.mutate_case(lambda case: case.update({"perturbations": declared}))

    def write_run_trace(self, perturbation, *, case_id="case-one", name="run.json") -> None:
        """Write a run trace the gate must resolve; `...` means omit the key."""
        trace = {
            "schema_version": "skill-eval-run/v1",
            "run_id": "aaaaaaaabbbbbbbbcccccccc",
            "case_id": case_id,
        }
        if perturbation is not Ellipsis:
            trace["perturbation"] = perturbation
        path = self.root / "evals" / "runs" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(trace), encoding="utf-8")

    def test_good_fixture_passes(self) -> None:
        result = self.run_gate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS skill eval coverage", result.stdout)

    def test_real_incident_with_live_target_passes(self) -> None:
        self.make_real_incident()
        result = self.run_gate()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_real_incident_requires_implementation_targets(self) -> None:
        self.mutate_case(
            lambda case: case.update(
                {"source": {"kind": "github_issue", "ref": "demo/repo#1"}}
            )
        )
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires implementation_targets", result.stderr)

    def test_missing_implementation_target_fails(self) -> None:
        self.make_real_incident(path="skills/demo-skill/missing.py")
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stale implementation target does not exist", result.stderr)

    def test_implementation_target_escape_fails(self) -> None:
        self.make_real_incident(path="../outside.py")
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("escapes repository", result.stderr)

    def test_wrong_skill_target_fails(self) -> None:
        self.make_real_incident(
            path="skills/other-skill/runtime.py", anchor="def foreign_contract("
        )
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must stay under skills/demo-skill/", result.stderr)

    def test_comment_only_anchor_fails(self) -> None:
        self.make_real_incident(anchor="legacy_anchor")
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not found on a non-comment line", result.stderr)

    def test_trivial_anchor_fails(self) -> None:
        self.make_real_incident(anchor="###")
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("anchor must be a meaningful token", result.stderr)

    def test_duplicate_implementation_target_fails(self) -> None:
        self.make_real_incident()
        self.mutate_case(
            lambda case: case["implementation_targets"].append(
                dict(case["implementation_targets"][0])
            )
        )
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate implementation target", result.stderr)

    def test_empty_runnable_set_fails(self) -> None:
        self.case_path.unlink()
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no runnable eval cases", result.stderr)

    def test_missing_verifier_fails(self) -> None:
        self.mutate_case(lambda case: case.pop("verifier"))
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("verifier must be an object", result.stderr)

    def test_fabricated_claim_link_fails(self) -> None:
        self.mutate_coverage(
            lambda coverage: coverage["claims"].update(
                {"demo-skill:not-actually-in-case": {"cases": ["case-one"]}}
            )
        )
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fabricated coverage", result.stderr)

    def test_missing_case_reference_fails(self) -> None:
        self.mutate_coverage(
            lambda coverage: coverage["claims"]["demo-skill:does-real-work"].update(
                {"cases": ["does-not-exist"]}
            )
        )
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("references missing case", result.stderr)

    def test_unregistered_claim_fails(self) -> None:
        self.mutate_case(lambda case: case["claims"].append("second-claim"))
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("has no coverage registry entry", result.stderr)

    def test_missing_fixture_fails(self) -> None:
        self.mutate_case(lambda case: case["task"].update({"fixture": "missing.txt"}))
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("task.fixture does not exist", result.stderr)

    def test_bound_perturbation_passes(self) -> None:
        self.declare_perturbations()
        self.write_run_trace({"id": "context-drop-spec", "axis": "context"})
        result = self.run_gate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1 bound run-trace perturbations", result.stdout)

    def test_duplicate_perturbation_id_fails(self) -> None:
        self.declare_perturbations(
            {
                "id": "context-drop-spec",
                "axis": "context",
                "description": "Remove the written spec from the working context.",
                "expected_effect": "The gap is surfaced instead of guessed at.",
            },
            {
                "id": "context-drop-spec",
                "axis": "tool",
                "description": "A second disturbance reusing the first identifier.",
                "expected_effect": "Nothing can say which of the two a run applied.",
            },
        )
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate perturbation id", result.stderr)

    def test_run_trace_perturbation_must_resolve_to_a_declared_one(self) -> None:
        self.declare_perturbations()
        self.write_run_trace({"id": "never-declared-anywhere", "axis": "context"})
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not declare", result.stderr)

    def test_run_trace_perturbation_axis_must_match_the_declaration(self) -> None:
        self.declare_perturbations()
        self.write_run_trace({"id": "context-drop-spec", "axis": "tool"})
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("declares axis 'context'", result.stderr)

    def test_run_trace_bound_to_unknown_case_fails(self) -> None:
        self.declare_perturbations()
        self.write_run_trace({"id": "context-drop-spec", "axis": "context"}, case_id="case-nine")
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("binds to unknown case", result.stderr)

    def test_perturbation_claimed_against_a_case_that_declares_none_fails(self) -> None:
        self.write_run_trace({"id": "context-drop-spec", "axis": "context"})
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not declare", result.stderr)

    def test_absent_and_null_perturbation_states_stay_green(self) -> None:
        self.declare_perturbations()
        self.write_run_trace(Ellipsis, name="absent.json")
        self.write_run_trace(None, name="baseline.json")
        result = self.run_gate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("0 bound run-trace perturbations", result.stdout)

    def test_unparsable_run_trace_candidate_fails(self) -> None:
        (self.root / "evals" / "runs").mkdir(parents=True, exist_ok=True)
        (self.root / "evals" / "runs" / "broken.json").write_text("{not json", encoding="utf-8")
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid JSON", result.stderr)

    def test_agent_judge_alone_fails_hard_gate(self) -> None:
        self.mutate_case(
            lambda case: case["verifier"].update({"type": "agent_judge"})
        )
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("agent_judge cannot be the sole verifier", result.stderr)


if __name__ == "__main__":
    unittest.main()
