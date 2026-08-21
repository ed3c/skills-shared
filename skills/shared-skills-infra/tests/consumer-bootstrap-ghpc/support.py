#!/usr/bin/env python3
"""Hermetic fixture builder for the github-portfolio-control consumer bootstrap.

Builds a fully synthetic `shared` world (its own scripts copy, its own five
fixture Skills, its own github-portfolio-control canonical body, and its own
not-yet-merged "candidate" commit carrying seven Codex agent templates) so the
suite never depends on this real checkout's history or network access, and so
STALE_PIN can be planted and killed deterministically.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_NAMES = (
    "consumer_bootstrap_common.py", "consumer_bootstrap_receipt.py",
    "consumer_bootstrap_routes.py", "consumer_bootstrap_ghpc.py",
)
SKILLS = [
    "agentic-tech-lead-orchestration", "git-town-stacked-pr-worker",
    "github-delivery-loop", "procedural-shadow-runtime", "shared-skills-infra",
]
CANDIDATE_SOURCE_PATH = "skills/agentic-tech-lead-orchestration/references/codex-agents"
CODEX_ROLES = (
    "portfolio-explorer", "acceptance-adversary", "dependency-auditor",
    "runtime-admission-auditor", "implementation-worker",
    "consolidation-verifier", "release-auditor",
)


def run(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if check and result.returncode:
        raise AssertionError(f"command failed {args}:\n{result.stdout}\n{result.stderr}")
    return result


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def init_git(root: Path, remote: str | None = None) -> None:
    root.mkdir(parents=True, exist_ok=True)
    run("git", "init", "-b", "main", cwd=root)
    run("git", "config", "user.name", "Test", cwd=root)
    run("git", "config", "user.email", "test@example.com", cwd=root)
    if remote:
        run("git", "remote", "add", "origin", remote, cwd=root)


def commit_all(root: Path, message: str) -> str:
    run("git", "add", "-A", cwd=root)
    run("git", "commit", "-m", message, cwd=root)
    return run("git", "rev-parse", "HEAD", cwd=root).stdout.strip()


def working_tree_hash(root: Path) -> str:
    """A real git tree hash of the current working tree, including untracked
    generated files, without leaving a commit behind."""
    run("git", "add", "-A", cwd=root)
    tree = run("git", "write-tree", cwd=root).stdout.strip()
    run("git", "reset", cwd=root)
    return tree


def template_body(role: str) -> str:
    return (
        f'name = "{role}"\n'
        f'description = "fixture template for {role}"\n'
        'sandbox_mode = "read-only"\n'
        'model = "${MODEL_ID}"\n'
        'model_reasoning_effort = "${REASONING_EFFORT}"\n\n'
        'developer_instructions = """\n'
        f"ROLE: {role} (fixture).\n"
        '"""\n'
    )


def profile(main_commit: str, owned_tree: str, candidate_commit: str) -> dict[str, Any]:
    return {
        "schema": "repository-control-plane-profile/v1",
        "profile": "github-portfolio-control",
        "skills": SKILLS,
        "runtime_capabilities": {
            "git_town": {"scope": "user", "installer_state": "NOT_IMPLEMENTED"},
            "forgejo": {"scope": "host", "service_state": "NOT_EXERCISED"},
        },
        "authority": {
            "automatic_merge": False, "automatic_conflict_resolution": False,
            "visibility_change": False, "credential_values": False,
        },
        "subject_pin": {
            "main_commit": main_commit,
            "owned_tree_path": "skills/github-portfolio-control",
            "owned_tree": owned_tree,
            "candidate_commit": candidate_commit,
            "candidate_source_path": CANDIDATE_SOURCE_PATH,
            "candidate_repin_policy": (
                "fixture: candidate_commit must be re-bound to merged main at publication."
            ),
        },
    }


def make_shared(root: Path):
    scripts = root / "skills/shared-skills-infra/scripts"
    scripts.mkdir(parents=True)
    for name in SCRIPT_NAMES:
        shutil.copy2(SKILL_ROOT / "scripts" / name, scripts / name)

    for name in SKILLS:
        skill = root / "skills" / name / "SKILL.md"
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.write_text(
            f"---\nname: {name}\ndescription: fixture\n---\n"
            f"# {name}\nCANONICAL_BODY_MARKER_{name.replace('-', '_').upper()}\n"
        )

    ghpc_dir = root / "skills/github-portfolio-control"
    ghpc_dir.mkdir(parents=True, exist_ok=True)
    (ghpc_dir / "AGENTS.md").write_text(
        "# github-portfolio-control AGENTS fixture\nCANONICAL_BODY_MARKER_GHPC_AGENTS\n"
    )
    (ghpc_dir / "README.md").write_text(
        "# github-portfolio-control README fixture\nCANONICAL_BODY_MARKER_GHPC_README\n"
    )

    (root / ".gitignore").write_text("__pycache__/\n*.pyc\n")
    init_git(root, "https://github.com/ed3c/skills-shared.git")
    main_commit = commit_all(root, "fixture shared source, without the ghpc profile itself")
    owned_tree = run(
        "git", "rev-parse", f"HEAD:skills/github-portfolio-control", cwd=root
    ).stdout.strip()

    run("git", "checkout", "-b", "candidate", cwd=root)
    templates_dir = root / CANDIDATE_SOURCE_PATH
    templates_dir.mkdir(parents=True, exist_ok=True)
    for role in CODEX_ROLES:
        (templates_dir / f"{role}.toml.template").write_text(template_body(role))
    candidate_commit = commit_all(root, "fixture portfolio-core candidate templates")
    run("git", "checkout", "main", cwd=root)

    profile_path = root / "skills/shared-skills-infra/references/repository-control-plane-profile.github-portfolio-control.json"
    selected = profile(main_commit, owned_tree, candidate_commit)
    write_json(profile_path, selected)
    commit_all(root, "add ghpc profile pinning main+candidate")

    sys.path.insert(0, str(scripts))
    spec = importlib.util.spec_from_file_location("fixture_bootstrap_ghpc", scripts / "consumer_bootstrap_ghpc.py")
    assert spec and spec.loader
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loaded
    spec.loader.exec_module(loaded)
    return loaded, profile_path, selected


def make_consumer(root: Path) -> None:
    init_git(root, "https://github.com/example/portfolio-repo.git")
    (root / "README.md").write_text("# Existing consumer prose\n\nKeep this paragraph.\n")
    commit_all(root, "initial consumer")


def files(root: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if ".git" in path.parts:
            continue
        if path.is_file() and not path.is_symlink():
            result[path.relative_to(root).as_posix()] = path.read_bytes()
    return result
