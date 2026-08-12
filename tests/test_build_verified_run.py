from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_verified_run.py"


class BuildVerifiedRunTests(unittest.TestCase):
    def test_repetition_stays_repetition_and_verifier_owns_outcome(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); executor = root / "executor.json"; receipt = root / "receipt.json"; routing = root / "routing.json"; out = root / "run.json"
            executor.write_text(json.dumps({
                "schema_version":"skill-eval-executor-evidence/v1","run_id":"run-12345678","case_id":"case-a","condition":"candidate_skill","skill_sha":"a"*40,
                "sampling":{"repetition_index":2,"seed_controlled":False,"model_seed":None},
                "model":{"provider":"openai","name":"m"},"harness":{"name":"skill-up","version":"v"},
                "outcome":{"passed":True,"duration_ms":1000,"input_tokens":10,"output_tokens":5}
            }))
            receipt.write_text(json.dumps({"schema_version":"skill-eval-verifier-receipt/v1","run_id":"run-12345678","case_id":"case-a","authority":"deterministic","passed":False}))
            routing.write_text(json.dumps({"case_id":"case-a","decision":"invoke","selected_skill":"demo"}))
            proc = subprocess.run(["python3",str(SCRIPT),"--executor-evidence",str(executor),"--verifier-receipt",str(receipt),"--routing-evidence",str(routing),"--output",str(out)],text=True,capture_output=True)
            self.assertEqual(proc.returncode,0,proc.stderr)
            value=json.loads(out.read_text())
            self.assertEqual(value["sampling"],{"kind":"repetition","index":2,"seed":None})
            self.assertFalse(value["outcome"]["passed"])
            self.assertEqual(value["outcome"]["verifier"],"deterministic-script")
            self.assertEqual(value["metrics"]["wall_seconds"],1.0)

    def test_mismatched_receipt_identity_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); executor=root/"executor.json"; receipt=root/"receipt.json"; routing=root/"routing.json"; out=root/"run.json"
            executor.write_text(json.dumps({"schema_version":"skill-eval-executor-evidence/v1","run_id":"run-a1234567","case_id":"case-a","condition":"candidate_skill","sampling":{"repetition_index":1,"seed_controlled":False,"model_seed":None}}))
            receipt.write_text(json.dumps({"schema_version":"skill-eval-verifier-receipt/v1","run_id":"run-b1234567","case_id":"case-a","authority":"deterministic"}))
            routing.write_text(json.dumps({"case_id":"case-a"}))
            proc=subprocess.run(["python3",str(SCRIPT),"--executor-evidence",str(executor),"--verifier-receipt",str(receipt),"--routing-evidence",str(routing),"--output",str(out)],text=True,capture_output=True)
            self.assertNotEqual(proc.returncode,0)
            self.assertIn("identity mismatch",proc.stderr)


if __name__ == "__main__": unittest.main()
