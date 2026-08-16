"""Portable profile contract and deterministic consumer document renderer."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

EXIT_SEMANTIC = 2
EXIT_ABSENT = 3
EXIT_INPUT = 64
TOOL_VERSION = "1.0.0"

SHA_RE = re.compile(r"^[0-9a-f]{40}([0-9a-f]{24})?$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REPOSITORY_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ENTRYPOINT_RE = re.compile(r"^[a-z][a-z0-9]*([._-][a-z0-9]+)*$")
SKILL_NAME_RE = ENTRYPOINT_RE

REQUIRED_CHAIN: tuple[tuple[str, str, str], ...] = (
    ("BOOTSTRAP", "shared-skills-infra", "skill-resolution"),
    ("SHADOW_ADMISSION", "procedural-shadow-runtime", "shadow-admission"),
    ("TECH_LEAD_PLAN", "agentic-tech-lead-orchestration", "task-dag"),
    ("SPATIAL_INVARIANTS", "spatial-loop-systems-engineering", "spatial-invariants"),
    ("STACK_DELIVERY", "git-town-stacked-pr-worker", "git-town-stack"),
    ("FORGE_RECONCILIATION", "dual-forge-repository-loop", "dual-forge-reconciliation"),
)

DEFAULT_PROFILE = (
    Path(__file__).resolve().parents[1]
    / "references"
    / "repository-control-plane.default.json"
)


class ContractError(RuntimeError):
    """Raised when an input cannot satisfy the control-plane contract."""


def read_json(path: Path, *, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ContractError(f"unreadable {label} {path}: {error}") from error


def canonical_json(document: Any) -> str:
    return json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def sha256_document(document: Any) -> str:
    return hashlib.sha256(canonical_json(document).encode("utf-8")).hexdigest()


def render(document: dict[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def safe_relative(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ContractError(f"{field} must be a non-empty repository-relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ContractError(f"{field} must be a safe repository-relative path")
    return path.as_posix()


def expect_exact_keys(document: dict[str, Any], expected: set[str], *, label: str) -> None:
    actual = set(document)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ContractError(f"{label} keys mismatch: missing={missing} extra={extra}")


def expect_entrypoint(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not ENTRYPOINT_RE.fullmatch(value):
        raise ContractError(f"{field} must be a dotted or dashed entrypoint id")
    return value


def _validate_runtime(runtime: Any) -> None:
    if not isinstance(runtime, dict):
        raise ContractError("runtime must be an object")
    expect_exact_keys(runtime, {"repository_id", "skills", "git_town", "forgejo"}, label="runtime")
    if runtime["repository_id"] != "ed3c/runtime-env":
        raise ContractError("runtime.repository_id must be ed3c/runtime-env")

    skills = runtime["skills"]
    if not isinstance(skills, dict):
        raise ContractError("runtime.skills must be an object")
    expect_exact_keys(
        skills,
        {"scope", "owner", "setup_entrypoint", "probe_entrypoint", "without_receipt"},
        label="runtime.skills",
    )
    if skills["scope"] != "user" or skills["owner"] != "skills-shared":
        raise ContractError("canonical Skill distribution must be user-scoped and skills-shared-owned")
    if skills["setup_entrypoint"] != "shared-skills-infra.install":
        raise ContractError("runtime.skills.setup_entrypoint mismatch")
    if skills["probe_entrypoint"] != "shared-skills-infra.check":
        raise ContractError("runtime.skills.probe_entrypoint mismatch")
    if skills["without_receipt"] != "NOT_EXERCISED":
        raise ContractError("runtime.skills.without_receipt must be NOT_EXERCISED")

    git_town = runtime["git_town"]
    if not isinstance(git_town, dict):
        raise ContractError("runtime.git_town must be an object")
    expect_exact_keys(
        git_town,
        {
            "scope",
            "owner",
            "executable",
            "setup_entrypoint",
            "probe_entrypoint",
            "implementation_state",
            "without_receipt",
        },
        label="runtime.git_town",
    )
    if git_town["scope"] != "user" or git_town["owner"] != "runtime-env":
        raise ContractError("Git Town must be installed once at user scope by runtime-env")
    executable = git_town["executable"]
    if (
        not isinstance(executable, str)
        or not ENTRYPOINT_RE.fullmatch(executable)
        or "/" in executable
        or "\\" in executable
    ):
        raise ContractError("runtime.git_town.executable must be a portable tool name")
    if git_town["setup_entrypoint"] != "repository-control-plane.install-git-town":
        raise ContractError("runtime.git_town.setup_entrypoint mismatch")
    if git_town["probe_entrypoint"] != "repository-control-plane.git-town-version":
        raise ContractError("runtime.git_town.probe_entrypoint mismatch")
    if git_town["implementation_state"] not in {"IMPLEMENTED", "NOT_IMPLEMENTED"}:
        raise ContractError("runtime.git_town.implementation_state is invalid")
    if git_town["without_receipt"] != "NOT_EXERCISED":
        raise ContractError("runtime.git_town.without_receipt must be NOT_EXERCISED")

    forgejo = runtime["forgejo"]
    if not isinstance(forgejo, dict):
        raise ContractError("runtime.forgejo must be an object")
    expect_exact_keys(
        forgejo,
        {
            "scope",
            "owner",
            "endpoint_variable",
            "profile_id",
            "workload_id",
            "probe_entrypoint",
            "without_receipt",
        },
        label="runtime.forgejo",
    )
    if forgejo["scope"] != "host" or forgejo["owner"] != "runtime-env":
        raise ContractError("Forgejo must be one host-scoped service owned by runtime-env")
    expected_forgejo = {
        "endpoint_variable": "FORGEJO_URL",
        "profile_id": "forgejo-delivery-keychain-local",
        "workload_id": "forgejo-delivery-loop",
        "probe_entrypoint": "credential-canary",
    }
    for field, expected in expected_forgejo.items():
        if forgejo[field] != expected:
            raise ContractError(f"runtime.forgejo.{field} mismatch")
    if forgejo["without_receipt"] != "NOT_EXERCISED":
        raise ContractError("runtime.forgejo.without_receipt must be NOT_EXERCISED")


def validate_profile(document: Any) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ContractError("profile must be an object")
    expect_exact_keys(
        document,
        {
            "schema",
            "id",
            "binding",
            "canonical",
            "selected_skills",
            "controller_chain",
            "runtime",
            "monitor",
            "projection",
            "authority",
        },
        label="profile",
    )
    if document["schema"] != "repository-control-plane-profile/v1":
        raise ContractError("profile schema must be repository-control-plane-profile/v1")
    if document["id"] != "skills-shared-default":
        raise ContractError("profile.id must be skills-shared-default")
    if document["binding"] != "repository-control-plane":
        raise ContractError("profile.binding must be repository-control-plane")
    canonical = document["canonical"]
    if not isinstance(canonical, dict):
        raise ContractError("profile.canonical must be an object")
    expect_exact_keys(canonical, {"repository_id", "url"}, label="profile.canonical")
    if canonical != {
        "repository_id": "ed3c/skills-shared",
        "url": "https://github.com/ed3c/skills-shared",
    }:
        raise ContractError("profile.canonical must identify ed3c/skills-shared")

    selected = document["selected_skills"]
    if (
        not isinstance(selected, list)
        or any(not isinstance(item, str) or not SKILL_NAME_RE.fullmatch(item) for item in selected)
        or len(selected) != len(set(selected))
    ):
        raise ContractError("selected_skills must be a unique array of canonical Skill names")

    chain = document["controller_chain"]
    if not isinstance(chain, list):
        raise ContractError("controller_chain must be an array")
    normalized: list[tuple[str, str, str]] = []
    for index, item in enumerate(chain):
        if not isinstance(item, dict):
            raise ContractError(f"controller_chain[{index}] must be an object")
        expect_exact_keys(item, {"phase", "skill", "receipt"}, label=f"controller_chain[{index}]")
        phase, skill, receipt = item["phase"], item["skill"], item["receipt"]
        if not isinstance(phase, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]*", phase):
            raise ContractError(f"controller_chain[{index}].phase is invalid")
        if not isinstance(skill, str) or not SKILL_NAME_RE.fullmatch(skill):
            raise ContractError(f"controller_chain[{index}].skill is invalid")
        expect_entrypoint(receipt, field=f"controller_chain[{index}].receipt")
        normalized.append((phase, skill, receipt))
    if tuple(normalized) != REQUIRED_CHAIN:
        raise ContractError("controller_chain must equal the canonical six-phase chain")
    if selected != [item[1] for item in REQUIRED_CHAIN]:
        raise ContractError("selected_skills must equal controller_chain skill order")

    _validate_runtime(document["runtime"])

    monitor = document["monitor"]
    if not isinstance(monitor, dict):
        raise ContractError("monitor must be an object")
    expect_exact_keys(
        monitor,
        {
            "source",
            "query",
            "mode",
            "polling_scope",
            "input_schema",
            "output_schema",
            "unfinished_states",
        },
        label="monitor",
    )
    if monitor["source"] != "github" or monitor["mode"] != "READ_ONLY_PLAN":
        raise ContractError("the portable monitor may only create a read-only GitHub plan")
    if monitor["polling_scope"] != "host":
        raise ContractError("issue polling must be host-scoped, not copied per repository")
    if monitor["query"] != "is:issue is:open":
        raise ContractError("monitor.query must be is:issue is:open")
    if monitor["input_schema"] != "github-open-issues-snapshot/v1":
        raise ContractError("monitor.input_schema is invalid")
    if monitor["output_schema"] != "repository-control-plane/monitor-plan/v1":
        raise ContractError("monitor.output_schema is invalid")
    if monitor["unfinished_states"] != ["OPEN", "BLOCKED", "IN_PROGRESS", "NOT_EXERCISED"]:
        raise ContractError("monitor.unfinished_states must preserve all unresolved states")

    projection = document["projection"]
    if not isinstance(projection, dict):
        raise ContractError("projection must be an object")
    expect_exact_keys(
        projection,
        {"requirements_path", "control_plane_path", "binding_path", "surfaces"},
        label="projection",
    )
    expected_projection = {
        "requirements_path": ".agents/shared-skills.requirements.json",
        "control_plane_path": ".agents/repository-control-plane.json",
        "binding_path": ".agents/bindings/repository-control-plane.json",
        "surfaces": {"claude": ".claude/skills", "codex": ".agents/skills"},
    }
    if projection != expected_projection:
        raise ContractError("projection must equal the canonical thin attachment paths")
    for field in ("requirements_path", "control_plane_path", "binding_path"):
        safe_relative(projection[field], field=f"projection.{field}")
    for carrier, value in projection["surfaces"].items():
        safe_relative(value, field=f"projection.surfaces.{carrier}")

    authority = document["authority"]
    if not isinstance(authority, dict):
        raise ContractError("authority must be an object")
    expect_exact_keys(
        authority,
        {
            "consumer_mutation",
            "host_install",
            "automatic_merge",
            "automatic_conflict_resolution",
            "visibility_change",
            "skill_body_copy",
            "secret_values",
        },
        label="authority",
    )
    if authority["consumer_mutation"] != "CONSUMER_POLICY_REQUIRED":
        raise ContractError("consumer mutation must remain consumer-policy governed")
    if authority["host_install"] != "HOST_POLICY_REQUIRED":
        raise ContractError("host installation must remain host-policy governed")
    for field in (
        "automatic_merge",
        "automatic_conflict_resolution",
        "visibility_change",
        "skill_body_copy",
    ):
        if authority[field] is not False:
            raise ContractError(f"authority.{field} must be false")
    if authority["secret_values"] != "DENY":
        raise ContractError("authority.secret_values must be DENY")
    return document


def load_profile(path: Path) -> dict[str, Any]:
    return validate_profile(read_json(path, label="profile"))


def validate_repository_id(value: str, *, field: str) -> str:
    if not REPOSITORY_ID_RE.fullmatch(value):
        raise ContractError(f"{field} must use owner/repository form")
    return value


def validate_commit(value: str, *, field: str) -> str:
    if not SHA_RE.fullmatch(value):
        raise ContractError(f"{field} must be an exact 40- or 64-hex commit")
    return value


def build_consumer_documents(
    profile: dict[str, Any],
    *,
    consumer_repository_id: str,
    runtime_env_commit: str,
) -> dict[str, dict[str, Any]]:
    consumer_repository_id = validate_repository_id(
        consumer_repository_id, field="consumer_repository_id"
    )
    runtime_env_commit = validate_commit(runtime_env_commit, field="runtime_env_commit")

    requirements = {
        "schema": "shared-skills/consumer-requirements/v1",
        "binding": profile["binding"],
        "shared": profile["selected_skills"],
        "repo_owned": [],
        "surfaces": profile["projection"]["surfaces"],
    }
    forgejo = profile["runtime"]["forgejo"]
    control = {
        "schema": "repository-control-plane/consumer-binding/v1",
        "consumer_repository_id": consumer_repository_id,
        "profile": {
            "id": profile["id"],
            "content_sha256": sha256_document(profile),
        },
        "skills": {
            "canonical": profile["canonical"],
            "requirements_path": profile["projection"]["requirements_path"],
            "binding_path": profile["projection"]["binding_path"],
            "selected": profile["selected_skills"],
            "body_policy": "CANONICAL_ONLY",
        },
        "runtime_env": {
            "repository_id": profile["runtime"]["repository_id"],
            "commit_sha": runtime_env_commit,
            "profile_ids": [forgejo["profile_id"]],
            "workload_ids": [forgejo["workload_id"]],
            "capabilities": {
                "skill_distribution": profile["runtime"]["skills"],
                "git_town": profile["runtime"]["git_town"],
                "forgejo": forgejo,
            },
        },
        "monitor": {
            **profile["monitor"],
            "controller_chain": profile["controller_chain"],
        },
        "projection": profile["projection"],
        "authority": profile["authority"],
        "generated_by": {
            "tool": "repository_control_plane.py",
            "version": TOOL_VERSION,
        },
    }
    return {
        profile["projection"]["requirements_path"]: requirements,
        profile["projection"]["control_plane_path"]: control,
    }
