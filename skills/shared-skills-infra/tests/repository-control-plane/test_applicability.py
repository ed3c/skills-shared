from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = SKILL_ROOT / "scripts"
PROFILE = SKILL_ROOT / "references" / "repository-control-plane.default.json"
sys.path.insert(0, str(SCRIPTS))

from repository_control_plane_monitor import build_monitor_plan  # noqa: E402


class RepositoryControlPlaneApplicabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = json.loads(PROFILE.read_text(encoding="utf-8"))
        self.control = {
            "schema": "repository-control-plane/consumer-binding/v1",
            "consumer_repository_id": "ed3c/example",
            "profile": {"id": "skills-shared-default", "content_sha256": "a" * 64},
            "authority": {
                "consumer_mutation": "CONSUMER_POLICY_REQUIRED",
                "host_install": "HOST_POLICY_REQUIRED",
                "automatic_merge": False,
                "automatic_conflict_resolution": False,
                "visibility_change": False,
                "skill_body_copy": False,
                "secret_values": "DENY",
            },
        }

    def test_default_issue_does_not_manufacture_stack_or_forge(self) -> None:
        plan = build_monitor_plan(
            self.profile,
            control=self.control,
            snapshot=[{"number": 1, "title": "docs only", "state": "open"}],
        )
        issue = plan["issues"][0]
        self.assertEqual(
            issue["required_receipts"],
            ["skill-resolution", "shadow-admission", "task-dag"],
        )
        self.assertEqual(issue["phase_dispositions"]["SPATIAL_INVARIANTS"], "MONITOR")
        self.assertEqual(
            issue["phase_dispositions"]["STACK_DELIVERY"],
            "NOT_APPLICABLE_WITH_EVIDENCE",
        )
        self.assertEqual(
            issue["phase_dispositions"]["FORGE_RECONCILIATION"],
            "NOT_APPLICABLE_WITH_EVIDENCE",
        )

    def test_explicit_stack_and_forge_requirement_promotes_only_named_phases(self) -> None:
        plan = build_monitor_plan(
            self.profile,
            control=self.control,
            snapshot=[
                {
                    "number": 2,
                    "title": "real delivery",
                    "state": "open",
                    "required_phases": ["STACK_DELIVERY", "FORGE_RECONCILIATION"],
                }
            ],
        )
        issue = plan["issues"][0]
        self.assertEqual(issue["phase_dispositions"]["SPATIAL_INVARIANTS"], "MONITOR")
        self.assertEqual(issue["phase_dispositions"]["STACK_DELIVERY"], "REQUIRED")
        self.assertEqual(issue["phase_dispositions"]["FORGE_RECONCILIATION"], "REQUIRED")
        self.assertEqual(
            issue["required_receipts"],
            [
                "skill-resolution",
                "shadow-admission",
                "task-dag",
                "git-town-stack",
                "dual-forge-reconciliation",
            ],
        )

    def test_explicit_spatial_requirement_promotes_monitor_to_required(self) -> None:
        plan = build_monitor_plan(
            self.profile,
            control=self.control,
            snapshot=[
                {
                    "number": 3,
                    "title": "hard invariant change",
                    "state": "open",
                    "required_phases": ["SPATIAL_INVARIANTS"],
                }
            ],
        )
        issue = plan["issues"][0]
        self.assertEqual(issue["phase_dispositions"]["SPATIAL_INVARIANTS"], "REQUIRED")
        self.assertIn("spatial-invariants", issue["required_receipts"])
        self.assertNotIn("git-town-stack", issue["required_receipts"])
        self.assertNotIn("dual-forge-reconciliation", issue["required_receipts"])

    def test_unknown_required_phase_fails_closed(self) -> None:
        with self.assertRaisesRegex(Exception, "unknown required phase"):
            build_monitor_plan(
                self.profile,
                control=self.control,
                snapshot=[
                    {
                        "number": 4,
                        "title": "bad hint",
                        "state": "open",
                        "required_phases": ["MAGIC_SHIP"],
                    }
                ],
            )


if __name__ == "__main__":
    unittest.main()
