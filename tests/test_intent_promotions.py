"""Contract tests for the intent-promotion gate.

The selftest inside `scripts/check_intent_promotions.py` proves the gate refuses
its planted defects. These tests prove the committed fixtures satisfy the
committed schemas, and that the CLI's exit codes and digest binding behave as a
caller would rely on -- the parts a selftest running in memory cannot observe.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts" / "check_intent_promotions.py"
FIXTURES = ROOT / "evals" / "fixtures" / "intent-promotion"
SCHEMAS = ROOT / "evals" / "schema"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), *args],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )


class SchemaShapeTests(unittest.TestCase):
    def test_schemas_are_parseable_and_identified(self) -> None:
        for name, expected in (
            ("intent-promotion-contract.schema.json", "Intent Promotion Contract"),
            ("intent-promotion-receipt.schema.json", "Intent Promotion Receipt"),
        ):
            body = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
            self.assertEqual(body["title"], expected)
            self.assertTrue(body["$id"].endswith(name))
            self.assertFalse(body["additionalProperties"])

    def test_receipt_schema_binds_evaluator_and_approval_identity(self) -> None:
        """The hardened fields are what a caller cannot fabricate alone."""
        body = json.loads(
            (SCHEMAS / "intent-promotion-receipt.schema.json").read_text(encoding="utf-8")
        )
        run_required = set(body["properties"]["evaluator_receipts"]["items"]["required"])
        for field in ("evaluator_version", "evaluator_artifact_digest",
                      "receipt_ref", "receipt_digest", "execution_origin",
                      "subject_tree_sha"):
            self.assertIn(field, run_required)

        approval = body["properties"]["approval"]["anyOf"][1]
        for field in ("generated_by_agent", "review_ref", "readback_source"):
            self.assertIn(field, approval["required"])

        merge = body["properties"]["merge_subject"]["anyOf"][1]
        for field in ("candidate_head_sha", "candidate_tree_sha", "forge_readback"):
            self.assertIn(field, merge["required"])

    def test_contract_schema_pins_the_non_negotiable_constants(self) -> None:
        body = json.loads(
            (SCHEMAS / "intent-promotion-contract.schema.json").read_text(encoding="utf-8")
        )
        writeback = body["properties"]["writeback_policy"]["properties"]
        self.assertEqual(writeback["append_only"], {"const": True})
        self.assertEqual(writeback["similarity_overwrite_allowed"], {"const": False})
        approval = body["properties"]["approval_policy"]["properties"]
        self.assertEqual(approval["agent_may_create_approval"], {"const": False})
        self.assertEqual(approval["caller_flag_may_grant"], {"const": False})
        destination = body["properties"]["writeback_policy"]["properties"][
            "declared_destinations"]["items"]["properties"]
        self.assertEqual(destination["minimum_state"]["enum"], ["ADMITTED", "CANONICAL"])
        supersession = body["properties"]["supersession_policy"]["properties"]
        self.assertEqual(supersession["append_only_ledger"], {"const": True})


class FixtureTests(unittest.TestCase):
    def test_committed_fixtures_are_admitted(self) -> None:
        self.assertEqual(run("contract", str(FIXTURES / "valid-contract.json")).returncode, 0)
        for receipt in ("valid-receipt.json", "canonical-receipt.json",
                        "supersede-receipt.json"):
            result = run(
                "receipt", str(FIXTURES / receipt),
                "--contract", str(FIXTURES / "valid-contract.json"),
                "--ledger", str(FIXTURES / "ledger.json"),
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_no_destination_is_reachable_before_admitted(self) -> None:
        """Durable projection begins at ADMITTED, for every scope."""
        contract = json.loads((FIXTURES / "valid-contract.json").read_text(encoding="utf-8"))
        for destination in contract["writeback_policy"]["declared_destinations"]:
            self.assertIn(destination["minimum_state"], ("ADMITTED", "CANONICAL"),
                          destination["destination_id"])

    def test_supersession_without_a_ledger_is_refused(self) -> None:
        """A lineage claim nothing can confirm is not lineage."""
        result = run(
            "receipt", str(FIXTURES / "supersede-receipt.json"),
            "--contract", str(FIXTURES / "valid-contract.json"),
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("ledger", result.stderr)

    def test_receipt_digest_binds_the_committed_contract_bytes(self) -> None:
        raw = (FIXTURES / "valid-contract.json").read_bytes()
        expected = "sha256:" + hashlib.sha256(raw).hexdigest()
        for receipt in ("valid-receipt.json", "canonical-receipt.json",
                        "supersede-receipt.json"):
            body = json.loads((FIXTURES / receipt).read_text(encoding="utf-8"))
            self.assertEqual(body["contract_digest"], expected, receipt)

    def test_editing_the_contract_invalidates_every_receipt(self) -> None:
        """Rules and evidence move together, or evidence outlives its rules."""
        with tempfile.TemporaryDirectory() as raw:
            work = Path(raw)
            contract = json.loads((FIXTURES / "valid-contract.json").read_text(encoding="utf-8"))
            contract["contract_version"] = "1.0.1"
            altered = work / "contract.json"
            altered.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            result = run(
                "receipt", str(FIXTURES / "valid-receipt.json"), "--contract", str(altered)
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("contract_digest", result.stderr)


class ExitContractTests(unittest.TestCase):
    def test_selftest_is_green(self) -> None:
        result = run("selftest")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("mutations refused", result.stdout)

    def test_refusal_and_unusable_input_do_not_collapse(self) -> None:
        """A refused promotion is 2; an input that could not be read is 64.

        Collapsing them makes a mistyped path read as a policy failure, which
        is the more dangerous direction: it looks like the gate is working.
        """
        with tempfile.TemporaryDirectory() as raw:
            broken = Path(raw) / "broken.json"
            broken.write_text("{not json", encoding="utf-8")
            self.assertEqual(run("contract", str(broken)).returncode, 64)

            absent = Path(raw) / "absent.json"
            self.assertEqual(run("contract", str(absent)).returncode, 64)

            # An evaluated failure stays 2.
            wrong = json.loads((FIXTURES / "valid-contract.json").read_text(encoding="utf-8"))
            wrong["writeback_policy"]["declared_destinations"][0]["minimum_state"] = "PROPOSED"
            path = Path(raw) / "wrong.json"
            path.write_text(json.dumps(wrong), encoding="utf-8")
            self.assertEqual(run("contract", str(path)).returncode, 2)

        # Usage errors are argparse's exit 2 on stderr, distinct from a refusal
        # message; assert the refusal path always names itself.
        result = run("contract", str(FIXTURES / "valid-receipt.json"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("INTENT PROMOTION RED", result.stderr)


if __name__ == "__main__":
    unittest.main()
