#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "assert_issue_closure_contract.py"
spec = importlib.util.spec_from_file_location("closure", SCRIPT)
closure = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(closure)

SHA_A = "a" * 40
SHA_B = "b" * 40


def base():
    return {
        "schema_version": "agentic-tech-lead/issue-closure-contract/v1",
        "issue": {"repository": "ed3c/skills-shared", "number": 505, "github_state": "CLOSED", "github_state_reason": "COMPLETED"},
        "disposition": "DIRECTLY_LANDED",
        "acceptance": [{"id": "tree-truth", "status": "SATISFIED", "successor": None, "rationale": None}],
        "implementation": {
            "candidate_prs": [{"repository": "ed3c/skills-shared", "number": 507, "state": "CLOSED", "merged": True, "classification": "DIRECT"}],
            "landing": {"repository": "ed3c/skills-shared", "via_pr": 507, "commit": SHA_A, "tree": SHA_B},
        },
        "residual": [{"id": "fresh-live-v2", "state": "TRANSFERRED", "owner": "ed3c/skills-shared#464"}],
        "evidence_ceiling": "DETERMINISTIC",
        "shadow_review": {"verdict": "PASS"},
    }


class IssueClosureContractTest(unittest.TestCase):
    def test_direct_landed_positive(self):
        self.assertEqual([], closure.validate(base()))

    def test_312_completed_with_unresolved_phase2_fails(self):
        d = base(); d["issue"]["number"] = 312
        d["acceptance"].append({"id": "phase2-live-ab", "status": "UNRESOLVED", "successor": None, "rationale": None})
        self.assertTrue(any("unresolved acceptance" in e for e in closure.validate(d)))

    def test_scope_transfer_requires_successor(self):
        d = base(); d["disposition"] = "SCOPE_TRANSFERRED"; d["implementation"]["landing"] = None
        d["acceptance"] = [{"id": "phase2-live-ab", "status": "TRANSFERRED", "successor": None, "rationale": None}]
        self.assertTrue(any("no successor" in e for e in closure.validate(d)))

    def test_scope_transfer_positive(self):
        d = base(); d["disposition"] = "SCOPE_TRANSFERRED"; d["implementation"]["landing"] = None
        d["acceptance"] = [
            {"id": "phase1", "status": "SATISFIED", "successor": None, "rationale": None},
            {"id": "phase2", "status": "TRANSFERRED", "successor": "ed3c/skills-shared#231/#232/#234/#256", "rationale": None},
        ]
        self.assertEqual([], closure.validate(d))

    def test_403_consumed_without_landing_fails(self):
        d = base(); d["issue"]["number"] = 403; d["disposition"] = "CONSUMED_BY_CONVERGENCE"
        d["implementation"] = {"candidate_prs": [{"repository": "ed3c/skills-shared", "number": 404, "state": "CLOSED", "merged": False, "classification": "CONSUMED"}], "landing": None}
        self.assertTrue(any("immutable landed_via" in e for e in closure.validate(d)))

    def test_consumed_with_immutable_landing_passes(self):
        d = base(); d["disposition"] = "CONSUMED_BY_CONVERGENCE"
        d["implementation"] = {
            "candidate_prs": [{"repository": "ed3c/skills-shared", "number": 404, "state": "CLOSED", "merged": False, "classification": "CONSUMED"}],
            "landing": {"repository": "ed3c/skills-shared", "via_pr": 511, "commit": SHA_A, "tree": SHA_B},
        }
        self.assertEqual([], closure.validate(d))

    def test_cross_repo_direct_landing_is_unambiguous(self):
        d = base(); d["issue"]["number"] = 366
        d["implementation"] = {
            "candidate_prs": [{"repository": "ed3c/website-design-compiler", "number": 53, "state": "CLOSED", "merged": True, "classification": "DIRECT"}],
            "landing": {"repository": "ed3c/website-design-compiler", "via_pr": 53, "commit": SHA_A, "tree": SHA_B},
        }
        self.assertEqual([], closure.validate(d))

    def test_direct_landing_must_match_repository_and_pr(self):
        d = base(); d["implementation"]["landing"]["repository"] = "ed3c/website-design-compiler"
        self.assertTrue(any("does not identify" in e for e in closure.validate(d)))

    def test_candidate_without_repository_fails(self):
        d = base(); del d["implementation"]["candidate_prs"][0]["repository"]
        self.assertTrue(any("repository is ambiguous" in e for e in closure.validate(d)))

    def test_released_ceiling_cannot_hide_unexercised_residual(self):
        d = base(); d["evidence_ceiling"] = "RELEASED"; d["residual"] = [{"id": "live", "state": "NOT_EXERCISED", "owner": "ed3c/skills-shared#464"}]
        self.assertTrue(any("promoted to RELEASED" in e for e in closure.validate(d)))

    def test_closed_requires_shadow(self):
        d = base(); d["shadow_review"]["verdict"] = "HOLD"
        self.assertTrue(any("Shadow verdict" in e for e in closure.validate(d)))


if __name__ == "__main__":
    unittest.main()
