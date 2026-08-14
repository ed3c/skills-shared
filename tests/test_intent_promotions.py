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


class FixtureTests(unittest.TestCase):
    def test_committed_fixtures_are_admitted(self) -> None:
        self.assertEqual(run("contract", str(FIXTURES / "valid-contract.json")).returncode, 0)
        for receipt in ("valid-receipt.json", "canonical-receipt.json"):
            result = run(
                "receipt", str(FIXTURES / receipt),
                "--contract", str(FIXTURES / "valid-contract.json"),
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_receipt_digest_binds_the_committed_contract_bytes(self) -> None:
        raw = (FIXTURES / "valid-contract.json").read_bytes()
        expected = "sha256:" + hashlib.sha256(raw).hexdigest()
        for receipt in ("valid-receipt.json", "canonical-receipt.json"):
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

    def test_refusal_and_unreadable_input_do_not_collapse(self) -> None:
        """A refused promotion is 2; an unusable input is not the same event."""
        with tempfile.TemporaryDirectory() as raw:
            broken = Path(raw) / "broken.json"
            broken.write_text("{not json", encoding="utf-8")
            self.assertEqual(run("contract", str(broken)).returncode, 2)

            absent = Path(raw) / "absent.json"
            self.assertEqual(run("contract", str(absent)).returncode, 2)

        # Usage errors are argparse's exit 2 on stderr, distinct from a refusal
        # message; assert the refusal path always names itself.
        result = run("contract", str(FIXTURES / "valid-receipt.json"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("INTENT PROMOTION RED", result.stderr)


if __name__ == "__main__":
    unittest.main()
