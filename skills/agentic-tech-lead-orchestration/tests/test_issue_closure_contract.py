#!/usr/bin/env python3
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "assert_issue_closure_contract.py"
CLOSURE_AUDIT = Path(__file__).resolve().parents[1] / "references" / "closure-audit"
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
        # A synthetic fixture has no independent reviewer, so it carries the honest
        # self-authored terminal; the bound-PASS path is exercised below.
        "shadow_review": {"verdict": "HUMAN_ADMIT_REQUIRED"},
    }


class IssueClosureContractTest(unittest.TestCase):
    def test_direct_landed_positive(self): self.assertEqual([], closure.validate(base()))
    def test_312_completed_with_unresolved_phase2_fails(self):
        d = base(); d["issue"]["number"] = 312; d["acceptance"].append({"id":"phase2-live-ab","status":"UNRESOLVED","successor":None,"rationale":None})
        self.assertTrue(any("unresolved acceptance" in e for e in closure.validate(d)))
    def test_scope_transfer_requires_successor(self):
        d=base(); d["disposition"]="SCOPE_TRANSFERRED"; d["implementation"]["landing"]=None; d["acceptance"]=[{"id":"phase2-live-ab","status":"TRANSFERRED","successor":None,"rationale":None}]
        self.assertTrue(any("no successor" in e for e in closure.validate(d)))
    def test_scope_transfer_positive(self):
        d=base(); d["disposition"]="SCOPE_TRANSFERRED"; d["implementation"]["landing"]=None; d["acceptance"]=[{"id":"phase1","status":"SATISFIED","successor":None,"rationale":None},{"id":"phase2","status":"TRANSFERRED","successor":"ed3c/skills-shared#231/#232/#234/#256","rationale":None}]
        self.assertEqual([], closure.validate(d))
    def test_403_consumed_without_landing_fails(self):
        d=base(); d["issue"]["number"]=403; d["disposition"]="CONSUMED_BY_CONVERGENCE"; d["implementation"]={"candidate_prs":[{"repository":"ed3c/skills-shared","number":404,"state":"CLOSED","merged":False,"classification":"CONSUMED"}],"landing":None}
        self.assertTrue(any("immutable landed_via" in e for e in closure.validate(d)))
    def test_consumed_with_immutable_landing_passes(self):
        d=base(); d["disposition"]="CONSUMED_BY_CONVERGENCE"; d["implementation"]={"candidate_prs":[{"repository":"ed3c/skills-shared","number":404,"state":"CLOSED","merged":False,"classification":"CONSUMED"}],"landing":{"repository":"ed3c/skills-shared","via_pr":511,"commit":SHA_A,"tree":SHA_B}}
        self.assertEqual([], closure.validate(d))
    def test_cross_repo_direct_landing_is_unambiguous(self):
        d=base(); d["issue"]["number"]=366; d["implementation"]={"candidate_prs":[{"repository":"ed3c/website-design-compiler","number":53,"state":"CLOSED","merged":True,"classification":"DIRECT"}],"landing":{"repository":"ed3c/website-design-compiler","via_pr":53,"commit":SHA_A,"tree":SHA_B}}
        self.assertEqual([], closure.validate(d))
    def test_direct_landing_must_match_repository_and_pr(self):
        d=base(); d["implementation"]["landing"]["repository"]="ed3c/website-design-compiler"
        self.assertTrue(any("does not identify" in e for e in closure.validate(d)))
    def test_candidate_without_repository_fails(self):
        d=base(); del d["implementation"]["candidate_prs"][0]["repository"]
        self.assertTrue(any("repository is ambiguous" in e for e in closure.validate(d)))
    def test_released_ceiling_cannot_hide_unexercised_residual(self):
        d=base(); d["evidence_ceiling"]="RELEASED"; d["residual"]=[{"id":"live","state":"NOT_EXERCISED","owner":"ed3c/skills-shared#464"}]
        self.assertTrue(any("promoted to RELEASED" in e for e in closure.validate(d)))
    def test_closed_requires_shadow(self):
        d=base(); d["shadow_review"]["verdict"]="HOLD"
        self.assertTrue(any("Shadow verdict" in e for e in closure.validate(d)))


class ShadowBindingTest(unittest.TestCase):
    """#606: a PASS verdict must name a Shadow distinct from the packet author."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        receipt = self.root / "docs/traceability/shadow-receipt.json"
        receipt.parent.mkdir(parents=True)
        receipt.write_text('{"verdict": "PASS"}\n', encoding="utf-8")
        self.receipt = {"path": "docs/traceability/shadow-receipt.json", "sha256": hashlib.sha256(receipt.read_bytes()).hexdigest()}

    def bound(self):
        d = base()
        d["shadow_review"] = {
            "verdict": "PASS",
            "packet_author": {"host_class": "CLAUDE_CODE_LOCAL", "session_id": "writer-1", "worktree": "handoff-queue-audit"},
            "shadow_identity": {"host_class": "CLAUDE_CODE_LOCAL", "session_id": "shadow-2", "worktree": "shadow-audit"},
            "receipt": dict(self.receipt),
        }
        return d

    def test_bound_pass_positive(self): self.assertEqual([], closure.validate(self.bound(), root=self.root))
    def test_unbound_pass_is_refused(self):
        d=base(); d["shadow_review"]={"verdict":"PASS"}
        self.assertTrue(any("self-authored packet is HUMAN_ADMIT_REQUIRED" in e for e in closure.validate(d, root=self.root)))
    def test_self_signed_shadow_is_refused(self):
        d=self.bound(); d["shadow_review"]["shadow_identity"]=dict(d["shadow_review"]["packet_author"])
        self.assertTrue(any("distinct from the packet author" in e for e in closure.validate(d, root=self.root)))
    def test_anonymous_shadow_is_refused(self):
        d=self.bound(); d["shadow_review"]["shadow_identity"]["session_id"]=None
        self.assertTrue(any("named Shadow session_id" in e for e in closure.validate(d, root=self.root)))
    def test_absent_receipt_file_is_refused(self):
        d=self.bound(); d["shadow_review"]["receipt"]["path"]="docs/traceability/never-written.json"
        self.assertTrue(any("absent at its bound path" in e for e in closure.validate(d, root=self.root)))
    def test_receipt_digest_mismatch_is_refused(self):
        d=self.bound(); d["shadow_review"]["receipt"]["sha256"]="0"*64
        self.assertTrue(any("does not match its bound sha256" in e for e in closure.validate(d, root=self.root)))
    def test_historical_unbound_pass_stays_green(self):
        d=base(); d["shadow_review"]={"verdict":"PASS"}
        self.assertEqual([], closure.validate(d, historical=True, root=self.root))
    def test_human_admit_required_needs_no_binding(self): self.assertEqual([], closure.validate(base(), root=self.root))

    def test_planted_flip_of_a_historical_packet_is_refused(self):
        """Permanent control: HUMAN_ADMIT_REQUIRED -> PASS on the real ledger packets #606 was proven on."""
        for name in ("issue-407.json", "issue-508.json"):
            packet = CLOSURE_AUDIT / name
            d = json.loads(packet.read_text(encoding="utf-8"))
            self.assertEqual("HUMAN_ADMIT_REQUIRED", d["shadow_review"]["verdict"], name)
            d["shadow_review"]["verdict"] = "PASS"
            self.assertIs(False, closure.is_historical(name, d), name)
            self.assertTrue(any("self-authored packet is HUMAN_ADMIT_REQUIRED" in e for e in closure.validate(d)), name)

    def test_grandfathered_packets_are_named_one_by_one(self):
        ledger = json.loads((CLOSURE_AUDIT / "enforced-from.json").read_text(encoding="utf-8"))
        for entry in ledger["grandfathered_unbound_pass"]:
            d = json.loads((CLOSURE_AUDIT / entry["file"]).read_text(encoding="utf-8"))
            self.assertEqual(entry["issue"], d["issue"]["number"], entry["file"])
            self.assertEqual(entry["shadow_verdict"], d["shadow_review"]["verdict"], entry["file"])
            self.assertIs(True, closure.is_historical(entry["file"], d))

if __name__ == "__main__": unittest.main()
