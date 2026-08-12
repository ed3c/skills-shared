from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "skill-eval-physical-skill-up.yml"


class SkillEvalCostTierContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_manual_only(self) -> None:
        trigger_block = self.text.split("permissions:", 1)[0]
        self.assertIn("workflow_dispatch:", trigger_block)
        for forbidden in ("pull_request:", "push:", "schedule:", "workflow_run:"):
            self.assertNotIn(forbidden, trigger_block)

    def test_smoke_and_promotion_inputs_are_explicit(self) -> None:
        self.assertIn("evidence_tier:", self.text)
        self.assertIn("promotion_confirmation:", self.text)
        self.assertIn("RUN_PROMOTION_6_JOBS", self.text)
        self.assertRegex(
            self.text,
            re.compile(r"repetition:\s*\$\{\{\s*fromJSON\(inputs\.evidence_tier == 'promotion' && '\[1,2,3\]' \|\| '\[1\]'\)\s*\}\}"),
        )

    def test_smoke_is_non_promotable(self) -> None:
        self.assertIn("Remove promotion bundle from smoke runs", self.text)
        self.assertIn('rm -f "$attempt/evidence-bundle.json"', self.text)
        self.assertIn("'promotion_eligible':os.environ['EVIDENCE_TIER'] == 'promotion'", self.text)
        self.assertIn("test ! -e \"$attempt/evidence-bundle.json\"", self.text)

    def test_promotion_preserves_three_repetitions(self) -> None:
        self.assertIn("expected_repetitions':3 if", self.text)
        self.assertIn("test -f \"$attempt/evidence-bundle.json\"", self.text)

    def test_cost_and_secret_boundaries(self) -> None:
        self.assertIn("cancel-in-progress: true", self.text)
        self.assertIn("persist-credentials: false", self.text)
        self.assertIn("retention-days: ${{ inputs.evidence_tier == 'promotion' && 14 || 3 }}", self.text)
        self.assertIn("api-key: ${{ secrets.SKILL_EVAL_API_KEY }}", self.text)
        self.assertNotIn("SKILL_EVAL_API_KEY:", self.text)
        self.assertIn("max_retries':0", self.text)

    def test_mutation_controls_turn_red(self) -> None:
        mutations = {
            "automatic-trigger": self.text.replace("workflow_dispatch:", "pull_request:", 1),
            "promotion-default": self.text.replace("default: smoke", "default: promotion", 1),
            "single-promotion-repetition": self.text.replace("'[1,2,3]'", "'[1]'", 1),
            "smoke-promotable": self.text.replace(
                "'promotion_eligible':os.environ['EVIDENCE_TIER'] == 'promotion'",
                "'promotion_eligible':True",
                1,
            ),
            "keep-smoke-bundle": self.text.replace(
                'rm -f "$attempt/evidence-bundle.json"', ": # mutation", 1
            ),
        }
        for name, value in mutations.items():
            with self.subTest(name=name):
                if name == "automatic-trigger":
                    self.assertIn("pull_request:", value.split("permissions:", 1)[0])
                elif name == "promotion-default":
                    self.assertNotIn("default: smoke", value)
                elif name == "single-promotion-repetition":
                    self.assertNotIn("'[1,2,3]'", value)
                elif name == "smoke-promotable":
                    self.assertNotIn(
                        "'promotion_eligible':os.environ['EVIDENCE_TIER'] == 'promotion'",
                        value,
                    )
                else:
                    self.assertNotIn('rm -f "$attempt/evidence-bundle.json"', value)


if __name__ == "__main__":
    unittest.main()
