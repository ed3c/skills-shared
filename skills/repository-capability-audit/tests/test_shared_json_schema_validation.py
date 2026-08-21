from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
HELPER = SCRIPTS / "_json_schema_validation.py"

spec = importlib.util.spec_from_file_location("rca_json_schema_validation", HELPER)
assert spec and spec.loader
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class SharedJsonSchemaValidationTests(unittest.TestCase):
    def test_load_and_schema_format_match_frozen_behavior(self) -> None:
        validator = helper.require_draft202012_validator("TEST")
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.json"
            path.write_text(json.dumps({"count": "wrong"}), encoding="utf-8")
            document = helper.load_json_document(path, prefix="TEST", invalid_exit=64)
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {"count": {"type": "integer"}},
            "required": ["count"],
        }
        errors = helper.schema_errors(document, schema, validator)
        self.assertEqual(1, len(errors))
        self.assertTrue(errors[0].startswith("schema-invalid at count:"), errors)

    def test_missing_input_preserves_prefix_and_exit_code(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                helper.load_json_document(
                    Path("/definitely/not/present/rca.json"),
                    prefix="CANARY-RECEIPT",
                    invalid_exit=64,
                )
        self.assertEqual(64, raised.exception.code)
        self.assertIn("CANARY-RECEIPT-INVALID absent-input:", stderr.getvalue())

    def test_callers_no_longer_own_duplicate_transport_truth(self) -> None:
        for filename in ("check_canary_receipt.py", "check_held_out_corpus.py"):
            text = (SCRIPTS / filename).read_text(encoding="utf-8")
            self.assertIn("from _json_schema_validation import", text, filename)
            self.assertNotIn("def load_json(", text, filename)
            self.assertNotIn("def validate_schema(", text, filename)
            self.assertNotIn("json.loads(", text, filename)


if __name__ == "__main__":
    unittest.main()
