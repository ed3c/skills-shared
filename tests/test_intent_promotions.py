"""Tests for the intent-promotion lifecycle and durable-writeback gate."""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_intent_promotions.py"
FIXTURES = ROOT / "evals" / "fixtures" / "intent-promotion"
SCHEMAS = ROOT / "evals" / "schema"

SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from intent_promotion.common import PolicyRefusal  # noqa: E402
from intent_promotion.contract import validate_contract  # noqa: E402
from intent_promotion.fixtures import build_fixture_receipt  # noqa: E402
from intent_promotion.receipt import validate_receipt  # noqa: E402


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-S", str(CHECKER), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )


class SchemaShapeTests(unittest.TestCase):
    def test_schemas_are_parseable_and_closed(self) -> None:
        for name, title in (
            ("intent-promotion-contract.schema.json", "Intent Promotion Contract"),
            ("intent-promotion-receipt.schema.json", "Intent Promotion Receipt"),
        ):
            body = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
            self.assertEqual(body["title"], title)
            self.assertTrue(body["$id"].endswith(name))
            self.assertFalse(body["additionalProperties"])

    def test_contract_schema_pins_non_negotiable_policy(self) -> None:
        body = json.loads(
            (SCHEMAS / "intent-promotion-contract.schema.json").read_text(
                encoding="utf-8"
            )
        )
        writeback = body["properties"]["writeback_policy"]["properties"]
        self.assertEqual(writeback["append_only"], {"const": True})
        self.assertEqual(
            writeback["similarity_overwrite_allowed"], {"const": False}
        )
        self.assertEqual(
            writeback["durable_writeback_min_state"], {"const": "ADMITTED"}
        )
        approval = body["properties"]["approval_policy"]["properties"]
        self.assertEqual(approval["agent_may_create_approval"], {"const": False})
        self.assertEqual(
            approval["automation_may_create_approval"], {"const": False}
        )
        self.assertEqual(approval["caller_flag_may_grant"], {"const": False})


class FixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract_path = FIXTURES / "valid-contract.json"
        cls.contract_raw = cls.contract_path.read_bytes()
        cls.contract = json.loads(cls.contract_raw)

    def test_committed_contract_is_admitted(self) -> None:
        result = run("contract", str(self.contract_path))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_committed_receipts_are_admitted(self) -> None:
        for name in (
            "valid-receipt.json",
            "admitted-receipt.json",
            "canonical-receipt.json",
        ):
            result = run(
                "receipt",
                str(FIXTURES / name),
                "--contract",
                str(self.contract_path),
            )
            self.assertEqual(result.returncode, 0, f"{name}: {result.stderr}")

    def test_receipts_bind_exact_contract_bytes(self) -> None:
        expected = "sha256:" + hashlib.sha256(self.contract_raw).hexdigest()
        for name in (
            "valid-receipt.json",
            "admitted-receipt.json",
            "canonical-receipt.json",
        ):
            body = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
            self.assertEqual(
                body["contract_identity"]["contract_digest"], expected, name
            )

    def test_editing_contract_invalidates_every_receipt(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["contract_version"] = "1.1.1"
        changed_raw = (
            json.dumps(changed, indent=2, sort_keys=True) + "\n"
        ).encode()
        receipt = json.loads(
            (FIXTURES / "valid-receipt.json").read_text(encoding="utf-8")
        )
        with self.assertRaises(PolicyRefusal):
            validate_receipt(receipt, changed, changed_raw)

    def test_evaluator_registry_identity_is_load_bearing(self) -> None:
        receipt = json.loads(
            (FIXTURES / "valid-receipt.json").read_text(encoding="utf-8")
        )
        receipt["evaluator_receipts"][1]["implementation_digest"] = (
            "sha256:" + "0" * 64
        )
        with self.assertRaisesRegex(
            PolicyRefusal, "changed evaluator identity"
        ):
            validate_receipt(receipt, self.contract, self.contract_raw)

    def test_foreign_green_job_cannot_proxy_owning_ci(self) -> None:
        receipt = json.loads(
            (FIXTURES / "valid-receipt.json").read_text(encoding="utf-8")
        )
        receipt["evaluator_receipts"][1]["evaluator_id"] = "foreign-green-job"
        with self.assertRaisesRegex(PolicyRefusal, "not registered"):
            validate_receipt(receipt, self.contract, self.contract_raw)

    def test_pr_head_must_equal_candidate_head(self) -> None:
        receipt = json.loads(
            (FIXTURES / "valid-receipt.json").read_text(encoding="utf-8")
        )
        receipt["pr_subject"]["head_sha"] = "1" * 40
        with self.assertRaisesRegex(PolicyRefusal, "PR subject head"):
            validate_receipt(receipt, self.contract, self.contract_raw)

    def test_durable_projection_starts_at_admitted(self) -> None:
        receipt = json.loads(
            (FIXTURES / "valid-receipt.json").read_text(encoding="utf-8")
        )
        receipt["writebacks"] = [
            {
                "destination_id": "module-context",
                "scope": "MODULE",
                "durability": "DURABLE",
                "locator": (
                    "skills/controlled-technical-language-harness/"
                    "references/INTENT.md"
                ),
                "mode": "APPEND",
                "content_digest": "sha256:" + "1" * 64,
                "authority_subject": receipt["subject"]["commit_sha"],
                "current_projection": True,
            }
        ]
        with self.assertRaises(PolicyRefusal):
            validate_receipt(receipt, self.contract, self.contract_raw)

    def test_root_write_requires_human_action_and_admitted_subject(self) -> None:
        receipt = json.loads(
            (FIXTURES / "canonical-receipt.json").read_text(encoding="utf-8")
        )
        receipt["human_approval"]["allowed_actions"] = ["PROMOTE_CANONICAL"]
        with self.assertRaisesRegex(PolicyRefusal, "WRITE:root-context"):
            validate_receipt(receipt, self.contract, self.contract_raw)

    def test_caller_flag_is_not_human_approval(self) -> None:
        receipt = json.loads(
            (FIXTURES / "canonical-receipt.json").read_text(encoding="utf-8")
        )
        receipt["human_approval"] = None
        receipt["caller_flags"] = ["--allow-root-override"]
        with self.assertRaises(PolicyRefusal):
            validate_receipt(receipt, self.contract, self.contract_raw)

    def test_terminal_receipt_cannot_keep_current_projection(self) -> None:
        contract = self.contract
        receipt = build_fixture_receipt(
            contract, self.contract_raw, target="CANONICAL"
        )
        receipt["from_state"] = "CANONICAL"
        receipt["to_state"] = "REVOKED"
        receipt["human_approval"]["allowed_actions"] = ["REVOKE_INTENT"]
        receipt["lineage"]["revocation_reason"] = "The admitted intent is unsafe."
        receipt["writebacks"] = [
            {
                "destination_id": "intent-history",
                "scope": "HISTORY",
                "durability": "DURABLE",
                "locator": "docs/intent-history/MI-CTL-EVIDENCE.json",
                "mode": "REVOKE",
                "content_digest": "sha256:" + "8" * 64,
                "authority_subject": "f" * 40,
                "current_projection": True,
            }
        ]
        with self.assertRaisesRegex(PolicyRefusal, "current projection"):
            validate_receipt(receipt, contract, self.contract_raw)

    def test_private_reasoning_key_is_rejected(self) -> None:
        receipt = json.loads(
            (FIXTURES / "valid-receipt.json").read_text(encoding="utf-8")
        )
        receipt["reasoning_trace"] = ["private"]
        with self.assertRaisesRegex(PolicyRefusal, "private reasoning"):
            validate_receipt(receipt, self.contract, self.contract_raw)


class ExitContractTests(unittest.TestCase):
    def test_selftest_kills_all_planted_mutations(self) -> None:
        result = run("selftest")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("25 mutations refused", result.stdout)

    def test_policy_refusal_is_exit_2(self) -> None:
        receipt = json.loads(
            (FIXTURES / "valid-receipt.json").read_text(encoding="utf-8")
        )
        receipt["evidence_fresh"] = False
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "refused.json"
            path.write_text(json.dumps(receipt), encoding="utf-8")
            result = run(
                "receipt",
                str(path),
                "--contract",
                str(FIXTURES / "valid-contract.json"),
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("INTENT PROMOTION RED", result.stderr)

    def test_unreadable_or_unparseable_input_is_exit_64(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            absent = directory_path / "absent.json"
            self.assertEqual(run("contract", str(absent)).returncode, 64)

            broken = directory_path / "broken.json"
            broken.write_text("{not json", encoding="utf-8")
            self.assertEqual(run("contract", str(broken)).returncode, 64)

    def test_missing_cli_input_is_exit_64(self) -> None:
        result = run("contract")
        self.assertEqual(result.returncode, 64)
        self.assertIn("INTENT PROMOTION USAGE", result.stderr)


if __name__ == "__main__":
    unittest.main()
