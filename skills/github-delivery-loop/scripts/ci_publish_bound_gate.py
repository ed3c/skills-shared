#!/usr/bin/env python3
"""Strict publication gate that binds the compact receipt to its evidence sidecar.

This is the admitted v2 entrypoint for private-repository publication. It keeps
`ci_publish_gate.py` as the decision-policy module, but refuses to call that
policy until the detailed local evidence is subject-bound and content-addressed.

Exit codes:
  0  ALLOW one publication operation
  2  BLOCK by publication policy
  64 missing/malformed/stale/forged evidence or local Git failure
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from typing import Any

import ci_publish_gate as policy

EVIDENCE_SCHEMA = "github-delivery-local-verification-evidence/v1"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
MACHINE_PATHS = (
    re.compile(r"^/Users/"),
    re.compile(r"^/home/"),
    re.compile(r"^[A-Za-z]:[\\/](?:Users|Documents and Settings)[\\/]"),
    re.compile(r"^~/"),
)
COMMAND_FIELDS = {
    "id",
    "argv",
    "cwd",
    "timeout_seconds",
    "max_output_bytes",
    "started_at",
    "duration_ms",
    "exit",
    "timed_out",
    "spawn_error",
    "stdout_bytes",
    "stderr_bytes",
    "stdout_sha256",
    "stderr_sha256",
    "stdout_truncated",
    "stderr_truncated",
}
EVIDENCE_FIELDS = {
    "schema",
    "repository_id",
    "head_sha",
    "tree_sha",
    "contract_sha256",
    "verified_at",
    "clean_subject",
    "commands",
    "status",
    "content_sha256",
}


class EvidenceError(policy.InputError):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def require_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or SHA_RE.fullmatch(value) is None:
        raise EvidenceError(f"{label} must be an exact lowercase 40-character SHA")
    return value


def require_digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or DIGEST_RE.fullmatch(value) is None:
        raise EvidenceError(f"{label} must be a lowercase SHA-256")
    return value


def nonnegative(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise EvidenceError(f"{label} must be a non-negative integer")
    return value


def positive(value: Any, label: str) -> int:
    result = nonnegative(value, label)
    if result < 1:
        raise EvidenceError(f"{label} must be positive")
    return result


def safe_path(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise EvidenceError(f"{label} must be a non-empty repository-relative path")
    if any(pattern.search(value) for pattern in MACHINE_PATHS):
        raise EvidenceError(f"{label} contains a machine-local path")
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise EvidenceError(f"{label} must be repository-relative without '..'")
    return candidate.as_posix()


def safe_argv(value: Any, label: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise EvidenceError(f"{label} must be a non-empty string argv array")
    result = list(value)
    for index, item in enumerate(result):
        if any(character in item for character in ("\x00", "\n", "\r")):
            raise EvidenceError(f"{label}[{index}] contains a control character")
        if item.startswith(("/", "~/")) or any(
            pattern.search(item) for pattern in MACHINE_PATHS
        ):
            raise EvidenceError(f"{label}[{index}] contains an absolute/machine path")
    if result[0] in {"sh", "bash", "zsh", "fish"} and len(result) > 1 and result[1] in {"-c", "-lc"}:
        raise EvidenceError(f"{label} may not contain a shell command string")
    return result


def git_tree(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD^{tree}"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise EvidenceError(
            f"cannot resolve local Git tree: {result.stderr.strip() or result.stdout.strip()}"
        )
    return require_sha(result.stdout.strip(), "local Git tree")


def validate_command(value: Any, index: int) -> str:
    label = f"verification evidence commands[{index}]"
    if not isinstance(value, dict):
        raise EvidenceError(f"{label} must be an object")
    if set(value) != COMMAND_FIELDS:
        raise EvidenceError(
            f"{label} fields drifted: missing={sorted(COMMAND_FIELDS-set(value))} "
            f"extra={sorted(set(value)-COMMAND_FIELDS)}"
        )
    command_id = value["id"]
    if not isinstance(command_id, str) or ID_RE.fullmatch(command_id) is None:
        raise EvidenceError(f"{label}.id is invalid")
    safe_argv(value["argv"], f"{label}.argv")
    safe_path(value["cwd"], f"{label}.cwd")
    positive(value["timeout_seconds"], f"{label}.timeout_seconds")
    positive(value["max_output_bytes"], f"{label}.max_output_bytes")
    policy.parse_time(value["started_at"], f"{label}.started_at")
    nonnegative(value["duration_ms"], f"{label}.duration_ms")
    if value["exit"] != 0:
        raise EvidenceError(f"{label}.exit must be 0 for PASS evidence")
    if value["timed_out"] is not False:
        raise EvidenceError(f"{label}.timed_out must be false")
    if value["spawn_error"] is not None:
        raise EvidenceError(f"{label}.spawn_error must be null")
    nonnegative(value["stdout_bytes"], f"{label}.stdout_bytes")
    nonnegative(value["stderr_bytes"], f"{label}.stderr_bytes")
    require_digest(value["stdout_sha256"], f"{label}.stdout_sha256")
    require_digest(value["stderr_sha256"], f"{label}.stderr_sha256")
    if value["stdout_truncated"] is not False or value["stderr_truncated"] is not False:
        raise EvidenceError(f"{label} may not be truncated")
    return command_id


def validate_evidence(
    evidence: dict[str, Any],
    verification: dict[str, Any],
    repository_id: int,
    actual_head: str,
    actual_tree: str,
) -> None:
    if set(evidence) != EVIDENCE_FIELDS:
        raise EvidenceError(
            f"verification evidence fields drifted: "
            f"missing={sorted(EVIDENCE_FIELDS-set(evidence))} "
            f"extra={sorted(set(evidence)-EVIDENCE_FIELDS)}"
        )
    if evidence["schema"] != EVIDENCE_SCHEMA:
        raise EvidenceError(f"verification evidence schema must be {EVIDENCE_SCHEMA}")
    if evidence["repository_id"] != repository_id:
        raise EvidenceError("verification evidence repository identity mismatch")
    if require_sha(evidence["head_sha"], "verification evidence head") != actual_head:
        raise EvidenceError("verification evidence is stale for local HEAD")
    if require_sha(evidence["tree_sha"], "verification evidence tree") != actual_tree:
        raise EvidenceError("verification evidence tree does not match local HEAD tree")
    require_digest(evidence["contract_sha256"], "verification evidence contract_sha256")
    policy.parse_time(evidence["verified_at"], "verification evidence verified_at")
    if evidence["verified_at"] != verification["verified_at"]:
        raise EvidenceError("compact receipt and evidence timestamps differ")
    if evidence["clean_subject"] is not True:
        raise EvidenceError("verification evidence must record a clean subject")
    if evidence["status"] != "PASS" or verification["status"] != "PASS":
        raise EvidenceError("compact receipt and detailed evidence must both be PASS")

    commands = evidence["commands"]
    if not isinstance(commands, list) or not commands:
        raise EvidenceError("verification evidence commands must be non-empty")
    command_ids = [validate_command(item, index) for index, item in enumerate(commands)]
    if len(command_ids) != len(set(command_ids)):
        raise EvidenceError("verification evidence contains duplicate command IDs")
    if verification["commands"] != command_ids:
        raise EvidenceError("compact receipt command IDs do not match detailed evidence order")

    self_digest = require_digest(
        evidence["content_sha256"], "verification evidence content_sha256"
    )
    unsigned = dict(evidence)
    unsigned.pop("content_sha256")
    if digest(unsigned) != self_digest:
        raise EvidenceError("verification evidence self-digest is invalid")

    compact_digest = require_digest(
        verification["evidence_sha256"], "compact receipt evidence_sha256"
    )
    if digest(evidence) != compact_digest:
        raise EvidenceError("compact receipt does not bind the supplied evidence sidecar")


def emit(decision: policy.Decision, json_mode: bool, stream: Any = sys.stdout) -> None:
    policy.emit(decision, json_mode, stream=stream)


def fixture_evidence(head: str, tree: str) -> tuple[dict[str, Any], dict[str, Any]]:
    command = {
        "id": "fixture",
        "argv": ["python3", "-m", "json.tool", "registry.json"],
        "cwd": ".",
        "timeout_seconds": 10,
        "max_output_bytes": 4096,
        "started_at": "2026-08-12T05:00:00Z",
        "duration_ms": 10,
        "exit": 0,
        "timed_out": False,
        "spawn_error": None,
        "stdout_bytes": 3,
        "stderr_bytes": 0,
        "stdout_sha256": "a" * 64,
        "stderr_sha256": hashlib.sha256(b"").hexdigest(),
        "stdout_truncated": False,
        "stderr_truncated": False,
    }
    evidence: dict[str, Any] = {
        "schema": EVIDENCE_SCHEMA,
        "repository_id": 1326262274,
        "head_sha": head,
        "tree_sha": tree,
        "contract_sha256": "b" * 64,
        "verified_at": "2026-08-12T05:00:00Z",
        "clean_subject": True,
        "commands": [command],
        "status": "PASS",
    }
    evidence["content_sha256"] = digest(evidence)
    verification = {
        "schema": policy.VERIFICATION_SCHEMA,
        "repository_id": 1326262274,
        "head_sha": head,
        "status": "PASS",
        "verified_at": evidence["verified_at"],
        "evidence_sha256": digest(evidence),
        "commands": ["fixture"],
    }
    return verification, evidence


def selftest() -> None:
    head = "1" * 40
    tree = "2" * 40
    verification, evidence = fixture_evidence(head, tree)
    validate_evidence(evidence, verification, 1326262274, head, tree)

    mutations = []
    changed = json.loads(json.dumps(evidence))
    changed["commands"][0]["stdout_bytes"] += 1
    mutations.append(("sidecar-byte", verification, changed))
    forged = json.loads(json.dumps(verification))
    forged["evidence_sha256"] = "f" * 64
    mutations.append(("forged-compact", forged, evidence))
    wrong_head = json.loads(json.dumps(evidence))
    wrong_head["head_sha"] = "3" * 40
    mutations.append(("wrong-head", verification, wrong_head))
    wrong_tree = json.loads(json.dumps(evidence))
    wrong_tree["tree_sha"] = "4" * 40
    mutations.append(("wrong-tree", verification, wrong_tree))
    failed = json.loads(json.dumps(evidence))
    failed["status"] = "FAIL"
    mutations.append(("failed-status", verification, failed))
    timeout = json.loads(json.dumps(evidence))
    timeout["commands"][0]["timed_out"] = True
    mutations.append(("timed-out", verification, timeout))
    duplicate = json.loads(json.dumps(evidence))
    duplicate["commands"].append(json.loads(json.dumps(duplicate["commands"][0])))
    mutations.append(("duplicate-id", verification, duplicate))
    machine = json.loads(json.dumps(evidence))
    machine["commands"][0]["cwd"] = "/Users/example/repo"
    mutations.append(("machine-path", verification, machine))

    for name, compact, sidecar in mutations:
        try:
            validate_evidence(sidecar, compact, 1326262274, head, tree)
        except EvidenceError:
            pass
        else:
            raise EvidenceError(f"mutation unexpectedly passed: {name}")
    print("SELFTEST GREEN: compact receipt is bound to detailed evidence (8 mutations killed)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ci_publish_bound_gate.py")
    parser.add_argument("--selftest", action="store_true")
    subs = parser.add_subparsers(dest="command")
    evaluate_parser = subs.add_parser("evaluate")
    evaluate_parser.add_argument("--snapshot", type=Path, required=True)
    evaluate_parser.add_argument("--verification", type=Path, required=True)
    evaluate_parser.add_argument("--verification-evidence", type=Path, required=True)
    evaluate_parser.add_argument("--recovery", type=Path)
    evaluate_parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    evaluate_parser.add_argument("--intent", choices=sorted(policy.INTENTS), required=True)
    evaluate_parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        if args.command is not None:
            parser.error("--selftest cannot be combined with a command")
        try:
            selftest()
            return 0
        except (policy.InputError, OSError) as exc:
            print(f"SELFTEST RED: {exc}", file=sys.stderr)
            return 1

    if args.command != "evaluate":
        parser.error("evaluate or --selftest is required")

    try:
        snapshot = policy.load_object(args.snapshot, "publish snapshot")
        verification = policy.load_object(args.verification, "local verification receipt")
        evidence = policy.load_object(
            args.verification_evidence, "local verification evidence"
        )
        recovery = (
            policy.load_object(args.recovery, "billing recovery receipt")
            if args.recovery is not None
            else None
        )
        root = args.repo_root.resolve()
        actual_head = policy.git_head(root)
        actual_tree = git_tree(root)
        repository = snapshot.get("repository")
        if not isinstance(repository, dict) or not isinstance(
            repository.get("repository_id"), int
        ):
            raise EvidenceError("snapshot repository identity is absent")
        validate_evidence(
            evidence,
            verification,
            repository["repository_id"],
            actual_head,
            actual_tree,
        )
        decision = policy.evaluate(
            snapshot,
            verification,
            args.intent,
            actual_head,
            recovery,
        )
        emit(decision, args.json)
        return 0 if decision.decision == "ALLOW" else 2
    except policy.InputError as exc:
        decision = policy.Decision(
            "BLOCK",
            "invalid-policy-input",
            args.intent,
            None,
            detail=str(exc),
        )
        emit(decision, args.json, stream=sys.stderr)
        return 64
    except OSError as exc:
        print(f"BLOCK local-io-failure detail={exc}", file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
