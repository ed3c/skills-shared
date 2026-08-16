from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLISHER = ROOT / "scripts" / "publish_source_contribution.py"

DRIFT = 2
INVALID = 64


def run(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PUBLISHER), "--skill-root", str(root), *args],
        capture_output=True,
        text=True,
    )


class Sandbox:
    """A throwaway copy of the skill, so a planted defect never touches the tree."""

    def __init__(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "skill"
        for name in ("evals", "modules", "scripts"):
            shutil.copytree(ROOT / name, self.root / name)

    def state(self) -> dict:
        return json.loads((self.root / "evals/live-evidence-state.json").read_text())

    def write_state(self, payload: dict) -> None:
        (self.root / "evals/live-evidence-state.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n"
        )

    def close(self) -> None:
        self.tmp.cleanup()


class CommittedOutputs(unittest.TestCase):
    def test_committed_outputs_match_a_fresh_generation(self) -> None:
        result = run(ROOT, "--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("SOURCE-CONTRIBUTION-GREEN", result.stdout)

    def test_the_derived_layer_a_fractions_reproduce_the_committed_map(self) -> None:
        """The prose table in modules/ was written by hand before this generator."""
        report = json.loads((ROOT / "evals/live-source-contribution.json").read_text())
        expected = {
            "current-system-prompt": "13/16",
            "spatial-loop-systems-engineering": "5/7",
            "external-verify": "2/3",
            "judge-loop-chooser": "1/3",
            "controlled-technical-language-harness": "2/4",
            "knowledge-continuity": "1/3",
            "github-delivery-loop": "3/5",
        }
        for source, fraction in expected.items():
            self.assertEqual(report["sources"][source]["layer_a_fraction"], fraction, source)
        self.assertEqual(report["denominators"]["dependency_supported_mappings"], 14)
        self.assertEqual(report["denominators"]["dependency_source_mappings"], 25)


class OverlapIsPreserved(unittest.TestCase):
    def setUp(self) -> None:
        self.report = json.loads((ROOT / "evals/live-source-contribution.json").read_text())
        self.overlap = json.loads((ROOT / "evals/rule-to-source-overlap.json").read_text())

    def test_a_rule_named_by_several_sources_stays_named_by_several(self) -> None:
        shared = [r for r, e in self.overlap["rules"].items() if e["source_count"] > 1]
        self.assertTrue(shared, "the corpus has overlapping sources; the map must show it")
        for rule_id in shared:
            for source in self.overlap["rules"][rule_id]["sources"]:
                claim = next(
                    c for c in self.report["sources"][source]["claims"] if c["claim_id"] == rule_id
                )
                self.assertFalse(claim["isolable"])
                self.assertTrue(claim["shared_with_sources"])

    def test_the_denominators_are_not_one_number(self) -> None:
        counts = self.report["denominators"]
        self.assertNotEqual(counts["unique_semantic_claims"], counts["source_mappings"])
        self.assertGreater(counts["source_mappings"], counts["unique_semantic_claims"])

    def test_no_summed_total_is_published(self) -> None:
        """Summing overlapping fractions double-counts every shared rule."""
        text = json.dumps(self.report)
        for forbidden in ("total_fraction", "total_contribution", "aggregate_fraction"):
            self.assertNotIn(forbidden, text)
        for entry in self.report["sources"].values():
            self.assertIsInstance(entry["layer_a_fraction"], str)

    def test_the_lower_bound_never_exceeds_the_upper_bound(self) -> None:
        for source, entry in self.report["sources"].items():
            self.assertLessEqual(
                entry["layer_a_isolable_lower_bound"], entry["layer_a_upper_bound"], source
            )


class PlantedDefects(unittest.TestCase):
    def setUp(self) -> None:
        self.box = Sandbox()
        self.addCleanup(self.box.close)

    def test_a_live_state_with_no_matched_pair_is_refused(self) -> None:
        state = self.box.state()
        state["rules"]["RCA-001"]["live_state"] = "LIVE_MODEL_SUPPORTED"
        state["lanes"]["233_source_contribution"]["state"] = "LIVE_PARTIAL"
        self.box.write_state(state)
        result = run(self.box.root, "--check")
        self.assertEqual(result.returncode, INVALID, result.stdout)
        self.assertIn("unpaid-live-state", result.stderr)

    def test_a_live_state_whose_pair_receipt_is_absent_is_refused(self) -> None:
        state = self.box.state()
        state["rules"]["RCA-001"]["live_state"] = "LIVE_MODEL_SUPPORTED"
        state["rules"]["RCA-001"]["pairs"] = [
            {"receipt": "evals/receipts/does-not-exist.json"},
            {"receipt": "evals/receipts/also-absent.json"},
        ]
        state["lanes"]["233_source_contribution"]["state"] = "LIVE_PARTIAL"
        self.box.write_state(state)
        result = run(self.box.root, "--check")
        self.assertEqual(result.returncode, INVALID, result.stdout)
        self.assertIn("absent-pair-receipt", result.stderr)

    def test_a_pair_receipt_that_moved_under_its_digest_is_refused(self) -> None:
        state = self.box.state()
        state["rules"]["RCA-001"]["live_state"] = "LIVE_MODEL_SUPPORTED"
        state["rules"]["RCA-001"]["pairs"] = [
            {"receipt": "evals/pilot-result.json", "sha256": "00" * 32},
            {"receipt": "evals/matrix-slice1-result.json", "sha256": "00" * 32},
        ]
        state["lanes"]["233_source_contribution"]["state"] = "LIVE_PARTIAL"
        self.box.write_state(state)
        result = run(self.box.root, "--check")
        self.assertEqual(result.returncode, INVALID, result.stdout)
        self.assertIn("pair-receipt-digest-mismatch", result.stderr)

    def test_a_lane_claiming_more_than_its_rules_is_refused(self) -> None:
        state = self.box.state()
        state["lanes"]["233_source_contribution"]["state"] = "LIVE_PARTIAL"
        self.box.write_state(state)
        result = run(self.box.root, "--check")
        self.assertEqual(result.returncode, INVALID, result.stdout)
        self.assertIn("lane-state-mismatch", result.stderr)

    def test_a_rule_the_contract_retains_cannot_be_dropped_from_the_state(self) -> None:
        state = self.box.state()
        del state["rules"]["RCA-007"]
        self.box.write_state(state)
        result = run(self.box.root, "--check")
        self.assertEqual(result.returncode, INVALID, result.stdout)
        self.assertIn("rule-set-mismatch", result.stderr)

    def test_a_receipt_the_state_names_must_exist(self) -> None:
        state = self.box.state()
        state["receipts"].append(
            {"receipt_id": "invented", "path": "evals/receipts/invented.json", "layer": "B"}
        )
        self.box.write_state(state)
        result = run(self.box.root, "--check")
        self.assertEqual(result.returncode, INVALID, result.stdout)
        self.assertIn("absent-receipt", result.stderr)


class AbsenceStaysDistinct(unittest.TestCase):
    def setUp(self) -> None:
        self.box = Sandbox()
        self.addCleanup(self.box.close)

    def test_an_edited_output_is_drift_not_invalid_input(self) -> None:
        target = self.box.root / "evals/live-source-contribution.md"
        target.write_text(target.read_text() + "\nhand edit\n")
        result = run(self.box.root, "--check")
        self.assertEqual(result.returncode, DRIFT, result.stdout)
        self.assertIn("stale: evals/live-source-contribution.md", result.stderr)

    def test_a_pinned_file_is_covered_by_the_published_sums(self) -> None:
        target = self.box.root / "modules/measurement-limits.md"
        target.write_text(target.read_text() + "\nhand edit\n")
        result = run(self.box.root, "--check")
        self.assertEqual(result.returncode, DRIFT, result.stdout)
        self.assertIn("stale: evals/SHA256SUMS", result.stderr)

    def test_absent_input_is_invalid_rather_than_drift(self) -> None:
        (self.box.root / "evals/live-evidence-state.json").unlink()
        result = run(self.box.root, "--check")
        self.assertEqual(result.returncode, INVALID, result.stdout)
        self.assertIn("absent-input", result.stderr)

    def test_a_claim_with_no_retained_rule_can_never_reach_a_live_state(self) -> None:
        """There is nothing to ablate, so no receipt could ever support it."""
        report = json.loads((ROOT / "evals/live-source-contribution.json").read_text())
        unmapped = [
            claim
            for entry in report["sources"].values()
            for claim in entry["claims"]
            if not claim["mapped_rule_ids"]
        ]
        self.assertTrue(unmapped)
        for claim in unmapped:
            self.assertEqual(claim["layer_b_state"], "UNPROVEN_FOR_CORE", claim["claim_id"])


if __name__ == "__main__":
    unittest.main()
