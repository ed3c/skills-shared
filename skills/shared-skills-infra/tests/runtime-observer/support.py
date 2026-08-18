#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import sys
from typing import Any, Callable

PARENT = Path(__file__).resolve().parent.parent / "consumer-bootstrap"
_spec = importlib.util.spec_from_file_location(
    "consumer_bootstrap_test_support", PARENT / "support.py"
)
assert _spec and _spec.loader
_parent_support = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _parent_support
_spec.loader.exec_module(_parent_support)

commit_all = _parent_support.commit_all
fake_attach = _parent_support.fake_attach
make_consumer = _parent_support.make_consumer
make_shared = _parent_support.make_shared
profile = _parent_support.profile
run = _parent_support.run

SKILL_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_FILES = (
    "observe_consumer_runtime.py",
    "check_skill_bootstrap.py",
    "check_skill_requirements.py",
)
REFERENCE_FILES = (
    "runtime-requirements.json",
    "skill-resolution-receipt.schema.json",
    "skill-runtime-requirements.schema.json",
)


def copy_runtime_observer(shared: Path) -> None:
    scripts = shared / "skills/shared-skills-infra/scripts"
    references = shared / "skills/shared-skills-infra/references"
    scripts.mkdir(parents=True, exist_ok=True)
    references.mkdir(parents=True, exist_ok=True)
    for name in SCRIPT_FILES:
        shutil.copy2(SKILL_ROOT / "scripts" / name, scripts / name)
    for name in REFERENCE_FILES:
        shutil.copy2(SKILL_ROOT / "references" / name, references / name)
    run("git", "add", "-A", cwd=shared)
    run("git", "commit", "--amend", "--no-edit", cwd=shared)


def make_world(world: Path):
    shared = world / "shared"
    consumer = world / "consumer"
    module, profile_path = make_shared(shared)
    copy_runtime_observer(shared)
    selected = profile()
    attach = fake_attach(module, shared, selected)
    make_consumer(consumer)
    module.bootstrap_consumer(
        consumer=consumer,
        repository_id="example/new-repo",
        profile_path=profile_path,
        apply=True,
        attach_fn=attach,
        shared_root=shared,
    )
    commit_all(consumer, "admit consumer bootstrap")
    return module, selected, shared, consumer


def clone(source: Path, target: Path) -> Path:
    shutil.copytree(source, target, symlinks=True)
    return target


def refresh_consumer(
    module,
    selected: dict[str, Any],
    shared: Path,
    consumer: Path,
) -> str:
    profile_path = (
        shared
        / "skills/shared-skills-infra/references/"
        "repository-control-plane-profile.default.json"
    )
    attach = fake_attach(module, shared, selected)
    module.bootstrap_consumer(
        consumer=consumer,
        repository_id="example/new-repo",
        profile_path=profile_path,
        apply=True,
        attach_fn=attach,
        shared_root=shared,
    )
    commit_all(consumer, "refresh exact shared subject")
    return run("git", "rev-parse", "HEAD", cwd=consumer).stdout.strip()


def observer_command(
    shared: Path,
    consumer: Path,
    output: Path,
    *,
    expected_sha: str | None = None,
) -> list[str]:
    actual = run("git", "rev-parse", "HEAD", cwd=consumer).stdout.strip()
    return [
        sys.executable,
        str(shared / "skills/shared-skills-infra/scripts/observe_consumer_runtime.py"),
        "--consumer",
        str(consumer),
        "--shared-root",
        str(shared),
        "--repository-id",
        "example/new-repo",
        "--expected-consumer-sha",
        expected_sha or actual,
        "--consumer-visibility",
        "PUBLIC",
        "--output",
        str(output),
    ]


def run_observer(
    shared: Path,
    consumer: Path,
    output: Path,
    *,
    expected_sha: str | None = None,
    check: bool = True,
):
    return run(
        *observer_command(shared, consumer, output, expected_sha=expected_sha),
        cwd=consumer,
        check=check,
    )


def resign_bootstrap(module, receipt: dict[str, Any]) -> None:
    receipt.pop("receipt_sha256", None)
    receipt["receipt_sha256"] = module.sha256(module.canonical(receipt))


def mutate_shared_requirements(
    module,
    selected: dict[str, Any],
    shared: Path,
    consumer: Path,
    mutate: Callable[[dict[str, Any]], None] | None = None,
    *,
    remove: bool = False,
) -> str:
    path = shared / "skills/shared-skills-infra/references/runtime-requirements.json"
    if remove:
        path.unlink()
    else:
        value = json.loads(path.read_text())
        assert mutate is not None
        mutate(value)
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    commit_all(shared, "mutate runtime requirements")
    return refresh_consumer(module, selected, shared, consumer)
