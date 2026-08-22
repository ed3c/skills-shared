#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = ROOT / "skills/shared-skills-infra/scripts"
sys.path.insert(0, str(SCRIPTS))
SCRIPT = SCRIPTS / "consumer_bootstrap_cadg.py"
spec = importlib.util.spec_from_file_location("consumer_bootstrap_cadg", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

FAILS: list[str] = []


def git(root: Path, *args: str) -> None:
    result = subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)


def fresh() -> tuple[tempfile.TemporaryDirectory[str], Path]:
    td = tempfile.TemporaryDirectory()
    root = Path(td.name)
    git(root, "init", "-q")
    git(root, "config", "user.email", "fixture@example.invalid")
    git(root, "config", "user.name", "fixture")
    (root / "README.md").write_text("# Human repository\n\nkeep-this-prose\n", encoding="utf-8")
    git(root, "add", "README.md")
    git(root, "commit", "-qm", "initial")
    return td, root


def expect_red(label: str, fn) -> None:
    try:
        fn()
    except mod.BootstrapError:
        return
    except Exception as exc:
        FAILS.append(f"{label}: wrong exception {exc!r}")
        return
    FAILS.append(f"{label}: mutation survived")


def apply(root: Path) -> None:
    mod.bootstrap(consumer=root, repository_id="owner/consumer", apply=True, shared_root=ROOT)


def check(root: Path) -> None:
    mod.bootstrap(consumer=root, repository_id="owner/consumer", apply=False, shared_root=ROOT)


# Positive + idempotency + Human prose preservation.
td, repo = fresh()
try:
    before_readme = (repo / "README.md").read_bytes()
    apply(repo)
    check(repo)
    first = {p: (repo / p).read_bytes() for p in mod.generated_paths()}
    apply(repo)
    check(repo)
    second = {p: (repo / p).read_bytes() for p in mod.generated_paths()}
    if first != second:
        FAILS.append("SECOND_APPLY_NOT_BYTE_IDEMPOTENT")
    if (repo / "README.md").read_bytes() != before_readme:
        FAILS.append("HUMAN_PROSE_OVERWRITTEN")
    for surface in (repo / ".agents/skills", repo / ".claude/skills"):
        for name in mod.EXPECTED_SKILLS:
            candidate = surface / name / "SKILL.md"
            if candidate.exists() and not candidate.is_symlink():
                FAILS.append("COPIED_CANONICAL_SKILL_BODY")
finally:
    td.cleanup()

# Atomic downstream failure must restore every generated path.
td, repo = fresh()
try:
    expect_red("INJECTED_DOWNSTREAM_FAILURE", lambda: mod.bootstrap(
        consumer=repo, repository_id="owner/consumer", apply=True, shared_root=ROOT, fail_after=3
    ))
    leftovers = [p.as_posix() for p in mod.generated_paths() if (repo / p).exists() or (repo / p).is_symlink()]
    if leftovers:
        FAILS.append("CLEANUP_LEAVES_PARTIAL_GENERATED_STATE:" + ",".join(leftovers))
finally:
    td.cleanup()

# Unknown/human-owned target is refused before writes.
td, repo = fresh()
try:
    target = repo / "docs/traceability/CADG_INDEX.md"
    target.parent.mkdir(parents=True)
    target.write_text("human-owned\n", encoding="utf-8")
    expect_red("UNKNOWN_GENERATED_FILE_ACCEPTED", lambda: apply(repo))
    if target.read_text(encoding="utf-8") != "human-owned\n":
        FAILS.append("HUMAN_PROSE_OVERWRITTEN_ON_REFUSAL")
finally:
    td.cleanup()


def mutate_case(label: str, mutate) -> None:
    td, repo = fresh()
    try:
        apply(repo)
        mutate(repo)
        expect_red(label, lambda: check(repo))
    finally:
        td.cleanup()


def mutate_source_commit(repo: Path) -> None:
    path = repo / mod.SOURCE_REL
    value = json.loads(path.read_text())
    value["commit"] = "main"
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def mutate_source_checker(repo: Path) -> None:
    path = repo / mod.SOURCE_REL
    value = json.loads(path.read_text())
    value["artifacts"]["checker"]["git_blob"] = "0" * 40
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def mutate_workflow(repo: Path) -> None:
    path = repo / mod.WORKFLOW_REL
    text = path.read_text()
    source = json.loads((repo / mod.SOURCE_REL).read_text())
    path.write_text(text.replace(source["commit"], "1" * 40))


def promote_receipt(repo: Path) -> None:
    path = repo / mod.RECEIPT_REL
    value = json.loads(path.read_text())
    value["states"]["agent_execution"] = "PASS"
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def widen_credentials(repo: Path) -> None:
    path = repo / mod.PROFILE_REL
    value = json.loads(path.read_text())
    value["authority"]["credential_values"] = True
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def remove_rollback(repo: Path) -> None:
    path = repo / mod.RECEIPT_REL
    value = json.loads(path.read_text())
    value.pop("rollback")
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")

mutate_case("MUTABLE_MAIN_OR_LATEST_PIN", mutate_source_commit)
mutate_case("STALE_CADG_SCHEMA_OR_CHECKER_PIN", mutate_source_checker)
mutate_case("CADG_WORKFLOW_POINTS_TO_DIFFERENT_SHARED_COMMIT", mutate_workflow)
mutate_case("BOOTSTRAP_PASS_PROMOTED_TO_AGENT_OR_SHADOW_PASS", promote_receipt)
mutate_case("PRIVATE_CONSUMER_IMPORT_WIDENS_CREDENTIAL_ACCESS", widen_credentials)
mutate_case("ROLLBACK_MISSING", remove_rollback)

# Copied Skill body must be rejected.
td, repo = fresh()
try:
    apply(repo)
    copied = repo / ".agents/skills/human-led-agentic-engineering"
    copied.mkdir(parents=True)
    (copied / "SKILL.md").write_text("copied body\n")
    expect_red("COPIED_CANONICAL_SKILL_BODY", lambda: check(repo))
finally:
    td.cleanup()

# Explicit rollback on a clean generated profile leaves no partial state.
td, repo = fresh()
try:
    apply(repo)
    mod.bootstrap(consumer=repo, repository_id="owner/consumer", apply=False, rollback=True, shared_root=ROOT)
    leftovers = [p.as_posix() for p in mod.generated_paths() if (repo / p).exists() or (repo / p).is_symlink()]
    if leftovers:
        FAILS.append("CLEANUP_LEAVES_PARTIAL_GENERATED_STATE_AFTER_ROLLBACK:" + ",".join(leftovers))
    if (repo / "README.md").read_text() != "# Human repository\n\nkeep-this-prose\n":
        FAILS.append("ROLLBACK_DAMAGED_HUMAN_PROSE")
finally:
    td.cleanup()

if FAILS:
    for item in FAILS:
        print("CADG-BOOTSTRAP-TEST-RED", item)
    raise SystemExit(2)
print("CADG-BOOTSTRAP-TEST-GREEN falsifiers=11 idempotency=PASS rollback=PASS evidence_ceiling=DETERMINISTIC")
