from __future__ import annotations

import unittest

from scripts.check_capability_unlocks import validate_unlock


class CapabilityUnlockTests(unittest.TestCase):
    def good(self):
        return {
            "schema_version": "capability-unlock/v1",
            "id": "unlock-example",
            "skill": "example-skill",
            "skill_sha": "abcdef0123456789",
            "case_ids": [f"holdout-{i}" for i in range(6)],
            "baseline": {"no_skill_passes": 1, "current_skill_passes": 1, "total": 6},
            "candidate": {"passes": 4, "total": 6},
            "supported_stacks": [
                {"model": "model-a", "harness": "codex"},
                {"model": "model-b", "harness": "claude-code"}
            ],
            "evidence_bundles": ["evidence/run-a.json", "evidence/run-b.json"]
        }

    def test_good_unlock_passes(self):
        validate_unlock(self.good())

    def test_baseline_must_mostly_fail(self):
        value = self.good(); value["baseline"]["no_skill_passes"] = 2
        with self.assertRaisesRegex(ValueError, "baseline"):
            validate_unlock(value)

    def test_candidate_must_unlock_at_least_two_thirds(self):
        value = self.good(); value["candidate"]["passes"] = 3
        with self.assertRaisesRegex(ValueError, "candidate"):
            validate_unlock(value)

    def test_requires_two_distinct_stacks(self):
        value = self.good(); value["supported_stacks"][1] = dict(value["supported_stacks"][0])
        with self.assertRaisesRegex(ValueError, "two distinct"):
            validate_unlock(value)


if __name__ == "__main__":
    unittest.main()
