from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_canary_receipt.py"
SCHEMA_ROOT = ROOT / "references"


def digest(seed: str) -> str:
    return (seed * 64)[:64]


def probe(probe_id: str, outcome: str = "PASS") -> dict:
    return {"probe_id": probe_id, "attempted": True, "outcome": outcome}


def receipt() -> dict:
    return {
        "schema": "canary-receipt/v1",
        "canary_id": "rca-canary-alpha-2026-08",
        "consumer": {
            "repository_id": "example/consumer-alpha",
            "commit_sha": "a" * 40,
            "tree_sha": "b" * 40,
            "authorization_state": "PUBLIC",
        },
        "audit_subject": {
            "skill_digest": digest("5"),
            "module_digests": {"modules/domain-instances.md": digest("6")},
        },
        "identities": {
            "model_provider": "anthropic",
            "model_family": "claude",
            "model_version": "opus-4",
            "agent_harness": "claude-code",
            "agent_harness_version": "1.0.0",
            "runtime_identity": "CLAUDE_CODE_LOCAL",
            "runtime_version": "1.0.0",
            "toolset_digest": digest("7"),
        },
        "evaluator": {
            "evaluator_id": "deterministic-audit-evaluator",
            "version": "1.0.0",
            "digest": digest("e"),
            "owner": "INDEPENDENT_DETERMINISTIC",
        },
        "task_digest": digest("8"),
        "credential_authorization": {
            "credentials_granted": ["read-only-github-token"],
            "credential_present": True,
            "denial_reason": None,
            "data_egress_approved": True,
            "private_data_present": False,
            "data_egress_provider_approved": True,
        },
        "policy": {
            "network_policy": "allowlisted: github.com only",
            "filesystem_policy": "workspace-write, no host escape",
            "side_effect_policy": "no publication outside the admitted artifact paths",
        },
        "probes": {
            "positive": [probe("real-capability-with-evidence")],
            "falsifying": [probe("overstated-readme-claim")],
        },
        "rollback": {
            "rollback_subject_id": "known-good-2026-08-01",
            "rollback_subject_digest": digest("9"),
            "candidate_subject_id": "candidate-2026-08-15",
            "candidate_subject_digest": digest("c"),
            "cleanup_verified": True,
            "cleanup_evidence": "worktree and process residue scan: clean",
        },
        "publication": {
            "required_artifacts": ["verdict.json", "summary.md"],
            "published_artifacts": ["verdict.json", "summary.md"],
            "all_required_artifacts_published": True,
        },
        "gate_state": {
            "is_first_green": False,
            "production_like_gate_executed": True,
        },
        "module_shadowing": {
            "consumer_local_module_present": False,
            "shadows_canonical_digest": False,
        },
        "service_status": {
            "external_service_reachable": True,
        },
        "staleness": {
            "material_identity_changed_since_bound": False,
            "revalidated": False,
        },
        "revalidation_triggers": {
            "skill_or_module_digest": digest("s"),
            "model_provider_version_config": "anthropic/claude/opus-4",
            "agent_harness_or_tool_surface": "claude-code/1.0.0",
            "runtime_image_or_workflow_version": "CLAUDE_CODE_LOCAL/1.0.0",
            "evaluator_corpus_or_policy_digest": digest("e"),
            "repository_head_or_capability_claim": "a" * 40,
            "artifact_publication_path": "evals/receipts/",
        },
        "run_window": {
            "started_at": "2026-08-15T00:00:00Z",
            "ended_at": "2026-08-15T01:00:00Z",
            "expiry_at": "2026-11-15T00:00:00Z",
        },
    }


def run(document: dict) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "receipt.json"
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        process = subprocess.run(
            [sys.executable, str(CHECKER), str(path), "--schema-root", str(SCHEMA_ROOT)],
            capture_output=True, text=True, check=False,
        )
        return process.returncode, process.stderr


class CanaryReceiptTests(unittest.TestCase):
    def test_a_clean_receipt_is_admissible(self):
        code, stderr = run(receipt())
        self.assertEqual(code, 0, stderr)

    def test_stale_receipt_reused_after_subject_movement_is_refused(self):
        document = receipt()
        document["staleness"] = {
            "material_identity_changed_since_bound": True,
            "revalidated": False,
        }
        code, stderr = run(document)
        self.assertEqual(code, 2, stderr)
        self.assertIn("stale-receipt-reused-after-subject-movement", stderr)

    def test_external_outage_recorded_as_repository_defect_is_refused(self):
        document = receipt()
        document["service_status"]["external_service_reachable"] = False
        document["probes"]["positive"][0]["outcome"] = "FAIL_REPOSITORY_DEFECT"
        code, stderr = run(document)
        self.assertEqual(code, 2, stderr)
        self.assertIn("external-service-outage-recorded-as-repository-defect", stderr)

    def test_missing_credential_recorded_as_policy_denial_is_refused(self):
        document = receipt()
        document["credential_authorization"]["credential_present"] = False
        document["credential_authorization"]["denial_reason"] = "POLICY_DENIED"
        code, stderr = run(document)
        self.assertEqual(code, 2, stderr)
        self.assertIn("credential-missing-recorded-as-policy-denial", stderr)

    def test_policy_denial_recorded_as_credential_missing_is_refused(self):
        document = receipt()
        document["credential_authorization"]["credential_present"] = True
        document["credential_authorization"]["denial_reason"] = "CREDENTIAL_MISSING"
        code, stderr = run(document)
        self.assertEqual(code, 2, stderr)
        self.assertIn("policy-denial-recorded-as-credential-missing", stderr)

    def test_partial_artifact_publication_accepted_as_complete_is_refused(self):
        document = receipt()
        document["publication"]["published_artifacts"] = ["verdict.json"]
        document["publication"]["all_required_artifacts_published"] = True
        code, stderr = run(document)
        self.assertEqual(code, 2, stderr)
        self.assertIn("partial-publication-accepted-as-complete", stderr)

    def test_first_green_with_skipped_production_like_gate_is_refused(self):
        document = receipt()
        document["gate_state"] = {
            "is_first_green": True,
            "production_like_gate_executed": False,
        }
        code, stderr = run(document)
        self.assertEqual(code, 2, stderr)
        self.assertIn("first-green-with-skipped-production-like-gate", stderr)

    def test_rollback_target_equal_to_candidate_is_refused(self):
        document = receipt()
        document["rollback"]["rollback_subject_digest"] = document["rollback"]["candidate_subject_digest"]
        code, stderr = run(document)
        self.assertEqual(code, 2, stderr)
        self.assertIn("rollback-target-equals-candidate", stderr)

    def test_consumer_local_module_shadowing_canonical_is_refused(self):
        document = receipt()
        document["module_shadowing"] = {
            "consumer_local_module_present": True,
            "shadows_canonical_digest": True,
        }
        code, stderr = run(document)
        self.assertEqual(code, 2, stderr)
        self.assertIn("consumer-local-module-shadows-canonical", stderr)

    def test_private_data_routed_to_unapproved_provider_is_refused(self):
        document = receipt()
        document["credential_authorization"]["private_data_present"] = True
        document["credential_authorization"]["data_egress_provider_approved"] = False
        code, stderr = run(document)
        self.assertEqual(code, 2, stderr)
        self.assertIn("private-data-routed-to-unapproved-provider", stderr)

    def test_producer_owned_evaluator_is_schema_invalid(self):
        document = receipt()
        document["evaluator"]["owner"] = "PRODUCER"
        code, stderr = run(document)
        self.assertEqual(code, 64, stderr)
        self.assertIn("schema-invalid", stderr)

    def test_missing_required_field_is_schema_invalid(self):
        document = receipt()
        del document["rollback"]
        code, stderr = run(document)
        self.assertEqual(code, 64, stderr)
        self.assertIn("schema-invalid", stderr)

    def test_absent_input_stays_distinct(self):
        process = subprocess.run(
            [sys.executable, str(CHECKER), str(ROOT / "tests" / "fixtures" / "absent.json")],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(process.returncode, 64)
        self.assertIn("absent-input", process.stderr)


if __name__ == "__main__":
    unittest.main()
