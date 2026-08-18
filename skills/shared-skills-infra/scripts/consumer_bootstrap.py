#!/usr/bin/env python3
"""Scaffold and verify a thin, atomic Domain Decoupling consumer bootstrap."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Callable

from consumer_bootstrap_common import (
    BINDING_REL, BootstrapError, PROFILE_REL, PROFILE_SOURCE, RECEIPT_REL,
    RECEIPT_SCHEMA, REQUIREMENTS_REL, REPOSITORY_ID, SOURCE_REL, SOURCE_SCHEMA,
    WORKFLOW_REL, SharedIdentity, canonical, capture, ensure_git_worktree, json_text,
    preflight_generated, read_json, reject_copied_skill_bodies, restore,
    sha256, shared_identity,
)
from consumer_bootstrap_receipt import (
    artifact_records, build_receipt, validate_binding, validate_receipt,
    validate_receipt_shape, validate_rollback,
)
from consumer_bootstrap_routes import (
    BEGIN, DOC_ROUTES, WORKFLOW_MARKER, merge_block, observed_block, route_blocks,
    workflow_text,
)

SHARED_ROOT = Path(__file__).resolve().parents[3]


def default_attach(profile_path: Path, consumer: Path, check: bool) -> None:
    from repository_control_plane import attach
    attach(profile_path, consumer, check=check)


def profile_document(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BootstrapError(f"unreadable control-plane profile: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema") != "repository-control-plane-profile/v1":
        raise BootstrapError("unsupported control-plane profile")
    skills = value.get("skills")
    if not isinstance(skills, list) or not skills or any(not isinstance(item, str) or not item for item in skills):
        raise BootstrapError("control-plane profile Skill closure is invalid")
    authority = value.get("authority")
    if not isinstance(authority, dict) or any(item is not False for item in authority.values()):
        raise BootstrapError("control-plane profile widened automatic authority")
    return value


def route_records(consumer: Path, blocks: dict[Path, str]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for relative, expected in sorted(blocks.items(), key=lambda item: item[0].as_posix()):
        observed = observed_block(consumer / relative)
        if observed != expected:
            raise BootstrapError(f"managed route block drifted: {relative}")
        result.append({
            "path": relative.as_posix(),
            "managed_block_sha256": sha256(observed.encode("utf-8")),
            "state": "MANAGED_BLOCK",
        })
    workflow = consumer / WORKFLOW_REL
    if not workflow.is_file() or workflow.is_symlink():
        raise BootstrapError("generated bootstrap workflow missing or non-regular")
    result.append({"path": WORKFLOW_REL.as_posix(), "sha256": sha256(workflow.read_bytes()), "state": "GENERATED"})
    return result


def generated_paths() -> set[Path]:
    return set(DOC_ROUTES) | {SOURCE_REL, PROFILE_REL, REQUIREMENTS_REL, BINDING_REL, RECEIPT_REL, WORKFLOW_REL}


def preflight(consumer: Path) -> None:
    preflight_generated(consumer / SOURCE_REL, {SOURCE_SCHEMA})
    preflight_generated(consumer / PROFILE_REL, {"repository-control-plane-binding/v1"})
    preflight_generated(consumer / REQUIREMENTS_REL, {"shared-skills/consumer-requirements/v1"})
    preflight_generated(consumer / BINDING_REL, {"shared-skills/consumer-binding/v1"})
    preflight_generated(consumer / RECEIPT_REL, {RECEIPT_SCHEMA})
    preflight_generated(consumer / WORKFLOW_REL, marker=WORKFLOW_MARKER)


def rollback_subject(consumer: Path, initial_commit: str, initial_tree: str) -> dict[str, str]:
    receipt_path = consumer / RECEIPT_REL
    if not receipt_path.is_file():
        return {"commit": initial_commit, "tree": initial_tree}
    receipt = read_json(receipt_path)
    validate_receipt_shape(receipt)
    validate_rollback(consumer, receipt["rollback"])
    return receipt["rollback"]


def apply_routes(consumer: Path, blocks: dict[Path, str], shared_root: Path) -> None:
    for relative, block in blocks.items():
        path = consumer / relative
        current = path.read_text(encoding="utf-8") if path.is_file() else None
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(merge_block(current, block, relative), encoding="utf-8")
    workflow = consumer / WORKFLOW_REL
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text(workflow_text(shared_root), encoding="utf-8")


def bootstrap_consumer(
    *,
    consumer: Path,
    repository_id: str,
    profile_path: Path,
    apply: bool,
    attach_fn: Callable[[Path, Path, bool], None] = default_attach,
    shared_root: Path = SHARED_ROOT,
) -> None:
    if not REPOSITORY_ID.fullmatch(repository_id):
        raise BootstrapError("repository-id must be owner/name")
    consumer = consumer.resolve()
    initial_commit, initial_tree = ensure_git_worktree(consumer)
    identity: SharedIdentity = shared_identity(shared_root)
    profile = profile_document(profile_path)
    skills = profile["skills"]
    blocks = route_blocks(repository_id)
    expected_workflow = workflow_text(shared_root)
    preflight(consumer)
    reject_copied_skill_bodies(consumer, skills)

    if apply:
        rollback = rollback_subject(consumer, initial_commit, initial_tree)
        snapshot = capture(consumer, generated_paths())
        try:
            apply_routes(consumer, blocks, shared_root)
            (consumer / SOURCE_REL).parent.mkdir(parents=True, exist_ok=True)
            (consumer / SOURCE_REL).write_text(json_text(identity.source_document()), encoding="utf-8")
            attach_fn(profile_path, consumer, False)
            reject_copied_skill_bodies(consumer, skills)
            binding = validate_binding(consumer, identity, skills)
            routes = route_records(consumer, blocks)
            artifacts = artifact_records(consumer, routes)
            receipt = build_receipt(repository_id, identity, rollback, artifacts, binding, profile)
            (consumer / RECEIPT_REL).write_text(json_text(receipt), encoding="utf-8")
            validate_receipt(consumer, receipt)
        except Exception:
            restore(consumer, snapshot)
            raise
    else:
        source = read_json(consumer / SOURCE_REL)
        if source != identity.source_document():
            raise BootstrapError("consumer shared-source pin is stale or substituted")
        for relative, expected in blocks.items():
            if observed_block(consumer / relative) != expected:
                raise BootstrapError(f"managed route block drifted: {relative}")
        workflow = consumer / WORKFLOW_REL
        if not workflow.is_file() or workflow.is_symlink() or workflow.read_text(encoding="utf-8") != expected_workflow:
            raise BootstrapError("generated bootstrap workflow drifted")
        attach_fn(profile_path, consumer, True)
        reject_copied_skill_bodies(consumer, skills)
        binding = validate_binding(consumer, identity, skills)
        existing = read_json(consumer / RECEIPT_REL)
        validate_receipt_shape(existing)
        validate_rollback(consumer, existing["rollback"])
        routes = route_records(consumer, blocks)
        artifacts = artifact_records(consumer, routes)
        expected = build_receipt(repository_id, identity, existing["rollback"], artifacts, binding, profile)
        validate_receipt(consumer, expected)

    print(
        "CONSUMER-BOOTSTRAP-GREEN "
        f"consumer={repository_id} shared={identity.commit[:12]} routes={len(blocks)} "
        f"mode={'apply' if apply else 'check'} runtime=NOT_EXERCISED "
        "merge=HUMAN_ADMIT_REQUIRED"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--consumer", required=True, type=Path)
    parser.add_argument("--repository-id", required=True)
    parser.add_argument("--profile", type=Path, default=PROFILE_SOURCE)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    profile = args.profile if args.profile.is_absolute() else SHARED_ROOT / args.profile
    try:
        bootstrap_consumer(
            consumer=args.consumer, repository_id=args.repository_id,
            profile_path=profile, apply=args.apply,
        )
        return 0
    except BootstrapError as exc:
        print(f"CONSUMER-BOOTSTRAP-RED {exc}", file=sys.stderr)
        return 2
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"CONSUMER-BOOTSTRAP-INVALID {exc}", file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
