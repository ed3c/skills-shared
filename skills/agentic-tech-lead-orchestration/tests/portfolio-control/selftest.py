#!/usr/bin/env python3
"""Mutation controls for repository portfolio prompt and contract foundation."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = SKILL_ROOT / "scripts"
REFS = SKILL_ROOT / "references" / "repository-portfolio-control"
EXAMPLES = REFS / "examples"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from repository_portfolio_common import digest_object, load_json  # noqa: E402
import assert_issue_pr_acceptance as acceptance_gate  # noqa: E402
import assert_one_shot_ci_epoch as ci_gate  # noqa: E402
import assert_portfolio_multigraph as graph_gate  # noqa: E402
import assert_repository_portfolio_snapshot as snapshot_gate  # noqa: E402
import assert_subagent_join as join_gate  # noqa: E402
import check_repository_portfolio_prompt_pack as prompt_gate  # noqa: E402


class PortfolioControlTests(unittest.TestCase):
    def load(self, name: str):
        return load_json(EXAMPLES / name)

    def test_positive_denominator(self) -> None:
        self.assertEqual(prompt_gate.validate(load_json(REFS / "prompt-manifest.json")), [])
        self.assertEqual(snapshot_gate.validate(self.load("good-snapshot.json"), 300), [])
        errors, state = acceptance_gate.validate(self.load("good-acceptance.json"))
        self.assertEqual(errors, [])
        self.assertEqual(state, "READY")
        self.assertEqual(graph_gate.validate(self.load("good-multigraph.json")), [])
        errors, state = join_gate.validate(
            self.load("good-join-receipt.json"),
            self.load("good-dispatches.json"),
        )
        self.assertEqual(errors, [])
        self.assertEqual(state, "PASS")
        errors, verdict = ci_gate.validate(self.load("good-ci-epoch.json"))
        self.assertEqual(errors, [])
        self.assertEqual(verdict, "PASS")

    def test_prompt_digest_drift(self) -> None:
        candidate = copy.deepcopy(load_json(REFS / "prompt-manifest.json"))
        candidate["prompts"][0]["sha256"] = "0" * 64
        candidate["manifest_digest"] = digest_object(candidate, "manifest_digest")
        errors = prompt_gate.validate(candidate)
        self.assertTrue(any("prompt digest drift" in error for error in errors))

    def test_mixed_snapshot_epoch(self) -> None:
        candidate = self.load("good-snapshot.json")
        candidate["repositories"][0]["issues_observed_at"] = "2026-08-21T13:50:00Z"
        candidate["epoch_digest"] = digest_object(candidate, "epoch_digest")
        errors = snapshot_gate.validate(candidate, 300)
        self.assertIn("MIXED_SNAPSHOT_EPOCH: observation skew exceeds bound", errors)

    def test_duplicate_repository_subject(self) -> None:
        candidate = self.load("good-snapshot.json")
        candidate["repositories"].append(copy.deepcopy(candidate["repositories"][0]))
        candidate["epoch_digest"] = digest_object(candidate, "epoch_digest")
        errors = snapshot_gate.validate(candidate, 300)
        self.assertTrue(any("duplicate repository subject" in error for error in errors))

    def test_issue_without_frozen_acceptance(self) -> None:
        candidate = self.load("good-acceptance.json")
        candidate["oracles"] = []
        candidate["contract_digest"] = digest_object(candidate, "contract_digest")
        errors, state = acceptance_gate.validate(candidate)
        self.assertIn("ISSUE_WITHOUT_FROZEN_ACCEPTANCE", errors)
        self.assertEqual(state, "BLOCKED_BY_MISSING_ACCEPTANCE")

    def test_runtime_available_is_not_exercised(self) -> None:
        candidate = self.load("good-acceptance.json")
        candidate["runtime_requirements"][0]["state"] = "NOT_EXERCISED"
        candidate["contract_digest"] = digest_object(candidate, "contract_digest")
        errors, state = acceptance_gate.validate(candidate)
        self.assertEqual(errors, [])
        self.assertEqual(state, "READY")

    def test_absent_runtime_blocks(self) -> None:
        candidate = self.load("good-acceptance.json")
        candidate["runtime_requirements"][0]["state"] = "ABSENT"
        candidate["contract_digest"] = digest_object(candidate, "contract_digest")
        errors, state = acceptance_gate.validate(candidate)
        self.assertEqual(errors, [])
        self.assertEqual(state, "BLOCKED_BY_RUNTIME")

    def test_acceptance_lease_overlap(self) -> None:
        candidate = self.load("good-acceptance.json")
        candidate["leases"]["read_only_paths"] = [
            "skills/agentic-tech-lead-orchestration/references/repository-portfolio-control/contracts/**"
        ]
        candidate["contract_digest"] = digest_object(candidate, "contract_digest")
        errors, _ = acceptance_gate.validate(candidate)
        self.assertTrue(any("exclusive path overlaps" in error for error in errors))

    def test_overlapping_writers_cannot_share_wave(self) -> None:
        candidate = self.load("good-multigraph.json")
        candidate["nodes"][1]["exclusive_paths"] = ["path/a/contracts/**"]
        candidate["digest"] = digest_object(candidate, "digest")
        errors = graph_gate.validate(candidate)
        self.assertIn("OVERLAPPING_WRITERS_FALSELY_PARALLELIZED", errors)

    def test_path_disjoint_work_not_serialized_as_conflict(self) -> None:
        candidate = self.load("good-multigraph.json")
        candidate["graphs"][3]["edges"] = [
            {"source": "A", "target": "B", "kind": "PATH_CONFLICT", "reason": "invented conflict"}
        ]
        candidate["ready_waves"] = [["A"], ["B"]]
        candidate["digest"] = digest_object(candidate, "digest")
        errors = graph_gate.validate(candidate)
        self.assertIn("PATH_DISJOINT_WORK_FALSELY_SERIALIZED", errors)

    def test_true_child_requires_consumed_parent_bytes(self) -> None:
        candidate = self.load("good-multigraph.json")
        candidate["graphs"][2]["edges"] = [
            {"source": "A", "target": "B", "kind": "TRUE_CHILD", "reason": "prose-only"}
        ]
        candidate["ready_waves"] = [["A"], ["B"]]
        candidate["digest"] = digest_object(candidate, "digest")
        errors = graph_gate.validate(candidate)
        self.assertIn("TRUE_CHILD_WITHOUT_CONSUMED_PARENT_BYTES", errors)

    def test_join_incomplete_is_not_pass(self) -> None:
        receipt = self.load("good-join-receipt.json")
        receipt["results"] = receipt["results"][:-1]
        receipt["missing_attempts"] = ["attempt-3"]
        receipt["denominator"] = {"requested": 3, "terminal": 2, "pass": 2, "non_pass": 0}
        receipt["join_state"] = "JOIN_INCOMPLETE"
        receipt["join_digest"] = digest_object(receipt, "join_digest")
        errors, state = join_gate.validate(receipt)
        self.assertEqual(errors, [])
        self.assertEqual(state, "JOIN_INCOMPLETE")

    def test_missing_agent_cannot_be_dropped(self) -> None:
        receipt = self.load("good-join-receipt.json")
        receipt["results"] = receipt["results"][:-1]
        receipt["missing_attempts"] = []
        receipt["denominator"] = {"requested": 3, "terminal": 2, "pass": 2, "non_pass": 0}
        receipt["join_state"] = "PASS"
        receipt["join_digest"] = digest_object(receipt, "join_digest")
        errors, _ = join_gate.validate(receipt)
        self.assertTrue(any("missing_attempts denominator drifted" in error for error in errors))
        self.assertTrue(any("join_state drifted" in error for error in errors))

    def test_failed_agent_remains_in_denominator(self) -> None:
        receipt = self.load("good-join-receipt.json")
        receipt["results"][1]["state"] = "FAIL"
        receipt["results"][1]["result_digest"] = digest_object(
            receipt["results"][1], "result_digest"
        )
        receipt["denominator"] = {"requested": 3, "terminal": 3, "pass": 2, "non_pass": 1}
        receipt["join_state"] = "JOIN_COMPLETE_WITH_BLOCKERS"
        receipt["join_digest"] = digest_object(receipt, "join_digest")
        errors, state = join_gate.validate(receipt)
        self.assertEqual(errors, [])
        self.assertEqual(state, "JOIN_COMPLETE_WITH_BLOCKERS")

    def test_read_only_agent_cannot_write(self) -> None:
        receipt = self.load("good-join-receipt.json")
        receipt["results"][0]["changed_paths"] = ["README.md"]
        receipt["results"][0]["result_digest"] = digest_object(
            receipt["results"][0], "result_digest"
        )
        receipt["join_digest"] = digest_object(receipt, "join_digest")
        errors, _ = join_gate.validate(receipt)
        self.assertTrue(any("read-only role changed paths" in error for error in errors))

    def test_model_alias_is_not_exact_identity(self) -> None:
        dispatches = self.load("good-dispatches.json")
        dispatches[0]["agent"]["model"] = "FABLE_5"
        dispatches[0]["dispatch_digest"] = digest_object(
            dispatches[0], "dispatch_digest"
        )
        receipt = self.load("good-join-receipt.json")
        receipt["results"][0]["dispatch_digest"] = dispatches[0]["dispatch_digest"]
        receipt["results"][0]["result_digest"] = digest_object(
            receipt["results"][0], "result_digest"
        )
        receipt["join_digest"] = digest_object(receipt, "join_digest")
        errors, _ = join_gate.validate(receipt, dispatches)
        self.assertTrue(
            any("MODEL_ALIAS_REPORTED_AS_EXACT_IDENTITY" in error for error in errors)
        )

    def test_private_dispatch_requires_egress_admission(self) -> None:
        dispatches = self.load("good-dispatches.json")
        dispatches[0]["subject"]["visibility"] = "PRIVATE"
        dispatches[0]["agent"]["data_boundary"] = "PUBLIC_ONLY"
        dispatches[0]["agent"]["private_egress_admitted"] = False
        dispatches[0]["dispatch_digest"] = digest_object(
            dispatches[0], "dispatch_digest"
        )
        receipt = self.load("good-join-receipt.json")
        receipt["results"][0]["subject"]["visibility"] = "PRIVATE"
        receipt["results"][0]["dispatch_digest"] = dispatches[0]["dispatch_digest"]
        receipt["results"][0]["result_digest"] = digest_object(
            receipt["results"][0], "result_digest"
        )
        receipt["join_digest"] = digest_object(receipt, "join_digest")
        errors, _ = join_gate.validate(receipt, dispatches)
        self.assertTrue(
            any("PRIVATE_REPO_DISPATCH_WITHOUT_EGRESS_ADMISSION" in error for error in errors)
        )

    def test_one_shot_rejects_multiple_pushes(self) -> None:
        candidate = self.load("good-ci-epoch.json")
        candidate["publication"]["code_push_count"] = 2
        candidate["verdict"] = "REJECT"
        candidate["digest"] = digest_object(candidate, "digest")
        errors, verdict = ci_gate.validate(candidate)
        self.assertIn("one final code push is required", errors)
        self.assertEqual(verdict, "REJECT")

    def test_one_shot_rejects_old_head(self) -> None:
        candidate = self.load("good-ci-epoch.json")
        candidate["workflow_runs"][0]["head_sha"] = "9" * 40
        candidate["verdict"] = "REJECT"
        candidate["digest"] = digest_object(candidate, "digest")
        errors, _ = ci_gate.validate(candidate)
        self.assertIn("OLD_HEAD_WORKFLOW_RECEIPT_REUSED", errors)

    def test_one_shot_rejects_empty_green(self) -> None:
        candidate = self.load("good-ci-epoch.json")
        candidate["workflow_runs"][0]["steps"] = 0
        candidate["verdict"] = "REJECT"
        candidate["digest"] = digest_object(candidate, "digest")
        errors, _ = ci_gate.validate(candidate)
        self.assertIn("EMPTY_OR_SKIPPED_WORKFLOW_PROMOTED_TO_PASS", errors)

    def test_blind_rerun_rejected(self) -> None:
        candidate = self.load("good-ci-epoch.json")
        candidate["publication"]["rerun_count"] = 1
        candidate["publication"]["rerun_classification"] = "CODE_FAILURE"
        candidate["verdict"] = "REJECT"
        candidate["digest"] = digest_object(candidate, "digest")
        errors, _ = ci_gate.validate(candidate)
        self.assertIn("BLIND_RERUN_AFTER_CODE_FAILURE", errors)


if __name__ == "__main__":
    unittest.main(verbosity=2)
