#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path

SKILL=Path(__file__).resolve().parents[2]
SCRIPT=SKILL/"scripts/check_repository_portfolio_prompt_pack.py"
spec=importlib.util.spec_from_file_location("gate",SCRIPT)
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
MANIFEST=SKILL/"references/repository-portfolio-control/prompt-manifest.json"

class Tests(unittest.TestCase):
    def load(self):return json.loads(MANIFEST.read_text())
    def test_positive(self):self.assertEqual(gate.validate(self.load()),[])
    def test_coordinator_drift(self):
        value=self.load();value["required_coordinator_instruction"]="Use agents"
        self.assertTrue(any("coordinator instruction" in error for error in gate.validate(value)))
    def test_missing_role(self):
        value=self.load();value["required_roles"].append("missing-role")
        self.assertTrue(any("role absent" in error for error in gate.validate(value)))
    def test_authority_widening(self):
        path=SKILL/"references/repository-portfolio-control/codex-agent-templates.md"
        original=path.read_text()
        try:
            path.write_text(original.replace('sandbox_mode = "read-only"','sandbox_mode = "workspace-write"',1))
            self.assertTrue(any("agent count drift" in error for error in gate.validate(self.load())))
        finally:path.write_text(original)

if __name__=="__main__":unittest.main(verbosity=2)
