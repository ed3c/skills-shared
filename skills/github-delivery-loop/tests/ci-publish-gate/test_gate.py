from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "ci_publish_gate.py"
SPEC = importlib.util.spec_from_file_location("ci_publish_gate", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


LOCAL = "a" * 40
REMOTE = "b" * 40


def snapshot(intent: str = "ready-for-review") -> dict:
    return {
        "schema": "github-ci-publish-snapshot/v1",
        "repository": "ed3c/skills-shared",
        "repository_owner": "ed3c",
        "private": True,
        "intent": intent,
        "local_head": LOCAL,
        "local_verification": {
            "head_sha": LOCAL,
            "status": "passed",
            "completed_at": "2026-08-12T05:10:00Z",
        },
        "pull_request": {
            "number": 42,
            "is_draft": True,
            "remote_head": REMOTE,
        },
        "actionable_feedback": None,
        "billing_blocker": None,
        "recovery": None,
    }


class CiPublishGateTests(unittest.TestCase):
    def test_malformed_intent_fails_closed_without_type_error(self) -> None:
        value = snapshot()
        value["intent"] = ["ready-for-review"]

        with self.assertRaisesRegex(MODULE.SnapshotError, "intent must be a string"):
            MODULE.evaluate(value)

    def test_initial_draft_pr_is_a_deliberate_publication(self) -> None:
        value = snapshot("initial-pr")
        value["pull_request"] = None

        self.assertEqual(MODULE.evaluate(value), (True, "initial-pr"))

    def test_ready_for_review_requires_a_draft_with_new_head(self) -> None:
        value = snapshot()
        self.assertEqual(MODULE.evaluate(value), (True, "ready-for-review"))

        value["pull_request"]["is_draft"] = False
        self.assertEqual(MODULE.evaluate(value), (False, "pull-request-already-ready"))

    def test_local_verification_must_pin_the_exact_head(self) -> None:
        value = snapshot()
        value["local_verification"]["head_sha"] = REMOTE

        self.assertEqual(MODULE.evaluate(value), (False, "verification-head-mismatch"))

    def test_current_remote_head_is_not_pushed_again(self) -> None:
        value = snapshot()
        value["pull_request"]["remote_head"] = LOCAL

        self.assertEqual(MODULE.evaluate(value), (False, "remote-head-already-current"))

    def test_repair_requires_actionable_feedback_for_remote_head(self) -> None:
        value = snapshot("repair")
        value["pull_request"]["is_draft"] = False
        value["actionable_feedback"] = {
            "actionable": True,
            "head_sha": REMOTE,
            "observed_at": "2026-08-12T05:05:00Z",
        }

        self.assertEqual(MODULE.evaluate(value), (True, "repair"))

        value["actionable_feedback"]["head_sha"] = "c" * 40
        self.assertEqual(MODULE.evaluate(value), (False, "feedback-head-mismatch"))

    def test_one_feedback_batch_cannot_be_published_twice(self) -> None:
        value = snapshot("repair")
        value["pull_request"]["is_draft"] = False
        value["actionable_feedback"] = {
            "actionable": True,
            "head_sha": REMOTE,
            "observed_at": "2026-08-12T05:05:00Z",
        }
        value["last_publication"] = {
            "intent": "repair",
            "feedback_observed_at": "2026-08-12T05:05:00Z",
        }

        self.assertEqual(MODULE.evaluate(value), (False, "feedback-already-published"))

    def test_billing_recovery_must_be_owner_authored_and_later(self) -> None:
        value = snapshot()
        value["billing_blocker"] = {
            "kind": "account-billing-no-runner",
            "observed_at": "2026-08-12T05:00:00Z",
        }
        value["recovery"] = {
            "author": "someone-else",
            "status": "actions-restored",
            "recovered_at": "2026-08-12T05:20:00Z",
        }
        self.assertEqual(MODULE.evaluate(value), (False, "billing-recovery-untrusted"))

        value["recovery"]["author"] = "ed3c"
        value["recovery"]["recovered_at"] = "2026-08-12T04:59:59Z"
        self.assertEqual(MODULE.evaluate(value), (False, "billing-recovery-stale"))

        value["recovery"]["recovered_at"] = "2026-08-12T05:20:00Z"
        self.assertEqual(MODULE.evaluate(value), (True, "ready-for-review"))


if __name__ == "__main__":
    unittest.main()
