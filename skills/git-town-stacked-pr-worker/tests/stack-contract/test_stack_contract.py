from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
SKILL_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = SKILL_ROOT / "scripts" / "check_stack_contract.py"
SPEC = importlib.util.spec_from_file_location("check_stack_contract", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
FIXTURE = TEST_DIR / "fixtures" / "valid-stack.json"


class StackContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.valid = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_positive_stack_is_green(self) -> None:
        self.assertEqual(MODULE.validate_stack(self.valid), [])

    def test_wrong_pr_base_turns_red(self) -> None:
        mutated = copy.deepcopy(self.valid)
        mutated["branches"][1]["pr_base"] = "main"
        self.assertIn(
            "ibc/02-git-town-stack-binding PR base does not equal declared parent branch",
            MODULE.validate_stack(mutated),
        )

    def test_stale_parent_turns_red(self) -> None:
        mutated = copy.deepcopy(self.valid)
        mutated["branches"][1]["behind_by"] = 2
        self.assertIn(
            "ibc/02-git-town-stack-binding is stale: behind_by must be 0",
            MODULE.validate_stack(mutated),
        )

    def test_wrong_merge_base_turns_red(self) -> None:
        mutated = copy.deepcopy(self.valid)
        mutated["branches"][1]["merge_base_sha"] = "f" * 40
        self.assertIn(
            "ibc/02-git-town-stack-binding merge base is not the exact declared parent head",
            MODULE.validate_stack(mutated),
        )

    def test_stale_receipt_turns_red(self) -> None:
        mutated = copy.deepcopy(self.valid)
        mutated["branches"][1]["evidence_subject_sha"] = "f" * 40
        self.assertIn(
            "ibc/02-git-town-stack-binding evidence subject does not equal the exact branch head",
            MODULE.validate_stack(mutated),
        )

    def test_fake_serial_child_turns_red(self) -> None:
        mutated = copy.deepcopy(self.valid)
        branch = mutated["branches"][1]
        branch["consumes_contracts"] = []
        branch["consumes_paths"] = []
        branch["dependency_reason"] = "Prose is not proof of a dependency."
        self.assertIn(
            "ibc/02-git-town-stack-binding is fake serialization: child has no consumed contract or byte dependency",
            MODULE.validate_stack(mutated),
        )

    def test_child_missing_parent_dependency_turns_red(self) -> None:
        mutated = copy.deepcopy(self.valid)
        mutated["branches"][1]["depends_on_branches"] = []
        self.assertIn(
            "ibc/02-git-town-stack-binding child dependency list must include its parent branch",
            MODULE.validate_stack(mutated),
        )

    def test_sibling_dependency_turns_red(self) -> None:
        mutated = copy.deepcopy(self.valid)
        mutated["branches"][2]["depends_on_branches"].append("ibc/04-forgejo-delivery-adapter")
        errors = MODULE.validate_stack(mutated)
        self.assertTrue(any("sibling depends on another sibling" in item for item in errors))

    def test_sibling_path_overlap_turns_red(self) -> None:
        mutated = copy.deepcopy(self.valid)
        mutated["branches"][3]["allowed_paths"] = ["skills/knowledge-continuity/references"]
        errors = MODULE.validate_stack(mutated)
        self.assertTrue(any("sibling path lease overlap" in item for item in errors))

    def test_convergence_created_early_turns_red(self) -> None:
        mutated = copy.deepcopy(self.valid)
        mutated["convergence_plan"]["state"] = "CREATED"
        self.assertIn(
            "convergence branch must remain NOT_CREATED until all prerequisites are ADMITTED",
            MODULE.validate_stack(mutated),
        )

    def test_missing_human_boundary_turns_red(self) -> None:
        mutated = copy.deepcopy(self.valid)
        mutated["human_owned_operations"].remove("merge_or_ship")
        errors = MODULE.validate_stack(mutated)
        self.assertTrue(any("merge_or_ship" in item for item in errors))

    def test_ancestry_cycle_turns_red(self) -> None:
        mutated = copy.deepcopy(self.valid)
        mutated["branches"][0]["parent_branch"] = "ibc/02-git-town-stack-binding"
        mutated["branches"][0]["pr_base"] = "ibc/02-git-town-stack-binding"
        errors = MODULE.validate_stack(mutated)
        self.assertTrue(any("ancestry cycle" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
