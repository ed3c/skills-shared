#!/usr/bin/env python3
"""Observe one exact GitHub Actions Skill-bootstrap admission subject.

This observer is intentionally narrow. It admits only the read-only
`consumer-bootstrap-verification` task, selects only `shared-skills-infra`, and
reuses the existing `skill-resolution-receipt/v1` checker as admission authority.
It does not observe a local Codex/Claude user surface, an Agent/model task, a
provider, Git Town, Forgejo, merge, release, or production execution.
"""
from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any
from urllib.parse import urlparse

from consumer_bootstrap_common import (
    BINDING_REL,
    RECEIPT_REL,
    SOURCE_REL,
    BootstrapError,
    canonical,
    git_out,
    read_json,
    reject_copied_skill_bodies,
    shared_identity,
)
from consumer_bootstrap_receipt import validate_receipt_shape, validate_rollback

TASK_ID = "consumer-bootstrap-verification/v1"
SELECTED_SKILL = "shared-skills-infra"
RUNTIME_IDENTITY = "GITHUB_ACTIONS"
ACCESS_MODE = "GITHUB_ACTIONS_PINNED_BUNDLE"
RESOLVER_VERSION = "consumer-runtime-observer/v1"
RUNTIME_REQUIREMENTS_REL = Path(
    "skills/shared-skills-infra/references/runtime-requirements.json"
)
REQUIREMENTS_CHECKER_REL = Path(
    "skills/shared-skills-infra/scripts/check_skill_requirements.py"
)
BOOTSTRAP_CHECKER_REL = Path(
    "skills/shared-skills-infra/scripts/check_skill_bootstrap.py"
)
SCHEMA_ROOT_REL = Path("skills/shared-skills-infra/references")
FIXED_PROBES = (
    "probe.binding-readback",
    "probe.git-available",
    "probe.jsonschema-available",
    "probe.python-version",
)
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
REPOSITORY_ID = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class ObservationError(ValueError):
    """A readable subject violates a runtime-admission invariant."""


class ObservationInputError(ValueError):
    """A required subject is absent, unreadable, malformed, or schema-invalid."""


class ObservationDependencyError(RuntimeError):
    """A required deterministic validator or probe dependency is unavailable."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def run_git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "git failed"
        raise ObservationError(detail)
    return result


def git_value(root: Path, *args: str) -> str:
    return run_git(root, *args).stdout.strip()


def repository_id_from_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or parsed.username or not parsed.hostname:
        raise ObservationError("shared repository identity must be credential-free HTTP(S)")
    path = parsed.path.strip("/").removesuffix(".git")
    parts = path.split("/")
    if len(parts) != 2 or not all(parts):
        raise ObservationError("shared repository URL must identify owner/name")
    identity = "/".join(parts)
    if not REPOSITORY_ID.fullmatch(identity):
        raise ObservationError("shared repository owner/name is invalid")
    return identity


def content_digest(path: Path) -> str:
    if not path.is_dir() or path.is_symlink():
        raise ObservationError(f"canonical Skill root absent or non-directory: {path}")
    digest = hashlib.sha256()
    files = sorted(
        item
        for item in path.rglob("*")
        if item.is_file()
        and "__pycache__" not in item.parts
        and not item.name.endswith(".pyc")
    )
    if not files or not (path / "SKILL.md").is_file():
        raise ObservationError("canonical shared-skills-infra Skill body is incomplete")
    for item in files:
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def validate_binding(binding: dict[str, Any], source: dict[str, Any], shared_root: Path) -> dict[str, Any]:
    expected_fields = {
        "binding",
        "registry_sha256",
        "requirements_sha256",
        "repo_owned",
        "schema",
        "skills",
        "source",
        "surfaces",
        "content_sha256",
    }
    if set(binding) != expected_fields or binding.get("schema") != "shared-skills/consumer-binding/v1":
        raise ObservationError("consumer binding schema or fields drifted")
    unsigned = dict(binding)
    claimed = unsigned.pop("content_sha256", None)
    if claimed != sha256(canonical(unsigned)):
        raise ObservationError("consumer binding aggregate digest is stale")
    if binding["source"] != source["source"]:
        raise ObservationError("consumer binding source differs from exact source pin")
    if not HEX64.fullmatch(binding.get("registry_sha256", "")):
        raise ObservationError("consumer binding registry digest is invalid")
    rows = binding.get("skills")
    if not isinstance(rows, list):
        raise ObservationError("consumer binding Skill rows are absent")
    names = [row.get("name") for row in rows if isinstance(row, dict)]
    if len(names) != len(rows) or len(names) != len(set(names)) or names != sorted(names):
        raise ObservationError("consumer binding Skill denominator is duplicate or unordered")
    selected = next((row for row in rows if row.get("name") == SELECTED_SKILL), None)
    if selected is None:
        raise ObservationError("shared-skills-infra is absent from the consumer binding")
    if set(selected) != {"name", "content_sha256", "entrypoint"}:
        raise ObservationError("selected Skill binding fields drifted")
    if selected["entrypoint"] != f"skills/{SELECTED_SKILL}/SKILL.md":
        raise ObservationError("selected Skill entrypoint was substituted")
    actual_digest = content_digest(shared_root / "skills" / SELECTED_SKILL)
    if selected["content_sha256"] != actual_digest:
        raise ObservationError("selected Skill content digest is stale")
    return selected


def artifact_digest(receipt: dict[str, Any], path: str) -> str:
    matches = [row for row in receipt.get("artifacts", []) if row.get("path") == path]
    if len(matches) != 1 or matches[0].get("state") != "GENERATED":
        raise ObservationError(f"bootstrap receipt does not bind generated artifact: {path}")
    digest = matches[0].get("sha256")
    if not isinstance(digest, str) or not HEX64.fullmatch(digest):
        raise ObservationError(f"bootstrap receipt artifact digest invalid: {path}")
    return digest


def validate_bootstrap_receipt(
    *,
    receipt: dict[str, Any],
    source: dict[str, Any],
    binding: dict[str, Any],
    consumer: Path,
    repository_id: str,
) -> str:
    try:
        validate_receipt_shape(receipt)
        validate_rollback(consumer, receipt["rollback"])
    except BootstrapError as exc:
        raise ObservationError(str(exc)) from exc
    if receipt["consumer"]["repository"] != repository_id:
        raise ObservationError("bootstrap receipt consumer repository was substituted")
    if receipt["shared_source"] != source:
        raise ObservationError("bootstrap receipt shared source differs from source pin")
    semantic = sha256(canonical(binding))
    if receipt["binding"] != {
        "path": BINDING_REL.as_posix(),
        "semantic_sha256": semantic,
        "content_sha256": binding["content_sha256"],
    }:
        raise ObservationError("bootstrap receipt binding identity is stale")
    if artifact_digest(receipt, SOURCE_REL.as_posix()) != sha256(
        (consumer / SOURCE_REL).read_bytes()
    ):
        raise ObservationError("bootstrap receipt source artifact is stale")
    if artifact_digest(receipt, BINDING_REL.as_posix()) != sha256(
        (consumer / BINDING_REL).read_bytes()
    ):
        raise ObservationError("bootstrap receipt binding artifact is stale")
    return sha256((consumer / RECEIPT_REL).read_bytes())


def run_checked_document(checker: Path, document: Path, schema_root: Path) -> None:
    if not checker.is_file() or checker.is_symlink():
        raise ObservationDependencyError(f"required checker missing: {checker}")
    result = subprocess.run(
        [
            sys.executable,
            str(checker),
            str(document),
            "--schema-root",
            str(schema_root),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return
    detail = result.stderr.strip() or result.stdout.strip() or "checker failed"
    if result.returncode == 70:
        raise ObservationDependencyError(detail)
    if result.returncode == 64:
        raise ObservationInputError(detail)
    raise ObservationError(detail)


def validate_runtime_requirements(shared_root: Path) -> tuple[dict[str, Any], str]:
    path = shared_root / RUNTIME_REQUIREMENTS_REL
    if not path.is_file() or path.is_symlink():
        raise ObservationError("shared-skills-infra runtime requirements are absent")
    run_checked_document(
        shared_root / REQUIREMENTS_CHECKER_REL,
        path,
        shared_root / SCHEMA_ROOT_REL,
    )
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ObservationInputError(f"unreadable runtime requirements: {exc}") from exc
    if document.get("skill_name") != SELECTED_SKILL:
        raise ObservationError("runtime requirements belong to another Skill")
    if document.get("supported_runtime_identities") != [RUNTIME_IDENTITY]:
        raise ObservationError("bootstrap verification requires an exact GitHub Actions runtime declaration")
    if document.get("network_policy") != {"mode": "NONE", "allowed_hosts": []}:
        raise ObservationError("bootstrap verification cannot admit network access")
    if document.get("filesystem") != {
        "needs_writable_worktree": False,
        "writable_subpaths": [],
    }:
        raise ObservationError("bootstrap verification cannot admit repository writes")
    if document.get("isolation") != {
        "requires_isolated_worktree": False,
        "sandbox": "READ_ONLY",
    }:
        raise ObservationError("bootstrap verification requires a read-only sandbox")
    if document.get("secret_variable_names") != []:
        raise ObservationError("bootstrap verification cannot require secrets")
    if document.get("setup_entrypoints") != []:
        raise ObservationError("bootstrap verification cannot execute setup entrypoints")
    probes = document.get("probe_entrypoints")
    if not isinstance(probes, list) or tuple(sorted(probes)) != FIXED_PROBES:
        raise ObservationError("runtime requirements contain a missing or unregistered probe")
    expected_exec = {
        "git": (">=2.30", "SYSTEM_PACKAGE"),
        "jsonschema": ("==4.26.0", "LANGUAGE_PACKAGE"),
        "python3": (">=3.12", "SYSTEM_PACKAGE"),
    }
    observed_exec: dict[str, tuple[str, str]] = {}
    for row in document.get("executables", []):
        if not isinstance(row, dict) or set(row) != {
            "name",
            "version_constraint",
            "provenance",
        }:
            raise ObservationError("runtime executable declaration fields drifted")
        observed_exec[row["name"]] = (row["version_constraint"], row["provenance"])
    if observed_exec != expected_exec:
        raise ObservationError("runtime executable closure or pins drifted")
    boundary = document.get("not_exercised_without_substrate")
    if not isinstance(boundary, list) or len(boundary) < 3:
        raise ObservationError("runtime requirements do not bound unexercised host/model/provider lanes")
    blob = git_value(shared_root, "rev-parse", f"HEAD:{RUNTIME_REQUIREMENTS_REL.as_posix()}")
    if not HEX40.fullmatch(blob):
        raise ObservationError("runtime requirements are not bound to an exact Git blob")
    return document, sha256(path.read_bytes())


def parse_git_version(text: str) -> tuple[int, int]:
    match = re.search(r"(\d+)\.(\d+)", text)
    if not match:
        return (0, 0)
    return int(match.group(1)), int(match.group(2))


def fixed_probe_results(binding_readback: bool) -> list[dict[str, str]]:
    results: dict[str, str] = {}
    results["probe.binding-readback"] = "PASS" if binding_readback else "FAIL"

    git_probe = subprocess.run(
        ["git", "--version"], text=True, capture_output=True, check=False
    )
    results["probe.git-available"] = (
        "PASS"
        if git_probe.returncode == 0
        and parse_git_version(git_probe.stdout) >= (2, 30)
        else "FAIL"
    )

    try:
        jsonschema_version = metadata.version("jsonschema")
    except metadata.PackageNotFoundError:
        jsonschema_version = "ABSENT"
    results["probe.jsonschema-available"] = (
        "PASS" if jsonschema_version == "4.26.0" else "FAIL"
    )
    results["probe.python-version"] = (
        "PASS" if sys.version_info >= (3, 12) else "FAIL"
    )
    return [{"id": probe, "state": results[probe]} for probe in FIXED_PROBES]


def outside(root: Path, candidate: Path) -> bool:
    root = root.resolve()
    candidate = candidate.resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return True
    return False


def build_receipt(
    *,
    consumer: Path,
    shared_root: Path,
    repository_id: str,
    expected_consumer_sha: str,
    consumer_visibility: str,
    canonical_visibility: str,
) -> dict[str, Any]:
    if not REPOSITORY_ID.fullmatch(repository_id):
        raise ObservationInputError("repository-id must be owner/name")
    if consumer_visibility not in {"PUBLIC", "PRIVATE"}:
        raise ObservationInputError("consumer visibility must be PUBLIC or PRIVATE")
    if canonical_visibility not in {"PUBLIC", "PRIVATE"}:
        raise ObservationInputError("canonical visibility must be PUBLIC or PRIVATE")
    if not HEX40.fullmatch(expected_consumer_sha):
        raise ObservationInputError("expected consumer SHA must be an exact 40-hex commit")

    consumer = consumer.resolve()
    shared_root = shared_root.resolve()
    actual_consumer_sha = git_value(consumer, "rev-parse", "HEAD")
    if actual_consumer_sha != expected_consumer_sha:
        raise ObservationError(
            f"consumer head moved: expected={expected_consumer_sha} actual={actual_consumer_sha}"
        )

    try:
        identity = shared_identity(shared_root)
        source = read_json(consumer / SOURCE_REL)
        binding = read_json(consumer / BINDING_REL)
        bootstrap_receipt = read_json(consumer / RECEIPT_REL)
    except BootstrapError as exc:
        raise ObservationError(str(exc)) from exc

    # The binding-readback probe IS this pair of comparisons, not a literal: did
    # the consumer's committed source pin read back as the exact source document
    # (and repository identity) we resolved from the live shared root. Neither
    # comparison raises immediately -- both flow into fixed_probe_results() below
    # so the FAIL state is reachable in the emitted receipt/error, same as the
    # other fixed probes.
    binding_readback = source == identity.source_document() and (
        repository_id_from_url(identity.repository)
        == repository_id_from_url(source["source"]["repository"])
    )
    selected = validate_binding(binding, source, shared_root)
    bootstrap_digest = validate_bootstrap_receipt(
        receipt=bootstrap_receipt,
        source=source,
        binding=binding,
        consumer=consumer,
        repository_id=repository_id,
    )

    try:
        reject_copied_skill_bodies(consumer, [SELECTED_SKILL])
    except BootstrapError as exc:
        raise ObservationError(str(exc)) from exc

    requirements, requirements_digest = validate_runtime_requirements(shared_root)
    probes = fixed_probe_results(binding_readback=binding_readback)
    failed = [row["id"] for row in probes if row["state"] != "PASS"]
    if failed:
        raise ObservationError("capability probe failed: " + ",".join(failed))

    selected_tree = git_value(
        shared_root, "rev-parse", f"HEAD:skills/{SELECTED_SKILL}"
    )
    if not HEX40.fullmatch(selected_tree):
        raise ObservationError("selected Skill tree identity is invalid")

    rejected = [
        {
            "name": row["name"],
            "reason": f"not required by canonical task {TASK_ID}",
        }
        for row in binding["skills"]
        if row["name"] != SELECTED_SKILL
    ]
    plan = {
        "task": TASK_ID,
        "runtime": RUNTIME_IDENTITY,
        "access_mode": ACCESS_MODE,
        "consumer_commit": actual_consumer_sha,
        "shared_commit": identity.commit,
        "binding_content_sha256": binding["content_sha256"],
        "bootstrap_receipt_sha256": bootstrap_digest,
        "runtime_requirements_sha256": requirements_digest,
        "probe_ids": [row["id"] for row in probes],
    }
    return {
        "schema": "skill-resolution-receipt/v1",
        "resolver_version": RESOLVER_VERSION,
        "runtime_identity": RUNTIME_IDENTITY,
        "consumer": {
            "repository_id": repository_id,
            "subject_sha": actual_consumer_sha,
            "visibility": consumer_visibility,
        },
        "canonical": {
            "repository_id": repository_id_from_url(identity.repository),
            "visibility": canonical_visibility,
            "commit_sha": identity.commit,
            "registry_digest": binding["registry_sha256"],
        },
        "selected_skills": [
            {
                "name": SELECTED_SKILL,
                "canonical_path": f"skills/{SELECTED_SKILL}",
                "blob_or_tree_identity": selected_tree,
                "content_sha256": selected["content_sha256"],
                "selection_reason": "EXPLICIT_TASK_BINDING",
                "trigger_evidence": (
                    f"{TASK_ID};bootstrap-receipt-sha256={bootstrap_digest}"
                ),
                "transitive_dependencies": [],
                "access_mode": ACCESS_MODE,
                "surface_readback_state": "VERIFIED",
                "runtime_requirements_digest": requirements_digest,
            }
        ],
        "rejected_candidates": rejected,
        "shadowing_scan": {
            "state": "CLEAN",
            "surfaces_scanned": [".agents/skills", ".claude/skills"],
            "findings": [],
        },
        "environment": {
            "state": "PREPARED",
            "plan_digest": sha256(canonical(plan)),
            "required_secret_names": [],
            "absent_secret_names": [],
            "setup_entrypoints": [],
            "capability_probes": probes,
        },
        "bootstrap_states": [
            "RUNTIME_BOUND",
            "REPOSITORY_POLICY_BOUND",
            "SKILL_REQUIREMENTS_DISCOVERED",
            "MINIMAL_SKILL_SET_RESOLVED",
            "CANONICAL_SKILL_SUBJECTS_BOUND",
            "SKILL_SURFACES_AVAILABLE",
            "SKILL_RUNTIME_REQUIREMENTS_BOUND",
            "RUNTIME_ENV_CLOSURE_BOUND",
            "ENVIRONMENT_PLAN_RENDERED",
            "ENVIRONMENT_PREPARED",
            "CAPABILITY_PROBES_PASS",
            "TASK_EXECUTION_ADMITTED",
        ],
    }


def observe(
    *,
    consumer: Path,
    shared_root: Path,
    repository_id: str,
    expected_consumer_sha: str,
    consumer_visibility: str,
    canonical_visibility: str,
    output: Path,
) -> dict[str, Any]:
    consumer = consumer.resolve()
    shared_root = shared_root.resolve()
    output = output.resolve()
    if not outside(consumer, output) or not outside(shared_root, output):
        raise ObservationError("runtime receipt output must stay outside both repositories")
    output.parent.mkdir(parents=True, exist_ok=True)

    receipt = build_receipt(
        consumer=consumer,
        shared_root=shared_root,
        repository_id=repository_id,
        expected_consumer_sha=expected_consumer_sha,
        consumer_visibility=consumer_visibility,
        canonical_visibility=canonical_visibility,
    )
    fd, temporary_name = tempfile.mkstemp(
        prefix=".skill-resolution-", suffix=".json", dir=output.parent
    )
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        temporary.write_text(json_text(receipt), encoding="utf-8")
        run_checked_document(
            shared_root / BOOTSTRAP_CHECKER_REL,
            temporary,
            shared_root / SCHEMA_ROOT_REL,
        )
        os.replace(temporary, output)
    finally:
        if temporary.exists():
            temporary.unlink()
    print(
        "CONSUMER-RUNTIME-GREEN "
        f"task={TASK_ID} runtime={RUNTIME_IDENTITY} "
        f"consumer={repository_id}@{expected_consumer_sha[:12]} "
        f"shared={receipt['canonical']['commit_sha'][:12]} "
        "skills=1 probes=4 terminal=TASK_EXECUTION_ADMITTED "
        "agent_model_execution=NOT_EXERCISED provider=NOT_EXERCISED"
    )
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--consumer", required=True, type=Path)
    parser.add_argument("--shared-root", required=True, type=Path)
    parser.add_argument("--repository-id", required=True)
    parser.add_argument("--expected-consumer-sha", required=True)
    parser.add_argument(
        "--consumer-visibility", choices=("PUBLIC", "PRIVATE"), required=True
    )
    parser.add_argument(
        "--canonical-visibility", choices=("PUBLIC", "PRIVATE"), required=True
    )
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        observe(
            consumer=args.consumer,
            shared_root=args.shared_root,
            repository_id=args.repository_id,
            expected_consumer_sha=args.expected_consumer_sha,
            consumer_visibility=args.consumer_visibility,
            canonical_visibility=args.canonical_visibility,
            output=args.output,
        )
        return 0
    except ObservationDependencyError as exc:
        print(f"CONSUMER-RUNTIME-DEPENDENCY {exc}", file=sys.stderr)
        return 70
    except ObservationInputError as exc:
        print(f"CONSUMER-RUNTIME-INVALID {exc}", file=sys.stderr)
        return 64
    except (ObservationError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"CONSUMER-RUNTIME-RED {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
