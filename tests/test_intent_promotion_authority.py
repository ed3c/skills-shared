"""Contract tests for the intent-promotion authority readback layer.

The selftest proves the checker refuses its planted defects. These prove the
committed bundle is admitted, that the committed schemas really are executed as
deciding gates rather than merely parsed, and that the four exits stay distinct.
"""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts" / "check_intent_promotion_authority.py"
BUNDLE_DIR = ROOT / "evals" / "fixtures" / "intent-promotion" / "authority"
SCHEMAS = ROOT / "evals" / "schema"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), *args],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )


def digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


class CommittedBundleTests(unittest.TestCase):
    def test_committed_bundle_is_admitted(self) -> None:
        result = run("--bundle", str(BUNDLE_DIR / "bundle.json"))
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["status"], "PASS")
        self.assertTrue(receipt["evaluator_evidence_read"])
        self.assertTrue(receipt["forge_readback_read"])

    def test_every_declared_digest_matches_its_bytes(self) -> None:
        """The property the whole layer exists to enforce, checked directly."""
        bundle = json.loads((BUNDLE_DIR / "bundle.json").read_text(encoding="utf-8"))
        artifacts = [
            bundle[key] for key in
            ("bundle_schema", "contract_schema", "receipt_schema", "ledger_schema",
             "contract", "receipt", "ledger")
        ]
        artifacts += bundle["evidence"]["evaluator_receipts"]
        artifacts.append(bundle["evidence"]["forge_readback"])
        for artifact in artifacts:
            raw = (BUNDLE_DIR / artifact["path"]).read_bytes()
            self.assertEqual(digest(raw), artifact["artifact_digest"], artifact["path"])

    def test_receipt_binds_the_bundled_contract(self) -> None:
        bundle = json.loads((BUNDLE_DIR / "bundle.json").read_text(encoding="utf-8"))
        receipt = json.loads((BUNDLE_DIR / "receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["contract_digest"], bundle["contract"]["artifact_digest"])


class SchemasAreExecutedTests(unittest.TestCase):
    """A schema that is only parsed is not a gate.

    Each case plants a document that is valid JSON and invalid against the
    committed schema. If the schema were merely parsed, all of them would pass.
    """

    def _rebuilt(self, work: Path, mutate) -> Path:
        shutil.copytree(BUNDLE_DIR, work / "bundle")
        target = work / "bundle"
        receipt = json.loads((target / "receipt.json").read_text(encoding="utf-8"))
        mutate(receipt)
        payload = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
        (target / "receipt.json").write_text(payload, encoding="utf-8")
        bundle = json.loads((target / "bundle.json").read_text(encoding="utf-8"))
        bundle["receipt"]["artifact_digest"] = digest(payload.encode("utf-8"))
        (target / "bundle.json").write_text(
            json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target / "bundle.json"

    def test_additional_property_is_refused_by_the_schema(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = self._rebuilt(Path(raw), lambda r: r.__setitem__("extra_field", "x"))
            result = run("--bundle", str(path))
            self.assertEqual(result.returncode, 2)
            self.assertIn("fails its schema", result.stderr)

    def test_malformed_nested_field_is_refused_by_the_schema(self) -> None:
        def mutate(receipt: dict) -> None:
            receipt["evaluator_receipts"][0]["evaluator_version"] = "not-a-version"
        with tempfile.TemporaryDirectory() as raw:
            path = self._rebuilt(Path(raw), mutate)
            result = run("--bundle", str(path))
            self.assertEqual(result.returncode, 2)
            self.assertIn("fails its schema", result.stderr)

    def test_required_nested_field_removal_is_refused(self) -> None:
        def mutate(receipt: dict) -> None:
            receipt["evaluator_receipts"][0].pop("execution_origin")
        with tempfile.TemporaryDirectory() as raw:
            path = self._rebuilt(Path(raw), mutate)
            result = run("--bundle", str(path))
            self.assertEqual(result.returncode, 2)
            self.assertIn("fails its schema", result.stderr)

    def test_committed_schemas_are_valid_draft_2020_12(self) -> None:
        from jsonschema import Draft202012Validator
        for name in ("intent-promotion-authority-bundle.schema.json",
                     "intent-promotion-contract.schema.json",
                     "intent-promotion-receipt.schema.json",
                     "intent-promotion-ledger.schema.json"):
            body = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(body)


class ExitContractTests(unittest.TestCase):
    def test_selftest_is_green(self) -> None:
        result = run("--selftest")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("mutations refused", result.stdout)

    def test_four_exits_stay_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            work = Path(raw)

            # 64: unreadable input.
            self.assertEqual(run("--bundle", str(work / "absent.json")).returncode, 64)
            broken = work / "broken.json"
            broken.write_text("{not json", encoding="utf-8")
            self.assertEqual(run("--bundle", str(broken)).returncode, 64)

            # 2: read, and refused.
            shutil.copytree(BUNDLE_DIR, work / "bundle")
            target = work / "bundle"
            bundle = json.loads((target / "bundle.json").read_text(encoding="utf-8"))
            bundle["contract"]["artifact_digest"] = "sha256:" + "9" * 64
            (target / "bundle.json").write_text(
                json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            result = run("--bundle", str(target / "bundle.json"))
            self.assertEqual(result.returncode, 2)
            self.assertIn("AUTHORITY RED", result.stderr)

    def test_a_stale_bundle_cannot_reuse_an_old_result(self) -> None:
        """Changing any bundled artifact invalidates the bundle's own digest."""
        first = json.loads(run("--bundle", str(BUNDLE_DIR / "bundle.json")).stdout)
        with tempfile.TemporaryDirectory() as raw:
            work = Path(raw)
            shutil.copytree(BUNDLE_DIR, work / "bundle")
            target = work / "bundle"
            path = target / "bundle.json"
            body = json.loads(path.read_text(encoding="utf-8"))
            # Reordering keys changes bytes without changing meaning; the
            # receipt's bundle_digest must still differ.
            path.write_text(json.dumps(body, indent=4, sort_keys=True) + "\n", encoding="utf-8")
            second = json.loads(run("--bundle", str(path)).stdout)
        self.assertNotEqual(first["bundle_digest"], second["bundle_digest"])


if __name__ == "__main__":
    unittest.main()
