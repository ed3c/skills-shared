from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.check_capability_unlocks import validate_unlock


class CapabilityUnlockTests(unittest.TestCase):
    def good(self):
        return {
            "schema_version": "capability-unlock/v1",
            "id": "unlock-example",
            "skill": "example-skill",
            "skill_sha": "a" * 40,
            "case_ids": [f"holdout-{i}" for i in range(6)],
            "baseline": {"no_skill_passes": 1, "current_skill_passes": 1, "total": 6},
            "candidate": {"passes": 4, "total": 6},
            "supported_stacks": [
                {"model": "model-a", "harness": "codex"},
                {"model": "model-b", "harness": "claude-code"},
            ],
            "evidence_bundles": ["evidence/run-a.json", "evidence/run-b.json"],
        }

    def test_good_unlock_semantics_pass(self):
        validate_unlock(self.good())

    def test_requires_exact_skill_sha(self):
        value = self.good(); value["skill_sha"] = "abcdef0123456789"
        with self.assertRaisesRegex(ValueError, "40-char"):
            validate_unlock(value)

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

    def test_nonexistent_bundle_fails_when_resolved(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError, "cannot read evidence bundle"):
                validate_unlock(self.good(), Path(td))

    def _land_bundle(self, root: Path, *, authority="deterministic", skill_sha=None, case_id="holdout-0", model="model-a", harness="codex", passed=True):
        skill_sha = skill_sha or "a" * 40
        run_id = f"run-{case_id}-{model}-{harness}"
        run_path = root / "runs" / f"{run_id}.json"
        receipt_path = root / "receipts" / f"{run_id}.json"
        bundle_path = root / "evidence" / f"{run_id}.json"
        run_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        bundle_path.parent.mkdir(parents=True, exist_ok=True)
        run_path.write_text(json.dumps({
            "schema_version": "skill-eval-run/v1", "run_id": run_id, "case_id": case_id,
            "skill_sha": skill_sha, "model": {"name": model}, "harness": {"name": harness},
        }))
        receipt_path.write_text(json.dumps({
            "schema_version": "skill-eval-verifier-receipt/v1", "run_id": run_id,
            "case_id": case_id, "authority": authority, "passed": passed,
        }))
        bundle_path.write_text(json.dumps({
            "schema_version": "skill-eval-evidence/v1", "run_id": run_id,
            "case_id": case_id, "skill_sha": skill_sha, "promotion_eligible": True,
            "verifier_receipt": str(receipt_path.relative_to(root)),
            "run_trace": str(run_path.relative_to(root)),
        }))
        return str(bundle_path.relative_to(root))

    def test_llm_judge_bundle_cannot_unlock(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            value = self.good()
            refs = []
            for i in range(6):
                refs.append(self._land_bundle(root, case_id=f"holdout-{i}", model="model-a" if i < 3 else "model-b", harness="codex" if i < 3 else "claude-code", authority="llm_judge" if i == 0 else "deterministic"))
            value["evidence_bundles"] = refs
            with self.assertRaisesRegex(ValueError, "deterministic verifier authority"):
                validate_unlock(value, root)

    def test_wrong_skill_sha_bundle_cannot_unlock(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            value = self.good()
            refs = []
            for i in range(6):
                refs.append(self._land_bundle(root, case_id=f"holdout-{i}", model="model-a" if i < 3 else "model-b", harness="codex" if i < 3 else "claude-code", skill_sha=("b" * 40 if i == 0 else None)))
            value["evidence_bundles"] = refs
            with self.assertRaisesRegex(ValueError, "skill_sha mismatch"):
                validate_unlock(value, root)

    def test_resolved_bundles_must_cover_every_case_and_stack(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            value = self.good()
            refs = []
            for i in range(6):
                refs.append(self._land_bundle(root, case_id=f"holdout-{i}", model="model-a" if i < 3 else "model-b", harness="codex" if i < 3 else "claude-code"))
            value["evidence_bundles"] = refs
            validate_unlock(value, root)


if __name__ == "__main__":
    unittest.main()
