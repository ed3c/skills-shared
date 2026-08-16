from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = SKILL_ROOT / "scripts" / "repository_control_plane.py"
PROFILE = SKILL_ROOT / "references" / "repository-control-plane.default.json"
REGISTRY = SKILL_ROOT.parents[1] / "registry.json"
RUNTIME_COMMIT = "a" * 40
CANONICAL_COMMIT = "b" * 40
CONTENT_DIGEST = "c" * 64


class RepositoryControlPlaneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "consumer"
        self.root.mkdir()
        subprocess.run(
            ["git", "init", "-q", str(self.root)],
            check=True,
            text=True,
            capture_output=True,
        )

    def run_tool(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--profile", str(PROFILE), *arguments],
            text=True,
            capture_output=True,
            check=False,
        )

    def attach(self) -> subprocess.CompletedProcess[str]:
        return self.run_tool(
            "attach",
            "--target-root",
            str(self.root),
            "--consumer-repository-id",
            "ed3c/example",
            "--runtime-env-commit",
            RUNTIME_COMMIT,
            "--apply",
        )

    def write_generated_binding(self) -> Path:
        requirements = self.root / ".agents" / "shared-skills.requirements.json"
        profile = json.loads(PROFILE.read_text(encoding="utf-8"))
        binding = {
            "schema": "shared-skills/consumer-binding/v1",
            "binding": profile["binding"],
            "registry_sha256": "d" * 64,
            "requirements_sha256": hashlib.sha256(requirements.read_bytes()).hexdigest(),
            "repo_owned": [],
            "skills": [
                {
                    "name": name,
                    "content_sha256": CONTENT_DIGEST,
                    "entrypoint": f"skills/{name}/SKILL.md",
                }
                for name in sorted(profile["selected_skills"])
            ],
            "source": {
                "commit": CANONICAL_COMMIT,
                "repository": profile["canonical"]["url"],
                "tree": "e" * 40,
            },
            "surfaces": profile["projection"]["surfaces"],
        }
        binding["content_sha256"] = hashlib.sha256(
            json.dumps(
                binding,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        path = self.root / profile["projection"]["binding_path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(binding, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def test_profile_is_valid_and_names_exact_chain(self) -> None:
        result = self.run_tool("profile-check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS skills-shared-default", result.stdout)
        profile = json.loads(PROFILE.read_text(encoding="utf-8"))
        self.assertEqual(
            profile["selected_skills"],
            [item["skill"] for item in profile["controller_chain"]],
        )
        self.assertEqual(profile["runtime"]["git_town"]["scope"], "user")
        self.assertEqual(profile["runtime"]["forgejo"]["scope"], "host")
        self.assertFalse(profile["authority"]["skill_body_copy"])

    def test_profile_selected_skills_are_admitted_once_in_registry(self) -> None:
        profile = json.loads(PROFILE.read_text(encoding="utf-8"))
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        shared = [item["name"] for item in registry["shared"]]
        self.assertEqual(len(shared), len(set(shared)))
        self.assertEqual(
            set(profile["selected_skills"]) - set(shared),
            set(),
            "a selected central Skill cannot be synchronized until registry admission exists",
        )
        self.assertIn("procedural-shadow-runtime", shared)
        self.assertIn("agentic-tech-lead-orchestration", shared)

    def test_attach_is_dry_run_by_default_and_apply_is_idempotent(self) -> None:
        dry = self.run_tool(
            "attach",
            "--target-root",
            str(self.root),
            "--consumer-repository-id",
            "ed3c/example",
            "--runtime-env-commit",
            RUNTIME_COMMIT,
        )
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertIn("WOULD-CREATE .agents/shared-skills.requirements.json", dry.stdout)
        self.assertFalse((self.root / ".agents").exists())

        applied = self.attach()
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertIn("CREATED .agents/repository-control-plane.json", applied.stdout)
        requirements = json.loads(
            (self.root / ".agents" / "shared-skills.requirements.json").read_text(
                encoding="utf-8"
            )
        )
        profile = json.loads(PROFILE.read_text(encoding="utf-8"))
        self.assertEqual(requirements["shared"], profile["selected_skills"])
        self.assertFalse((self.root / ".agents" / "skills").exists())

        second = self.attach()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(second.stdout.count("UNCHANGED"), 2)

    def test_attach_check_detects_drift_without_rewriting(self) -> None:
        self.assertEqual(self.attach().returncode, 0)
        requirements = self.root / ".agents" / "shared-skills.requirements.json"
        original = requirements.read_text(encoding="utf-8")
        requirements.write_text("{}\n", encoding="utf-8")
        result = self.run_tool(
            "attach",
            "--target-root",
            str(self.root),
            "--consumer-repository-id",
            "ed3c/example",
            "--runtime-env-commit",
            RUNTIME_COMMIT,
            "--check",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("DRIFT .agents/shared-skills.requirements.json", result.stdout)
        self.assertEqual(requirements.read_text(encoding="utf-8"), "{}\n")
        requirements.write_text(original, encoding="utf-8")

    def test_attach_rejects_projection_symlink_escape(self) -> None:
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (self.root / ".agents").symlink_to(outside, target_is_directory=True)
        result = self.attach()
        self.assertEqual(result.returncode, 2)
        self.assertIn("symlink component .agents", result.stderr)
        self.assertEqual(list(outside.iterdir()), [])

    def test_nested_target_root_is_rejected(self) -> None:
        nested = self.root / "nested"
        nested.mkdir()
        result = self.run_tool(
            "attach",
            "--target-root",
            str(nested),
            "--consumer-repository-id",
            "ed3c/example",
            "--runtime-env-commit",
            RUNTIME_COMMIT,
            "--apply",
        )
        self.assertEqual(result.returncode, 64)
        self.assertIn("must equal the Git worktree root", result.stderr)

    def test_attach_rejects_mutable_runtime_identity(self) -> None:
        result = self.run_tool(
            "attach",
            "--target-root",
            str(self.root),
            "--consumer-repository-id",
            "ed3c/example",
            "--runtime-env-commit",
            "main",
            "--apply",
        )
        self.assertEqual(result.returncode, 64)
        self.assertIn("exact 40- or 64-hex commit", result.stderr)
        self.assertFalse((self.root / ".agents").exists())

    def test_verify_keeps_absent_binding_distinct_from_pass(self) -> None:
        self.assertEqual(self.attach().returncode, 0)
        result = self.run_tool("verify", "--target-root", str(self.root))
        self.assertEqual(result.returncode, 3)
        self.assertIn("NOT_EXERCISED BINDING_ABSENT", result.stderr)

    def test_verify_accepts_thin_binding_and_rejects_body_shadow(self) -> None:
        self.assertEqual(self.attach().returncode, 0)
        self.write_generated_binding()
        clean = self.run_tool("verify", "--target-root", str(self.root))
        self.assertEqual(clean.returncode, 0, clean.stderr)
        self.assertIn("structurally closed", clean.stdout)

        shadow = self.root / ".agents" / "skills" / "agentic-tech-lead-orchestration"
        shadow.mkdir(parents=True)
        (shadow / "SKILL.md").write_text("---\nname: agentic-tech-lead-orchestration\n---\n", encoding="utf-8")
        (shadow / "copied-body.md").write_text("forbidden copy\n", encoding="utf-8")
        blocked = self.run_tool("verify", "--target-root", str(self.root))
        self.assertEqual(blocked.returncode, 2)
        self.assertIn("SHADOWED agentic-tech-lead-orchestration", blocked.stderr)

    def test_verify_rejects_single_file_body_copy_and_dangling_symlink(self) -> None:
        self.assertEqual(self.attach().returncode, 0)
        self.write_generated_binding()
        copied = self.root / ".agents" / "skills" / "agentic-tech-lead-orchestration"
        copied.mkdir(parents=True)
        (copied / "SKILL.md").write_text(
            "---\nname: agentic-tech-lead-orchestration\n---\n# copied canonical body\n",
            encoding="utf-8",
        )
        body = self.run_tool("verify", "--target-root", str(self.root))
        self.assertEqual(body.returncode, 2)
        self.assertIn("forwarder markers missing", body.stderr)

        (copied / "SKILL.md").unlink()
        copied.rmdir()
        copied.symlink_to(self.root / "does-not-exist", target_is_directory=True)
        dangling = self.run_tool("verify", "--target-root", str(self.root))
        self.assertEqual(dangling.returncode, 2)
        self.assertIn("dangling or cyclic symlink", dangling.stderr)

    def test_verify_rejects_forged_binding_source_even_with_recomputed_digest(self) -> None:
        self.assertEqual(self.attach().returncode, 0)
        binding_path = self.write_generated_binding()
        binding = json.loads(binding_path.read_text(encoding="utf-8"))
        binding["source"]["repository"] = "https://example.invalid/skills-shared"
        unsigned = dict(binding)
        unsigned.pop("content_sha256")
        binding["content_sha256"] = hashlib.sha256(
            json.dumps(
                unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        binding_path.write_text(
            json.dumps(binding, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        result = self.run_tool("verify", "--target-root", str(self.root))
        self.assertEqual(result.returncode, 2)
        self.assertIn("canonical repository mismatch", result.stderr)

    def test_single_skill_forwarder_is_not_a_body_copy(self) -> None:
        self.assertEqual(self.attach().returncode, 0)
        self.write_generated_binding()
        forwarder = self.root / ".claude" / "skills" / "procedural-shadow-runtime"
        forwarder.mkdir(parents=True)
        (forwarder / "SKILL.md").write_text(
            "---\nname: procedural-shadow-runtime\ndisable-model-invocation: true\n---\n"
            "Load the canonical user-surface Skill with $ARGUMENTS.\n",
            encoding="utf-8",
        )
        result = self.run_tool("verify", "--target-root", str(self.root))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_verify_rejects_requirements_or_binding_closure_drift(self) -> None:
        self.assertEqual(self.attach().returncode, 0)
        binding_path = self.write_generated_binding()
        requirements_path = self.root / ".agents" / "shared-skills.requirements.json"
        requirements = json.loads(requirements_path.read_text(encoding="utf-8"))
        requirements["shared"].remove("dual-forge-repository-loop")
        requirements_path.write_text(
            json.dumps(requirements, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        result = self.run_tool("verify", "--target-root", str(self.root))
        self.assertEqual(result.returncode, 2)
        self.assertIn("consumer requirements drift", result.stderr)

        self.assertEqual(self.attach().returncode, 0)
        binding = json.loads(binding_path.read_text(encoding="utf-8"))
        binding["skills"] = binding["skills"][:-1]
        binding["requirements_sha256"] = hashlib.sha256(
            requirements_path.read_bytes()
        ).hexdigest()
        binding_path.write_text(
            json.dumps(binding, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        result = self.run_tool("verify", "--target-root", str(self.root))
        self.assertEqual(result.returncode, 2)
        self.assertIn("selected Skill closure/order mismatch", result.stderr)

    def test_monitor_plan_routes_only_open_issues_and_preserves_blockers(self) -> None:
        self.assertEqual(self.attach().returncode, 0)
        self.write_generated_binding()
        issues_path = self.root / "issues.json"
        issues_path.write_text(
            json.dumps(
                [
                    {"number": 7, "title": "closed", "state": "closed"},
                    {"number": 2, "title": "ready", "state": "open", "labels": []},
                    {
                        "number": 4,
                        "title": "blocked",
                        "state": "open",
                        "labels": [{"name": "blocked"}],
                        "blocked_by": [2],
                    },
                    {
                        "number": 3,
                        "title": "working",
                        "state": "open",
                        "labels": ["status:in-progress"],
                    },
                ]
            ),
            encoding="utf-8",
        )
        result = self.run_tool(
            "monitor-plan",
            "--target-root",
            str(self.root),
            "--issues",
            str(issues_path),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertEqual([item["number"] for item in plan["issues"]], [2, 3, 4])
        self.assertEqual([item["routing_state"] for item in plan["issues"]], ["READY", "IN_PROGRESS", "BLOCKED"])
        self.assertEqual(plan["issues"][2]["blocked_by"], [2])
        self.assertTrue(all(item["execution_state"] == "NOT_EXERCISED" for item in plan["issues"]))
        self.assertFalse(plan["authority"]["automatic_merge"])
        self.assertEqual(
            [item["skill"] for item in plan["issues"][0]["controller_chain"]],
            json.loads(PROFILE.read_text(encoding="utf-8"))["selected_skills"],
        )

    def test_monitor_requires_a_structurally_closed_attachment(self) -> None:
        self.assertEqual(self.attach().returncode, 0)
        issues_path = self.root / "issues.json"
        issues_path.write_text(
            json.dumps([{"number": 1, "title": "open", "state": "open"}]),
            encoding="utf-8",
        )
        result = self.run_tool(
            "monitor-plan",
            "--target-root",
            str(self.root),
            "--issues",
            str(issues_path),
        )
        self.assertEqual(result.returncode, 3)
        self.assertIn("BINDING_ABSENT", result.stderr)

    def test_monitor_rejects_tampered_authority_before_planning(self) -> None:
        self.assertEqual(self.attach().returncode, 0)
        self.write_generated_binding()
        control_path = self.root / ".agents" / "repository-control-plane.json"
        control = json.loads(control_path.read_text(encoding="utf-8"))
        control["authority"]["automatic_merge"] = True
        control_path.write_text(
            json.dumps(control, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        issues_path = self.root / "issues.json"
        issues_path.write_text(
            json.dumps([{"number": 1, "title": "open", "state": "open"}]),
            encoding="utf-8",
        )
        result = self.run_tool(
            "monitor-plan",
            "--target-root",
            str(self.root),
            "--issues",
            str(issues_path),
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("consumer control-plane binding drift", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_monitor_rejects_cycles_and_ignores_closed_blockers(self) -> None:
        self.assertEqual(self.attach().returncode, 0)
        self.write_generated_binding()
        issues_path = self.root / "issues.json"
        issues_path.write_text(
            json.dumps(
                [
                    {"number": 1, "title": "one", "state": "open", "blocked_by": [2]},
                    {"number": 2, "title": "two", "state": "open", "blocked_by": [1]},
                ]
            ),
            encoding="utf-8",
        )
        cycle = self.run_tool(
            "monitor-plan",
            "--target-root",
            str(self.root),
            "--issues",
            str(issues_path),
        )
        self.assertEqual(cycle.returncode, 64)
        self.assertIn("dependency cycle", cycle.stderr)

        issues_path.write_text(
            json.dumps(
                [
                    {"number": 1, "title": "one", "state": "open", "blocked_by": [2]},
                    {"number": 2, "title": "done", "state": "closed"},
                ]
            ),
            encoding="utf-8",
        )
        resolved = self.run_tool(
            "monitor-plan",
            "--target-root",
            str(self.root),
            "--issues",
            str(issues_path),
        )
        self.assertEqual(resolved.returncode, 0, resolved.stderr)
        plan = json.loads(resolved.stdout)
        self.assertEqual(plan["issues"][0]["routing_state"], "READY")
        self.assertEqual(plan["issues"][0]["blocked_by"], [])

    def test_monitor_no_open_work_is_not_reported_as_pass(self) -> None:
        self.assertEqual(self.attach().returncode, 0)
        self.write_generated_binding()
        issues_path = self.root / "issues.json"
        issues_path.write_text(
            json.dumps([{"number": 1, "title": "done", "state": "closed"}]),
            encoding="utf-8",
        )
        result = self.run_tool(
            "monitor-plan",
            "--target-root",
            str(self.root),
            "--issues",
            str(issues_path),
        )
        self.assertEqual(result.returncode, 3)
        self.assertEqual(json.loads(result.stdout)["issues"], [])

    def test_monitor_rejects_duplicate_issue_identity(self) -> None:
        self.assertEqual(self.attach().returncode, 0)
        self.write_generated_binding()
        issues_path = self.root / "issues.json"
        issues_path.write_text(
            json.dumps(
                [
                    {"number": 1, "title": "one", "state": "open"},
                    {"number": 1, "title": "duplicate", "state": "open"},
                ]
            ),
            encoding="utf-8",
        )
        result = self.run_tool(
            "monitor-plan",
            "--target-root",
            str(self.root),
            "--issues",
            str(issues_path),
        )
        self.assertEqual(result.returncode, 64)
        self.assertIn("duplicate issue number", result.stderr)

    def test_profile_mutation_runtime_entrypoint_fails_closed(self) -> None:
        profile = json.loads(PROFILE.read_text(encoding="utf-8"))
        profile["runtime"]["git_town"]["setup_entrypoint"] = "arbitrary.install"
        mutated = self.root / "mutated-runtime-profile.json"
        mutated.write_text(json.dumps(profile), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--profile", str(mutated), "profile-check"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 64)
        self.assertIn("runtime.git_town.setup_entrypoint mismatch", result.stderr)

    def test_profile_mutation_missing_shadow_phase_fails_closed(self) -> None:
        profile = json.loads(PROFILE.read_text(encoding="utf-8"))
        profile["selected_skills"].remove("procedural-shadow-runtime")
        profile["controller_chain"] = profile["controller_chain"][0:1] + profile["controller_chain"][2:]
        mutated = self.root / "mutated-profile.json"
        mutated.write_text(json.dumps(profile), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--profile", str(mutated), "profile-check"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 64)
        self.assertIn("canonical six-phase chain", result.stderr)


if __name__ == "__main__":
    unittest.main()
