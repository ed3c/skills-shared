#!/usr/bin/env python3
"""Portable primitives for Domain Decoupling consumer bootstrap."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
REPOSITORY_ID = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
FORBIDDEN_KEYS = {
    "api_key", "access_token", "bearer_token", "client_secret", "credential_value",
    "password", "private_key", "chain_of_thought", "hidden_reasoning",
    "private_reasoning", "reasoning_trace", "scratchpad",
}
ABSOLUTE_HOST = re.compile(r"(?:^|[\s`'\"])(?:/Users/|/home/|[A-Za-z]:\\\\Users\\\\)")

SOURCE_REL = Path(".agents/control-plane/source.json")
PROFILE_REL = Path(".agents/control-plane/profile.json")
REQUIREMENTS_REL = Path(".agents/control-plane/requirements.json")
BINDING_REL = Path(".agents/bindings/repository-control-plane.json")
RECEIPT_REL = Path(".agents/control-plane/bootstrap-receipt.json")
WORKFLOW_REL = Path(".github/workflows/domain-decoupling-bootstrap.yml")
DOMAIN_CONTRACT = Path("docs/architecture/DOMAIN_DECOUPLING.md")
GENERATOR = Path("skills/shared-skills-infra/scripts/shared_skills.py")
PROFILE_SOURCE = Path("skills/shared-skills-infra/references/repository-control-plane-profile.default.json")
WORKFLOW_ADAPTER = Path("skills/shared-skills-infra/modules/github-actions-consumer-bootstrap.yml")
SOURCE_SCHEMA = "shared-skills/source-pin/v1"
RECEIPT_SCHEMA = "shared-skills/consumer-bootstrap-receipt/v1"


class BootstrapError(ValueError):
    """A deterministic bootstrap invariant failed."""


@dataclass(frozen=True)
class SharedIdentity:
    repository: str
    commit: str
    tree: str
    interface_blob: str
    interface_sha256: str
    generator_blob: str
    generator_sha256: str
    profile_blob: str
    profile_sha256: str
    adapter_blob: str
    adapter_sha256: str

    def source_document(self) -> dict[str, Any]:
        return {
            "schema": SOURCE_SCHEMA,
            "source": {"repository": self.repository, "commit": self.commit, "tree": self.tree},
            "interface": {
                "id": "DOMAIN-DECOUPLING-V1", "path": DOMAIN_CONTRACT.as_posix(),
                "git_blob": self.interface_blob, "sha256": self.interface_sha256,
            },
            "generator": {
                "path": GENERATOR.as_posix(), "git_blob": self.generator_blob,
                "sha256": self.generator_sha256,
            },
            "profile": {
                "path": PROFILE_SOURCE.as_posix(), "git_blob": self.profile_blob,
                "sha256": self.profile_sha256,
            },
            "adapter": {
                "id": "github-actions-consumer-bootstrap/v1",
                "path": WORKFLOW_ADAPTER.as_posix(), "git_blob": self.adapter_blob,
                "sha256": self.adapter_sha256,
            },
        }


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True, check=False)
    if check and result.returncode:
        raise BootstrapError(result.stderr.strip() or result.stdout.strip() or f"git {' '.join(args)} failed")
    return result


def git_out(root: Path, *args: str) -> str:
    return run_git(root, *args).stdout.strip()


def ensure_git_worktree(root: Path) -> tuple[str, str]:
    probe = run_git(root, "rev-parse", "--is-inside-work-tree", check=False)
    if probe.returncode or probe.stdout.strip() != "true":
        raise BootstrapError(f"not a Git worktree: {root}")
    commit, tree = git_out(root, "rev-parse", "HEAD"), git_out(root, "rev-parse", "HEAD^{tree}")
    if not HEX40.fullmatch(commit) or not HEX40.fullmatch(tree):
        raise BootstrapError("consumer requires an initial immutable commit/tree")
    return commit, tree


def repository_url(root: Path) -> str:
    remotes = set(git_out(root, "remote").splitlines())
    for name in ("github", "github-archive", "origin", "forgejo"):
        if name not in remotes:
            continue
        value = git_out(root, "remote", "get-url", name).removesuffix(".git")
        if value.startswith("git@") and ":" in value:
            host, path = value[4:].split(":", 1)
            value = f"https://{host}/{path}"
        if not value.startswith(("https://", "http://")) or "@" in value.split("://", 1)[1].split("/", 1)[0]:
            continue
        return value
    raise BootstrapError("skills-shared requires a credential-free HTTP(S) remote")


def file_identity(root: Path, relative: Path) -> tuple[str, str]:
    path = root / relative
    if not path.is_file() or path.is_symlink():
        raise BootstrapError(f"required shared artifact absent or non-regular: {relative}")
    blob = git_out(root, "rev-parse", f"HEAD:{relative.as_posix()}")
    if not HEX40.fullmatch(blob):
        raise BootstrapError(f"invalid Git blob for {relative}")
    return blob, sha256(path.read_bytes())


def shared_identity(root: Path) -> SharedIdentity:
    if git_out(root, "status", "--porcelain", "--untracked-files=all"):
        raise BootstrapError("skills-shared source must be clean")
    commit, tree = git_out(root, "rev-parse", "HEAD"), git_out(root, "rev-parse", "HEAD^{tree}")
    if not HEX40.fullmatch(commit) or not HEX40.fullmatch(tree):
        raise BootstrapError("invalid skills-shared commit/tree")
    domain = (root / DOMAIN_CONTRACT).read_bytes()
    if b"DOMAIN-DECOUPLING-V1" not in domain or b"CANONICAL_METHOD" not in domain:
        raise BootstrapError("canonical Domain Decoupling markers are absent")
    ib, ih = file_identity(root, DOMAIN_CONTRACT)
    gb, gh = file_identity(root, GENERATOR)
    pb, ph = file_identity(root, PROFILE_SOURCE)
    ab, ah = file_identity(root, WORKFLOW_ADAPTER)
    return SharedIdentity(repository_url(root), commit, tree, ib, ih, gb, gh, pb, ph, ab, ah)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BootstrapError(f"unreadable JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BootstrapError(f"JSON root must be an object: {path}")
    reject_unsafe(value, str(path))
    return value


def reject_unsafe(value: Any, trail: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in FORBIDDEN_KEYS:
                raise BootstrapError(f"forbidden secret/private-reasoning field at {trail}.{key}")
            reject_unsafe(child, f"{trail}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_unsafe(child, f"{trail}[{index}]")
    elif isinstance(value, str) and ABSOLUTE_HOST.search(value):
        raise BootstrapError(f"machine-local absolute path at {trail}")


def preflight_generated(path: Path, schemas: set[str] | None = None, marker: str | None = None) -> None:
    if path.is_symlink():
        raise BootstrapError(f"generated authority cannot be a symlink: {path}")
    if path.exists() and not path.is_file():
        raise BootstrapError(f"generated authority is not a regular file: {path}")
    if not path.is_file():
        return
    if marker is not None:
        if not path.read_text(encoding="utf-8").startswith(marker + "\n"):
            raise BootstrapError(f"refuse to overwrite human-owned file: {path}")
        return
    if schemas is not None and read_json(path).get("schema") not in schemas:
        raise BootstrapError(f"refuse to overwrite unrecognized generated file: {path}")


def capture(root: Path, relative_paths: set[Path]) -> dict[Path, bytes | None]:
    result: dict[Path, bytes | None] = {}
    for relative in relative_paths:
        path = root / relative
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise BootstrapError(f"bootstrap target must be absent or a regular file: {relative}")
        result[relative] = path.read_bytes() if path.is_file() else None
    return result


def restore(root: Path, snapshot: dict[Path, bytes | None]) -> None:
    for relative, original in snapshot.items():
        path = root / relative
        if original is None:
            if path.is_file() or path.is_symlink():
                path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(original)
    for parent in sorted({(root / p).parent for p, v in snapshot.items() if v is None}, key=lambda p: len(p.parts), reverse=True):
        current = parent
        while current != root and current.is_dir():
            try:
                current.rmdir()
            except OSError:
                break
            current = current.parent


def reject_copied_skill_bodies(consumer: Path, skills: list[str]) -> None:
    for surface in (consumer / ".agents/skills", consumer / ".claude/skills"):
        for name in skills:
            candidate = surface / name
            if candidate.exists() and not candidate.is_symlink():
                raise BootstrapError(f"consumer-local body shadows canonical shared Skill: {candidate}")
