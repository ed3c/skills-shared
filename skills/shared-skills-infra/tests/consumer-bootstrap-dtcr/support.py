#!/usr/bin/env python3
"""Hermetic fixture builder for the dual-track-code-review-loop consumer bootstrap.

Builds a fully synthetic `shared` world (its own scripts copy, its own two
fixture Skills, its own canonical DTCR bodies and prompt catalogue) plus two
throwaway consumer repositories -- one EMPTY (a single `--allow-empty` initial
commit) and one BROWNFIELD (already carrying the default profile's managed
blocks, its five generated JSON authorities and a workflow). Nothing here
touches this real checkout's history and nothing reaches the network, so a
stale pin can be planted and killed deterministically.
"""
from __future__ import annotations

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
    "consumer_bootstrap_routes.py", "consumer_bootstrap_dtcr.py",
)
SKILLS = ["dual-track-code-review-loop", "shared-skills-infra"]
OWNED_TREE_PATH = "skills/dual-track-code-review-loop"
PROMPT_CATALOGUE = f"{OWNED_TREE_PATH}/references/prompts/README.md"
PROFILE_REL = (
    "skills/shared-skills-infra/references/"
    "repository-control-plane-profile.dual-track-code-review-loop.json"
)

DOMAIN_BEGIN = "<!-- BEGIN DOMAIN DECOUPLING BOOTSTRAP -->"
DOMAIN_END = "<!-- END DOMAIN DECOUPLING BOOTSTRAP -->"

# Generated authorities the default profile owns in the brownfield fixture.
# Every one of these must be byte-identical before and after a DTCR bootstrap.
FOREIGN_AUTHORITIES = (
    ".agents/control-plane/source.json",
    ".agents/control-plane/profile.json",
    ".agents/control-plane/requirements.json",
    ".agents/control-plane/bootstrap-receipt.json",
    ".agents/bindings/repository-control-plane.json",
)
FOREIGN_WORKFLOW = ".github/workflows/domain-decoupling-bootstrap.yml"

# Surfaces the #527 repair removed from scope: no generator, schema, fixture or
# precedent exists for any of them anywhere in this repository.
DROPPED_SURFACES = (
    ".agents/prompt-packets", ".agents/session-dispatch", ".agents/handoffs", ".agents/receipts",
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


def profile(main_commit: str, owned_tree: str) -> dict[str, Any]:
    return {
        "schema": "repository-control-plane-profile/v1",
        "profile": "dual-track-code-review-loop",
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
            "owned_tree_path": OWNED_TREE_PATH,
            "owned_tree": owned_tree,
            "candidate_commit": main_commit,
            "candidate_source_path": OWNED_TREE_PATH,
            "candidate_repin_policy": (
                "fixture: no unmerged candidate source exists; candidate_commit equals main_commit."
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

    dtcr_dir = root / OWNED_TREE_PATH
    (dtcr_dir / "AGENTS.md").write_text(
        "# dual-track-code-review-loop AGENTS fixture\nCANONICAL_BODY_MARKER_DTCR_AGENTS\n"
    )
    (dtcr_dir / "README.md").write_text(
        "# dual-track-code-review-loop README fixture\nCANONICAL_BODY_MARKER_DTCR_README\n"
    )
    catalogue = root / PROMPT_CATALOGUE
    catalogue.parent.mkdir(parents=True, exist_ok=True)
    catalogue.write_text(
        "# Dual-Track Code Review Loop -- zero-context Session prompts (fixture)\n\n"
        "CANONICAL_BODY_MARKER_DTCR_PROMPTS\n\n"
        "## P0 -- Control / Authority Binder\n\n"
        "```text\nROLE: DTCR Control Binder (fixture body).\n```\n"
    )

    (root / ".gitignore").write_text("__pycache__/\n*.pyc\n")
    init_git(root, "https://github.com/ed3c/skills-shared.git")
    main_commit = commit_all(root, "fixture shared source, without the dtcr profile itself")
    owned_tree = run("git", "rev-parse", f"HEAD:{OWNED_TREE_PATH}", cwd=root).stdout.strip()

    profile_path = root / PROFILE_REL
    selected = profile(main_commit, owned_tree)
    write_json(profile_path, selected)
    commit_all(root, "add dtcr profile pinning main")

    sys.path.insert(0, str(scripts))
    spec = importlib.util.spec_from_file_location(
        "fixture_bootstrap_dtcr", scripts / "consumer_bootstrap_dtcr.py"
    )
    assert spec and spec.loader
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loaded
    spec.loader.exec_module(loaded)
    return loaded, profile_path, selected


def make_consumer_empty(root: Path) -> None:
    """A genuinely empty repository: one initial commit, no tracked content."""
    init_git(root, "https://github.com/example/empty-repo.git")
    run("git", "commit", "--allow-empty", "-m", "initial empty consumer", cwd=root)


def make_consumer_brownfield(root: Path) -> None:
    """A repository already governed by the default (Domain Decoupling) profile."""
    init_git(root, "https://github.com/example/brownfield-repo.git")
    (root / "README.md").write_text(
        "# Existing consumer prose\n\nKeep this paragraph.\n\n"
        f"{DOMAIN_BEGIN}\n## Modular Agent control plane\n\nForeign managed body.\n{DOMAIN_END}\n"
    )
    (root / "AGENTS.md").write_text(
        "# Brownfield AGENTS router\n\nHand-written routing prose that must survive.\n\n"
        f"{DOMAIN_BEGIN}\n## Modular Agent bootstrap route\n\n"
        "Foreign managed body owned by the default profile.\n"
        f"{DOMAIN_END}\n"
    )
    write_json(root / ".agents/control-plane/source.json", {
        "schema": "shared-skills/source-pin/v1",
        "source": {"repository": "https://github.com/ed3c/skills-shared", "commit": "a" * 40, "tree": "b" * 40},
    })
    write_json(root / ".agents/control-plane/profile.json", {
        "schema": "repository-control-plane-binding/v1", "profile": "default",
    })
    write_json(root / ".agents/control-plane/requirements.json", {
        "schema": "shared-skills/consumer-requirements/v1", "binding": "default",
    })
    write_json(root / ".agents/control-plane/bootstrap-receipt.json", {
        "schema": "shared-skills/consumer-bootstrap-receipt/v1", "consumer": {"repository": "example/brownfield-repo"},
    })
    write_json(root / ".agents/bindings/repository-control-plane.json", {
        "schema": "shared-skills/consumer-binding/v1", "binding": "repository-control-plane",
    })
    workflow = root / FOREIGN_WORKFLOW
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text(
        "# GENERATED BY DOMAIN-DECOUPLING-V1 CONSUMER BOOTSTRAP\n"
        "name: domain-decoupling-bootstrap\non: workflow_dispatch\njobs: {}\n"
    )
    commit_all(root, "initial brownfield consumer under the default profile")


def files(root: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if ".git" in path.parts:
            continue
        if path.is_file() and not path.is_symlink():
            result[path.relative_to(root).as_posix()] = path.read_bytes()
    return result


def foreign_snapshot(root: Path) -> dict[str, bytes]:
    """Every byte the DTCR bootstrap must not touch in the brownfield fixture."""
    snapshot: dict[str, bytes] = {}
    for relative in (*FOREIGN_AUTHORITIES, FOREIGN_WORKFLOW):
        snapshot[relative] = (root / relative).read_bytes()
    return snapshot
