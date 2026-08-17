#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Callable

SKILL_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_NAMES = (
    "consumer_bootstrap.py", "consumer_bootstrap_common.py",
    "consumer_bootstrap_receipt.py", "consumer_bootstrap_routes.py",
)
SKILLS = [
    "shared-skills-infra", "procedural-shadow-runtime",
    "agentic-tech-lead-orchestration", "spatial-loop-systems-engineering",
    "git-town-stacked-pr-worker", "dual-forge-repository-loop",
]


def run(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if check and result.returncode:
        raise AssertionError(f"command failed {args}:\n{result.stdout}\n{result.stderr}")
    return result


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def commit_all(root: Path, message: str) -> None:
    run("git", "add", "-A", cwd=root)
    run("git", "commit", "-m", message, cwd=root)


def profile() -> dict[str, Any]:
    return {
        "schema": "repository-control-plane-profile/v1",
        "profile": "default-domain-decoupling",
        "skills": SKILLS,
        "runtime_capabilities": {
            "git_town": {"scope": "user", "installer_state": "NOT_IMPLEMENTED"},
            "forgejo": {"scope": "host", "service_state": "NOT_EXERCISED"},
        },
        "authority": {
            "automatic_merge": False, "automatic_conflict_resolution": False,
            "visibility_change": False, "credential_values": False,
        },
    }


def make_shared(root: Path):
    scripts = root / "skills/shared-skills-infra/scripts"
    scripts.mkdir(parents=True)
    for name in SCRIPT_NAMES:
        shutil.copy2(SKILL_ROOT / "scripts" / name, scripts / name)
    (scripts / "shared_skills.py").write_text("# canonical generator fixture\n")
    module = root / "skills/shared-skills-infra/modules/github-actions-consumer-bootstrap.yml"
    module.parent.mkdir(parents=True)
    shutil.copy2(SKILL_ROOT / "modules/github-actions-consumer-bootstrap.yml", module)
    contract = root / "docs/architecture/DOMAIN_DECOUPLING.md"
    contract.parent.mkdir(parents=True)
    contract.write_text("# Domain Decoupling\nDOMAIN-DECOUPLING-V1\nCANONICAL_METHOD\n")
    profile_path = root / "skills/shared-skills-infra/references/repository-control-plane-profile.default.json"
    write_json(profile_path, profile())
    for name in SKILLS:
        skill = root / "skills" / name / "SKILL.md"
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.write_text(f"---\nname: {name}\ndescription: fixture\n---\n# {name}\n")
    (root / ".gitignore").write_text("__pycache__/\n*.pyc\n")
    init_git(root, "https://github.com/ed3c/skills-shared.git")
    commit_all(root, "fixture shared source")
    sys.path.insert(0, str(scripts))
    spec = importlib.util.spec_from_file_location("fixture_bootstrap", scripts / "consumer_bootstrap.py")
    assert spec and spec.loader
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loaded
    spec.loader.exec_module(loaded)
    return loaded, profile_path


def content_digest(path: Path) -> str:
    digest = hashlib.sha256()
    for file in sorted(p for p in path.rglob("*") if p.is_file()):
        digest.update(file.relative_to(path).as_posix().encode())
        digest.update(b"\0" + file.read_bytes() + b"\0")
    return digest.hexdigest()


def fake_attach(module, shared: Path, selected_profile: dict[str, Any]) -> Callable:
    def attach(profile_path: Path, consumer: Path, check: bool) -> None:
        identity = module.shared_identity(shared)
        profile_binding = {
            "schema": "repository-control-plane-binding/v1",
            "profile": selected_profile["profile"],
            "profile_sha256": module.sha256(module.canonical(selected_profile)),
            "skills": SKILLS,
            "runtime_capabilities": selected_profile["runtime_capabilities"],
            "authority": selected_profile["authority"],
        }
        requirements = {
            "schema": "shared-skills/consumer-requirements/v1",
            "binding": "repository-control-plane", "shared": SKILLS, "repo_owned": [],
            "surfaces": {"claude": ".claude/skills", "codex": ".agents/skills"},
        }
        rows = [
            {"name": name, "content_sha256": content_digest(shared / "skills" / name),
             "entrypoint": f"skills/{name}/SKILL.md"}
            for name in sorted(SKILLS)
        ]
        binding = {
            "binding": "repository-control-plane", "registry_sha256": "a" * 64,
            "requirements_sha256": module.sha256(module.json_text(requirements).encode()),
            "repo_owned": [], "schema": "shared-skills/consumer-binding/v1", "skills": rows,
            "source": {"repository": identity.repository, "commit": identity.commit, "tree": identity.tree},
            "surfaces": requirements["surfaces"],
        }
        binding["content_sha256"] = module.sha256(module.canonical(binding))
        expected = {
            module.PROFILE_REL: module.json_text(profile_binding),
            module.REQUIREMENTS_REL: module.json_text(requirements),
            module.BINDING_REL: module.json_text(binding),
        }
        for relative, text in expected.items():
            path = consumer / relative
            if check:
                if not path.is_file() or path.read_text() != text:
                    raise module.BootstrapError(f"fake attach drift: {relative}")
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
    return attach


def make_consumer(root: Path) -> None:
    init_git(root, "https://github.com/example/new-repo.git")
    (root / "README.md").write_text("# Existing consumer prose\n\nKeep this line.\n")
    commit_all(root, "initial consumer")
