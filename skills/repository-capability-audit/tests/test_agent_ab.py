from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_CELL = ROOT / "scripts" / "run_agent_cell.py"
SCORE = ROOT / "scripts" / "score_agent_ab.py"


class AgentEffectivenessHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.receipts = self.root / "receipts"
        self.receipts.mkdir()
        self.task = self.root / "task.md"
        self.task.write_text(
            "Audit the exact repository capability claim.\n",
            encoding="utf-8",
        )
        self.evaluator_contract = self.root / "evaluator.json"
        self.evaluator_contract.write_text(
            json.dumps(
                {
                    "schema": "fixture-evaluator/v1",
                    "owner": "independent",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        self.agent_script = self.root / "fixture_agent.py"
        self.agent_script.write_text(
            """from __future__ import annotations
import json, os
from pathlib import Path
workspace = Path(os.environ['RCA_EVAL_WORKSPACE'])
if 'RCA_TEST_API_KEY' in os.environ:
    raise SystemExit('ambient secret leaked')
(workspace / '.hidden').mkdir(exist_ok=True)
(workspace / '.hidden' / 'runtime-evidence.json').write_text(json.dumps({'profile': os.environ['RCA_EVAL_PROFILE']}) + '\\n')
(workspace / 'agent-output.json').write_text(json.dumps({'profile': os.environ['RCA_EVAL_PROFILE'], 'case': os.environ['RCA_EVAL_CASE_ID']}) + '\\n')
""",
            encoding="utf-8",
        )
        self.evaluator_script = self.root / "fixture_evaluator.py"
        self.evaluator_script.write_text(
            """from __future__ import annotations
import json, os
from pathlib import Path
profile = os.environ['RCA_EVAL_PROFILE']
metrics_file = Path(os.environ['RCA_EVAL_METRICS_FILE'])
good = profile != 'no_skill'
metrics = {
  'task_success': good,
  'material_defects_found': 2 if good else 0,
  'material_defects_total': 2,
  'false_pass_count': 0 if good else 1,
  'false_pass_opportunities': 1,
  'evidence_packet_complete': good,
  'exact_subject_continuity': good,
  'negative_control_valid': good,
  'explicit_non_claim_accuracy': good,
  'trigger_correct': True,
  'tool_calls': 4,
  'input_tokens': 100,
  'output_tokens': 40,
  'duration_ms': 10,
  'cost_usd': 0.0,
}
metrics_file.write_text(json.dumps(metrics, sort_keys=True) + '\\n')
""",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cell(
        self,
        profile: str,
        treatment_text: str,
        *,
        evaluator_owner: str = "independent",
    ) -> Path:
        treatment = self.root / f"{profile}.md"
        treatment.write_text(treatment_text, encoding="utf-8")
        workspace = self.root / f"workspace-{profile}"
        output = self.receipts / f"{profile}.json"
        command = [
            sys.executable,
            str(RUN_CELL),
            "--profile",
            profile,
            "--case-id",
            "fixture-case",
            "--repository-id",
            "fixture/repository",
            "--commit",
            "a" * 40,
            "--tree",
            "b" * 40,
            "--repetition",
            "1",
            "--arm-order",
            "0",
            "--task-file",
            str(self.task),
            "--treatment-file",
            str(treatment),
            "--evaluator-file",
            str(self.evaluator_contract),
            "--agent-command-json",
            json.dumps([sys.executable, str(self.agent_script)]),
            "--evaluator-command-json",
            json.dumps([sys.executable, str(self.evaluator_script)]),
            "--agent-class",
            "deterministic_fixture",
            "--agent-provider",
            "fixture",
            "--agent-family",
            "fixture",
            "--agent-model",
            "fixture",
            "--agent-version",
            "1",
            "--agent-harness",
            "fixture-harness",
            "--agent-harness-version",
            "1",
            "--runtime-identity",
            "local-subprocess",
            "--runtime-version",
            "1",
            "--toolset-digest",
            "c" * 64,
            "--evaluator-identity",
            "fixture-evaluator",
            "--evaluator-version",
            "1",
            "--evaluator-owner",
            evaluator_owner,
            "--workspace",
            str(workspace),
            "--output",
            str(output),
        ]
        env = {
            **os.environ,
            "RCA_TEST_API_KEY": "must-not-cross",
        }
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        self.assertEqual(
            process.returncode,
            0,
            process.stderr + process.stdout,
        )
        return output

    def score(self) -> tuple[subprocess.CompletedProcess[str], dict]:
        output = self.root / "report.json"
        process = subprocess.run(
            [
                sys.executable,
                str(SCORE),
                "--receipts",
                str(self.receipts),
                "--output",
                str(output),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        return process, json.loads(output.read_text(encoding="utf-8"))

    def test_empty_receipt_set_is_not_exercised(self):
        process, report = self.score()
        self.assertEqual(process.returncode, 0)
        self.assertEqual(report["admission_state"], "NOT_EXERCISED")
        self.assertEqual(report["live_receipts"], 0)

    def test_fixture_agent_validates_harness_but_never_prompt_effectiveness(self):
        self.run_cell("no_skill", "")
        self.run_cell(
            "current_full_composition",
            "full procedure",
        )
        self.run_cell(
            "candidate_trimmed_skill",
            "trimmed procedure",
        )
        process, report = self.score()
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(
            report["admission_state"],
            "HARNESS_SELFTEST_ONLY",
        )
        self.assertEqual(report["fixture_receipts"], 3)
        self.assertEqual(report["live_receipts"], 0)
        receipt = json.loads(
            (
                self.receipts / "candidate_trimmed_skill.json"
            ).read_text()
        )
        paths = {item["path"] for item in receipt["artifacts"]}
        self.assertIn(".hidden/runtime-evidence.json", paths)
        self.assertIn(
            "RCA_TEST_API_KEY",
            receipt["removed_ambient_environment_names"],
        )

    def test_tampered_receipt_is_invalid_experiment(self):
        path = self.run_cell(
            "candidate_trimmed_skill",
            "trimmed procedure",
        )
        receipt = json.loads(path.read_text(encoding="utf-8"))
        receipt["metrics"]["task_success"] = False
        path.write_text(
            json.dumps(receipt, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        process, report = self.score()
        self.assertEqual(process.returncode, 2)
        self.assertEqual(
            report["admission_state"],
            "INVALID_EXPERIMENT",
        )
        self.assertTrue(
            any(
                "digest mismatch" in item
                for item in report["validation_failures"]
            )
        )

    def test_producer_owned_evaluator_is_invalid_experiment(self):
        self.run_cell(
            "candidate_trimmed_skill",
            "trimmed procedure",
            evaluator_owner="producer",
        )
        process, report = self.score()
        self.assertEqual(process.returncode, 2)
        self.assertEqual(
            report["admission_state"],
            "INVALID_EXPERIMENT",
        )
        self.assertTrue(
            any(
                "independently owned" in item
                for item in report["validation_failures"]
            )
        )


if __name__ == "__main__":
    unittest.main()
