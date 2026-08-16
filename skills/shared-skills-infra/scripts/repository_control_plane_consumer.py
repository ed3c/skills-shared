"""Consumer attachment writer and structural verifier."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from repository_control_plane_profile import (
    EXIT_ABSENT,
    EXIT_SEMANTIC,
    SHA256_RE,
    SHA_RE,
    ContractError,
    build_consumer_documents,
    read_json,
    render,
    sha256_document,
)


@dataclass(frozen=True)
class AttachmentInspection:
    """A side-effect-free structural inspection result."""

    code: int
    messages: tuple[str, ...]
    control: dict[str, Any] | None


def require_git_worktree(target_root: Path) -> Path:
    """Return the exact Git worktree root; nested paths are rejected."""

    target = target_root.expanduser().resolve()
    try:
        result = subprocess.run(
            ["git", "-C", str(target), "rev-parse", "--show-toplevel"],
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ContractError(f"cannot inspect target Git worktree {target}: {error}") from error
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git rev-parse failed"
        raise ContractError(f"target root is not a Git worktree: {target}: {detail}")
    discovered = Path(result.stdout.strip()).resolve()
    if discovered != target:
        raise ContractError(
            f"target root must equal the Git worktree root: requested={target} actual={discovered}"
        )
    return target


def _repository_path(
    target: Path,
    relative: str,
    *,
    allow_leaf_symlink: bool = False,
) -> tuple[Path, str | None]:
    """Resolve a fixed repo-relative path without following writable parent symlinks."""

    parts = Path(relative).parts
    candidate = target.joinpath(*parts)
    current = target
    for index, part in enumerate(parts):
        current = current / part
        is_leaf = index == len(parts) - 1
        if not os.path.lexists(current):
            continue
        if current.is_symlink():
            if is_leaf and allow_leaf_symlink:
                continue
            return candidate, f"UNSAFE {relative}: symlink component {current.relative_to(target)}"
        if not is_leaf and not current.is_dir():
            return candidate, f"UNSAFE {relative}: parent component is not a directory"
    try:
        resolved_parent = candidate.parent.resolve(strict=False)
    except OSError as error:
        return candidate, f"UNSAFE {relative}: cannot resolve parent: {error}"
    if resolved_parent != target and target not in resolved_parent.parents:
        return candidate, f"UNSAFE {relative}: parent resolves outside the repository"
    return candidate, None


def _atomic_write(destination: Path, content: str) -> None:
    """Replace one source document atomically within its already-checked directory."""

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            os.fchmod(handle.fileno(), 0o600)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, destination)
    except OSError as error:
        try:
            if "temporary" in locals() and temporary.exists():
                temporary.unlink()
        except OSError:
            pass
        raise ContractError(f"cannot atomically write {destination}: {error}") from error


def attach(
    profile: dict[str, Any],
    *,
    target_root: Path,
    consumer_repository_id: str,
    runtime_env_commit: str,
    apply: bool,
    check_only: bool,
) -> int:
    target = require_git_worktree(target_root)
    documents = build_consumer_documents(
        profile,
        consumer_repository_id=consumer_repository_id,
        runtime_env_commit=runtime_env_commit,
    )
    planned: list[tuple[str, Path, str, str | None]] = []
    drift = False
    for relative, document in documents.items():
        destination, unsafe = _repository_path(target, relative)
        if unsafe:
            print(unsafe, file=sys.stderr)
            return EXIT_SEMANTIC
        if os.path.lexists(destination) and not destination.is_file():
            print(f"UNSAFE {relative}: destination is not a regular file", file=sys.stderr)
            return EXIT_SEMANTIC
        try:
            current = destination.read_text(encoding="utf-8") if destination.is_file() else None
        except OSError as error:
            raise ContractError(f"cannot read {destination}: {error}") from error
        expected = render(document)
        planned.append((relative, destination, expected, current))
        if current != expected:
            drift = True

    for relative, destination, expected, current in planned:
        if current == expected:
            print(f"UNCHANGED {relative}")
            continue
        state = "MISSING" if current is None else "DRIFT"
        if check_only:
            print(f"{state} {relative}")
        elif not apply:
            print(f"WOULD-{'CREATE' if current is None else 'UPDATE'} {relative}")
        else:
            # Requirements are rendered first and the control binding last. An
            # interrupted two-file apply therefore fails closed as detectable drift.
            _atomic_write(destination, expected)
            print(f"{'CREATED' if current is None else 'UPDATED'} {relative}")
    if check_only and drift:
        return EXIT_SEMANTIC
    return 0


def _pointer_status(entry: Path, *, skill: str) -> tuple[bool, str]:
    """Accept a live canonical symlink or a bounded, explicit forwarder stub."""

    if entry.is_symlink():
        try:
            resolved = entry.resolve(strict=True)
        except (OSError, RuntimeError) as error:
            return False, f"dangling or cyclic symlink: {error}"
        if not resolved.is_dir() or resolved.name != skill:
            return False, "symlink target is not the named canonical Skill directory"
        if not (resolved / "SKILL.md").is_file():
            return False, "symlink target lacks SKILL.md"
        return True, "canonical symlink"
    if not entry.is_dir():
        return False, "project surface entry is neither a symlink nor a directory"
    try:
        children = sorted(entry.iterdir(), key=lambda item: item.name)
    except OSError as error:
        return False, f"cannot list forwarder: {error}"
    if len(children) != 1 or children[0].name != "SKILL.md":
        return False, "forwarder must contain exactly one SKILL.md"
    forwarder = children[0]
    if forwarder.is_symlink() or not forwarder.is_file():
        return False, "forwarder SKILL.md must be one regular file"
    try:
        if forwarder.stat().st_size > 4096:
            return False, "forwarder exceeds the 4096-byte body-copy ceiling"
        content = forwarder.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return False, f"cannot read forwarder: {error}"
    required = (
        f"name: {skill}",
        "disable-model-invocation: true",
        "$ARGUMENTS",
    )
    missing = [marker for marker in required if marker not in content]
    if missing:
        return False, f"forwarder markers missing: {', '.join(missing)}"
    return True, "bounded forwarder"


def _validate_generated_binding(
    binding: Any,
    *,
    profile: dict[str, Any],
    requirements_bytes: bytes,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(binding, dict):
        return ["generated Skill binding must be an object"]
    expected_keys = {
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
    if set(binding) != expected_keys:
        errors.append(
            "generated Skill binding keys mismatch: "
            f"missing={sorted(expected_keys - set(binding))} "
            f"extra={sorted(set(binding) - expected_keys)}"
        )
    if binding.get("schema") != "shared-skills/consumer-binding/v1":
        errors.append("generated Skill binding schema mismatch")
    if binding.get("binding") != profile["binding"]:
        errors.append("generated Skill binding id mismatch")
    registry_digest = binding.get("registry_sha256")
    if not isinstance(registry_digest, str) or not SHA256_RE.fullmatch(registry_digest):
        errors.append("generated Skill binding registry digest is invalid")
    expected_requirements = hashlib.sha256(requirements_bytes).hexdigest()
    if binding.get("requirements_sha256") != expected_requirements:
        errors.append("generated Skill binding requirements digest mismatch")
    if binding.get("repo_owned") != []:
        errors.append("generated Skill binding repo_owned must remain empty")
    if binding.get("surfaces") != profile["projection"]["surfaces"]:
        errors.append("generated Skill binding surfaces mismatch")

    source = binding.get("source")
    if not isinstance(source, dict) or set(source) != {"commit", "repository", "tree"}:
        errors.append("generated Skill binding source shape mismatch")
    else:
        if not SHA_RE.fullmatch(str(source.get("commit", ""))):
            errors.append("generated Skill binding lacks an exact canonical commit")
        if not SHA_RE.fullmatch(str(source.get("tree", ""))):
            errors.append("generated Skill binding lacks an exact canonical tree")
        if source.get("repository") != profile["canonical"]["url"]:
            errors.append("generated Skill binding canonical repository mismatch")

    skills = binding.get("skills")
    if not isinstance(skills, list):
        errors.append("generated Skill binding skills must be an array")
    else:
        names: list[str] = []
        for index, skill in enumerate(skills):
            if not isinstance(skill, dict):
                errors.append(f"generated Skill binding skills[{index}] is not an object")
                continue
            if set(skill) != {"name", "content_sha256", "entrypoint"}:
                errors.append(f"generated Skill binding skills[{index}] keys mismatch")
            name = skill.get("name")
            digest = skill.get("content_sha256")
            entrypoint = skill.get("entrypoint")
            if not isinstance(name, str):
                errors.append(f"generated Skill binding skills[{index}] lacks name")
                continue
            names.append(name)
            if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
                errors.append(f"generated Skill binding {name} lacks a full content digest")
            if entrypoint != f"skills/{name}/SKILL.md":
                errors.append(f"generated Skill binding {name} entrypoint mismatch")
        expected_names = sorted(profile["selected_skills"])
        if names != expected_names:
            errors.append("generated Skill binding selected Skill closure/order mismatch")
        if len(names) != len(set(names)):
            errors.append("generated Skill binding contains duplicate Skill names")

    content_digest = binding.get("content_sha256")
    if not isinstance(content_digest, str) or not SHA256_RE.fullmatch(content_digest):
        errors.append("generated Skill binding content digest is invalid")
    else:
        unsigned = dict(binding)
        unsigned.pop("content_sha256", None)
        if content_digest != sha256_document(unsigned):
            errors.append("generated Skill binding content digest mismatch")
    return errors


def inspect_attachment(
    profile: dict[str, Any],
    *,
    target_root: Path,
) -> AttachmentInspection:
    """Inspect a consumer without printing or mutating it."""

    target = require_git_worktree(target_root)
    requirements_relative = profile["projection"]["requirements_path"]
    control_relative = profile["projection"]["control_plane_path"]
    source_paths: dict[str, Path] = {}
    source_violations: list[str] = []
    for relative in (requirements_relative, control_relative):
        path, unsafe = _repository_path(target, relative)
        if unsafe:
            source_violations.append(unsafe)
        elif os.path.lexists(path) and not path.is_file():
            source_violations.append(f"UNSAFE {relative}: source is not a regular file")
        source_paths[relative] = path
    if source_violations:
        return AttachmentInspection(EXIT_SEMANTIC, tuple(source_violations), None)

    missing_sources = [relative for relative, path in source_paths.items() if not path.is_file()]
    if missing_sources:
        return AttachmentInspection(
            EXIT_ABSENT,
            (f"ABSENT source attachment files: {', '.join(missing_sources)}",),
            None,
        )

    requirements_path = source_paths[requirements_relative]
    control_path = source_paths[control_relative]
    requirements = read_json(requirements_path, label="consumer requirements")
    control = read_json(control_path, label="consumer control-plane binding")
    if not isinstance(requirements, dict):
        raise ContractError("consumer requirements must be an object")
    if not isinstance(control, dict):
        raise ContractError("consumer control-plane binding must be an object")
    try:
        consumer_id = control["consumer_repository_id"]
        runtime_commit = control["runtime_env"]["commit_sha"]
    except (KeyError, TypeError) as error:
        raise ContractError(f"consumer control-plane binding is incomplete: {error}") from error

    expected = build_consumer_documents(
        profile,
        consumer_repository_id=consumer_id,
        runtime_env_commit=runtime_commit,
    )
    violations: list[str] = []
    if requirements != expected[requirements_relative]:
        violations.append("consumer requirements drift from the profile")
    if control != expected[control_relative]:
        violations.append("consumer control-plane binding drift from the profile")

    for carrier, surface in profile["projection"]["surfaces"].items():
        root, unsafe = _repository_path(target, surface)
        if unsafe:
            violations.append(unsafe)
            continue
        if os.path.lexists(root) and not root.is_dir():
            violations.append(f"UNSAFE {surface}: project surface is not a directory")
            continue
        if not root.is_dir():
            continue
        for skill in profile["selected_skills"]:
            entry = root / skill
            if not os.path.lexists(entry):
                continue
            pointer, reason = _pointer_status(entry, skill=skill)
            if not pointer:
                violations.append(
                    f"SHADOWED {skill}: {carrier} project surface keeps a body copy ({reason})"
                )

    if violations:
        return AttachmentInspection(EXIT_SEMANTIC, tuple(violations), control)

    binding_relative = profile["projection"]["binding_path"]
    binding_path, unsafe = _repository_path(target, binding_relative)
    if unsafe:
        return AttachmentInspection(EXIT_SEMANTIC, (unsafe,), control)
    if os.path.lexists(binding_path) and not binding_path.is_file():
        return AttachmentInspection(
            EXIT_SEMANTIC,
            (f"UNSAFE {binding_relative}: generated binding is not a regular file",),
            control,
        )
    if not binding_path.is_file():
        return AttachmentInspection(
            EXIT_ABSENT,
            (f"NOT_EXERCISED BINDING_ABSENT {binding_relative}",),
            control,
        )
    binding = read_json(binding_path, label="generated Skill binding")
    binding_errors = _validate_generated_binding(
        binding,
        profile=profile,
        requirements_bytes=requirements_path.read_bytes(),
    )
    if binding_errors:
        return AttachmentInspection(EXIT_SEMANTIC, tuple(binding_errors), control)
    return AttachmentInspection(
        0,
        (
            "PASS repository control-plane attachment is structurally closed; "
            "host tool and forge execution remain receipt-scoped",
        ),
        control,
    )


def verify(profile: dict[str, Any], *, target_root: Path) -> int:
    inspection = inspect_attachment(profile, target_root=target_root)
    stream = sys.stdout if inspection.code == 0 else sys.stderr
    for message in inspection.messages:
        print(message, file=stream)
    return inspection.code
