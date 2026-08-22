#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

MODULE_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = MODULE_ROOT.parents[1]
SCRIPT = MODULE_ROOT / "cadg_pr_admission.py"
POLICY = MODULE_ROOT / "policy.default.json"
STRICT_POLICY = MODULE_ROOT / "policy.strict-material-gate.json"
CHECKER = SKILL_ROOT / "scripts" / "check_cadg_packet.py"
EXAMPLE = SKILL_ROOT / "examples" / "cadg" / "positive-forward-material-change.json"

spec = importlib.util.spec_from_file_location("cadg_pr_admission", SCRIPT)
assert spec and spec.loader
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


def run(*argv: str, cwd: Path, ok: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(list(argv), cwd=cwd, text=True, capture_output=True)
    if ok and result.returncode:
        raise AssertionError((argv, result.stdout, result.stderr))
    return result


class CadgPrAdmissionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="cadg-pr-")
        self.root = Path(self.tmp.name)
        run("git", "init", "-b", "main", cwd=self.root)
        run("git", "config", "user.email", "cadg-test@example.invalid", cwd=self.root)
        run("git", "config", "user.name", "CADG Test", cwd=self.root)
        (self.root / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        run("git", "add", ".", cwd=self.root)
        run("git", "commit", "-m", "base", cwd=self.root)
        self.base = run("git", "rev-parse", "HEAD", cwd=self.root).stdout.strip()
        self.base_tree = run("git", "rev-parse", "HEAD^{tree}", cwd=self.root).stdout.strip()
        run("git", "checkout", "-b", "agent/cadg-example", cwd=self.root)
        (self.root / "ARCHITECTURE.md").write_text("# Architecture\n\nOne writer.\n", encoding="utf-8")
        run("git", "add", ".", cwd=self.root)
        run("git", "commit", "-m", "material code", cwd=self.root)
        self.analyzed = run("git", "rev-parse", "HEAD", cwd=self.root).stdout.strip()
        self.analyzed_tree = run("git", "rev-parse", "HEAD^{tree}", cwd=self.root).stdout.strip()
        manifest, _ = adapter.manifest(self.root, ["ARCHITECTURE.md"], [".agents/cadg/**"])

        packet = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        packet["subject"].update({"repository": "ed3c/example-consumer", "base_commit": self.base,
                                  "base_tree": self.base_tree, "analyzed_commit": self.analyzed,
                                  "analyzed_tree": self.analyzed_tree})
        packet["subject"]["binding"]["code_manifest_digest"] = manifest
        packet["context"]["bound_commit"] = self.analyzed
        packet["context"]["bound_tree"] = self.analyzed_tree
        for source in packet["context"]["sources"]:
            source["revision"] = self.analyzed
        for evidence in packet["evidence"]:
            evidence["subject"].update({"repository": "ed3c/example-consumer", "base_commit": self.base,
                                        "base_tree": self.base_tree, "head_commit": self.analyzed,
                                        "head_tree": self.analyzed_tree, "branch": "agent/cadg-example"})
        packet["pr"].update({"repository": "ed3c/example-consumer", "number": 42,
                             "base_commit": self.base, "head_branch": "agent/cadg-example", "state": "DRAFT"})
        packet["delta"]["paths"] = ["ARCHITECTURE.md"]
        packet["rollback"].update({"commit": self.base, "tree": self.base_tree})
        self.packet = self.root / ".agents/cadg/packets/test.json"
        self.packet.parent.mkdir(parents=True)
        self.packet.write_text(json.dumps(packet, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        run("git", "add", ".", cwd=self.root)
        run("git", "commit", "-m", "CADG metadata", cwd=self.root)
        self.head = run("git", "rev-parse", "HEAD", cwd=self.root).stdout.strip()
        self.head_tree = run("git", "rev-parse", "HEAD^{tree}", cwd=self.root).stdout.strip()
        self.changed = self.root / "changed.txt"
        self.changed.write_text("ARCHITECTURE.md\n.agents/cadg/packets/test.json\n", encoding="utf-8")
        self.receipt = self.root / "receipt.json"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def argv(self, include_packet: bool = True, *, policy: Path = POLICY,
             boundary: str | None = None) -> list[str]:
        values = ["python3", str(SCRIPT), "--repo-root", str(self.root), "--policy", str(policy),
                  "--changed-files", str(self.changed), "--checker", str(CHECKER)]
        if include_packet:
            values += ["--packet", str(self.packet)]
        if boundary:
            values += ["--transition-boundary", boundary]
        values += ["--repository", "ed3c/example-consumer", "--pr-number", "42",
                   "--base-commit", self.base, "--base-tree", self.base_tree,
                   "--head-commit", self.head, "--head-tree", self.head_tree,
                   "--head-branch", "agent/cadg-example", "--human-admission-ref", "HUMAN-DESIGN-42",
                   "--receipt-out", str(self.receipt)]
        return values

    def test_positive_exact_pr_receipt_keeps_v1_shape(self) -> None:
        result = run(*self.argv(), cwd=self.root)
        self.assertIn("CADG-PR-GREEN", result.stdout)
        self.assertIn("mode=OBSERVE", result.stdout)
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        self.assertEqual(receipt["cadg"], "PASS")
        self.assertEqual(receipt["code"], "NOT_EXERCISED")
        self.assertEqual(receipt["shadow"], "NOT_EXERCISED")
        self.assertNotIn("operating_mode", receipt)
        self.assertNotIn("transition_boundary", receipt)

    def test_observe_material_change_without_packet_continues(self) -> None:
        result = run(*self.argv(False), cwd=self.root)
        self.assertEqual(result.returncode, 0)
        self.assertIn("CADG-PR-OBSERVE", result.stdout)
        self.assertIn("PARTIAL_CAUSAL_CHAIN", result.stdout)

    def test_warn_material_change_without_packet_warns_not_blocks(self) -> None:
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        policy["operating_mode"] = "WARN"
        warn_policy = self.root / "warn-policy.json"
        warn_policy.write_text(json.dumps(policy), encoding="utf-8")
        result = run(*self.argv(False, policy=warn_policy), cwd=self.root)
        self.assertEqual(result.returncode, 0)
        self.assertIn("CADG-PR-WARN", result.stderr)

    def test_gate_blocks_only_named_transition(self) -> None:
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        policy["operating_mode"] = "GATE"
        gate_policy = self.root / "gate-policy.json"
        gate_policy.write_text(json.dumps(policy), encoding="utf-8")
        reversible = run(*self.argv(False, policy=gate_policy, boundary="PR_IMPLEMENTATION_REVERSIBLE"), cwd=self.root)
        self.assertEqual(reversible.returncode, 0)
        self.assertIn("GATE-NOT-AT-BOUNDARY", reversible.stdout)
        irreversible = run(*self.argv(False, policy=gate_policy, boundary="MIGRATION_CONTRACTION"), cwd=self.root, ok=False)
        self.assertEqual(irreversible.returncode, 2)
        self.assertIn("CADG018", irreversible.stderr)

    def test_strict_profile_preserves_old_missing_packet_failure(self) -> None:
        result = run(*self.argv(False, policy=STRICT_POLICY), cwd=self.root, ok=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("CADG018", result.stderr)

    def test_stale_manifest_maps_to_fast_iteration_subject_blocker(self) -> None:
        (self.root / "ARCHITECTURE.md").write_text("# Architecture\nchanged again\n", encoding="utf-8")
        result = run(*self.argv(), cwd=self.root, ok=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("CADG-FI-001", result.stderr)


if __name__ == "__main__":
    unittest.main()
