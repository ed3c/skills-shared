#!/usr/bin/env python3
"""Validate the skills-shared GitHub Actions publication consumer profile.

Zero network. This gate validates repository-owned configuration only; it does
not produce evidence, publish, rerun, recover billing, transition a PR, or merge.

Exit codes: 0 valid, 2 contract violation, 64 unreadable/missing/tool failure.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
from typing import Any

PROFILE_SCHEMA = "skills-shared-ci-publication-profile/v1"
CONTRACT_SCHEMA = "github-delivery-local-verification-contract/v1"
REPOSITORY_ID = 1326262274
REPOSITORY = "ed3c/skills-shared"
INTENTS = ["initial-pr", "ready-for-review", "batched-repair"]
ENTRYPOINTS = {"local_verification", "github_snapshot", "publication_gate"}
SAFE_ENV = {"PATH", "HOME", "TMPDIR"}
SECRET_ENV_MARKERS = ("TOKEN", "SECRET", "PASSWORD", "PASSWD", "KEY", "COOKIE", "AUTH")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
MACHINE_PATHS = (
    re.compile(r"/Users/"),
    re.compile(r"/home/"),
    re.compile(r"[A-Za-z]:[\\/](?:Users|Documents and Settings)[\\/]"),
    re.compile(r"~/"),
)
SECRET_VALUES = (
    re.compile(r"gh[pousr]_[A-Za-z0-9_]+"),
    re.compile(r"github_pat_[A-Za-z0-9_]+"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),
    re.compile(r"https?://[^\s/:]+:[^\s/@]+@"),
)


class ProfileError(ValueError):
    pass


def load(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProfileError(f"missing {label}: {path}") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProfileError(f"unreadable {label}: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProfileError(f"{label} root must be an object")
    return value


def exact(value: dict[str, Any], fields: set[str], label: str) -> None:
    if set(value) != fields:
        raise ProfileError(
            f"{label} fields drifted: missing={sorted(fields-set(value))} "
            f"extra={sorted(set(value)-fields)}"
        )


def relative(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ProfileError(f"{label} must be a non-empty repository-relative path")
    if any(pattern.search(value) for pattern in MACHINE_PATHS):
        raise ProfileError(f"{label} contains a machine-local path")
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ProfileError(f"{label} must not be absolute or contain '..'")
    return candidate.as_posix()


def positive_int(value: Any, label: str, maximum: int) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 1
        or value > maximum
    ):
        raise ProfileError(f"{label} must be an integer in 1..{maximum}")
    return value


def scan_text(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for pattern in MACHINE_PATHS:
        if pattern.search(text):
            raise ProfileError(f"machine-local path in {path}")
    for pattern in SECRET_VALUES:
        if pattern.search(text):
            raise ProfileError(f"credential-like value in {path}")


def validate_contract(root: Path, path: Path) -> dict[str, Any]:
    value = load(path, "local verification contract")
    exact(value, {"schema", "repository_id", "inherit_env", "commands"}, "contract")
    if value["schema"] != CONTRACT_SCHEMA:
        raise ProfileError(f"contract.schema must be {CONTRACT_SCHEMA}")
    if value["repository_id"] != REPOSITORY_ID:
        raise ProfileError("contract.repository_id drifted")

    inherit = value["inherit_env"]
    if (
        not isinstance(inherit, list)
        or len(inherit) != len(set(inherit))
        or any(not isinstance(item, str) or not item for item in inherit)
    ):
        raise ProfileError("contract.inherit_env must be a unique string list")
    unsafe = sorted(set(inherit) - SAFE_ENV)
    if unsafe:
        raise ProfileError(f"contract inherits unadmitted environment names: {unsafe}")
    for name in inherit:
        if any(marker in name.upper() for marker in SECRET_ENV_MARKERS):
            raise ProfileError(f"secret-bearing environment name is forbidden: {name}")

    commands = value["commands"]
    if not isinstance(commands, list) or not commands:
        raise ProfileError("contract.commands must be a non-empty array")
    seen: set[str] = set()
    for index, command in enumerate(commands):
        label = f"contract.commands[{index}]"
        if not isinstance(command, dict):
            raise ProfileError(f"{label} must be an object")
        exact(
            command,
            {"id", "argv", "cwd", "timeout_seconds", "max_output_bytes"},
            label,
        )
        command_id = command["id"]
        if (
            not isinstance(command_id, str)
            or ID_RE.fullmatch(command_id) is None
            or command_id in seen
        ):
            raise ProfileError(f"invalid or duplicate command id: {command_id!r}")
        seen.add(command_id)
        argv = command["argv"]
        if (
            not isinstance(argv, list)
            or not argv
            or any(not isinstance(item, str) or not item for item in argv)
        ):
            raise ProfileError(f"{label}.argv must be a non-empty string array")
        if argv[0] in {"sh", "bash", "zsh", "fish"} and len(argv) > 1 and argv[1] in {"-c", "-lc"}:
            raise ProfileError(f"{label}.argv may not execute a shell command string")
        for item in argv:
            if "\n" in item or "\r" in item or "\x00" in item:
                raise ProfileError(f"{label}.argv contains a control character")
            if item.startswith(("/", "~/")) or any(pattern.search(item) for pattern in MACHINE_PATHS):
                raise ProfileError(f"{label}.argv contains an absolute/machine path")
        cwd = relative(command["cwd"], f"{label}.cwd")
        if not (root / cwd).resolve().is_relative_to(root.resolve()):
            raise ProfileError(f"{label}.cwd escapes repository")
        positive_int(command["timeout_seconds"], f"{label}.timeout_seconds", 600)
        positive_int(command["max_output_bytes"], f"{label}.max_output_bytes", 1048576)
    return value


def validate(root: Path) -> None:
    profile_path = root / ".github-delivery" / "ci-publication" / "profile.json"
    profile = load(profile_path, "CI publication profile")
    exact(
        profile,
        {
            "schema",
            "repository",
            "stable_check_name",
            "verification_contract",
            "runtime_root",
            "entrypoints",
            "publication_intents",
            "billing_circuit",
            "evidence",
        },
        "profile",
    )
    if profile["schema"] != PROFILE_SCHEMA:
        raise ProfileError(f"profile.schema must be {PROFILE_SCHEMA}")

    repository = profile["repository"]
    if not isinstance(repository, dict):
        raise ProfileError("profile.repository must be an object")
    exact(repository, {"full_name", "repository_id", "private"}, "profile.repository")
    if repository != {
        "full_name": REPOSITORY,
        "repository_id": REPOSITORY_ID,
        "private": True,
    }:
        raise ProfileError("profile repository identity drifted")

    check_name = profile["stable_check_name"]
    if check_name != "contract" or any(token in check_name for token in ("*", "${{", "<", ">")):
        raise ProfileError("stable_check_name must be exact literal 'contract'")

    verification_contract = relative(profile["verification_contract"], "verification_contract")
    expected_contract = ".github-delivery/ci-publication/local-verification.contract.json"
    if verification_contract != expected_contract:
        raise ProfileError(f"verification_contract must be {expected_contract}")
    contract_path = root / verification_contract
    if not contract_path.is_file():
        raise ProfileError(f"verification contract is absent: {verification_contract}")
    validate_contract(root, contract_path)

    runtime_root = relative(profile["runtime_root"], "runtime_root")
    if runtime_root != ".github-delivery/ci-publication/runtime":
        raise ProfileError("runtime_root drifted")
    ignore = root / ".github-delivery" / "ci-publication" / ".gitignore"
    if not ignore.is_file() or "runtime/" not in ignore.read_text(encoding="utf-8").splitlines():
        raise ProfileError("runtime output root is not ignored")

    entrypoints = profile["entrypoints"]
    if not isinstance(entrypoints, dict):
        raise ProfileError("entrypoints must be an object")
    exact(entrypoints, ENTRYPOINTS, "entrypoints")
    for name, raw in entrypoints.items():
        path = relative(raw, f"entrypoints.{name}")
        if not (root / path).is_file():
            raise ProfileError(f"entrypoint is absent: {name}={path}")

    if profile["publication_intents"] != INTENTS:
        raise ProfileError(f"publication_intents must equal {INTENTS}")

    billing = profile["billing_circuit"]
    if not isinstance(billing, dict):
        raise ProfileError("billing_circuit must be an object")
    exact(
        billing,
        {"open_state", "decision", "probe_by_push", "recovery_owner"},
        "billing_circuit",
    )
    if billing != {
        "open_state": "billing-open",
        "decision": "BLOCK",
        "probe_by_push": False,
        "recovery_owner": "ed3c",
    }:
        raise ProfileError("billing circuit must fail closed")

    evidence = profile["evidence"]
    if not isinstance(evidence, dict):
        raise ProfileError("evidence must be an object")
    exact(
        evidence,
        {
            "local_receipt_schema",
            "local_evidence_schema",
            "github_snapshot_schema",
            "sidecar_gate_binding",
            "hosted_exact_head",
        },
        "evidence",
    )
    if evidence != {
        "local_receipt_schema": "github-delivery-local-verification/v1",
        "local_evidence_schema": "github-delivery-local-verification-evidence/v1",
        "github_snapshot_schema": "github-actions-publish-snapshot/v1",
        "sidecar_gate_binding": "NOT_IMPLEMENTED",
        "hosted_exact_head": "NOT_EXERCISED",
    }:
        raise ProfileError("evidence boundary drifted or overclaimed")

    for path in (profile_path, contract_path, ignore):
        scan_text(path)


def fixture(root: Path) -> None:
    base = root / ".github-delivery" / "ci-publication"
    (base / "scripts").mkdir(parents=True)
    (root / "skills" / "github-delivery-loop" / "scripts").mkdir(parents=True)
    for name in ("local_verification.py", "github_actions_snapshot.py", "ci_publish_gate.py"):
        (root / "skills" / "github-delivery-loop" / "scripts" / name).write_text("# fixture\n")
    (root / "skills" / "github-delivery-loop" / "tests").mkdir(parents=True)
    (root / "skills" / "github-delivery-loop" / "evals.json").write_text("{}\n")
    (root / "registry.json").write_text("{}\n")
    (base / ".gitignore").write_text("runtime/\n")
    contract = {
        "schema": CONTRACT_SCHEMA,
        "repository_id": REPOSITORY_ID,
        "inherit_env": ["PATH"],
        "commands": [
            {
                "id": "fixture",
                "argv": ["python3", "-m", "json.tool", "registry.json"],
                "cwd": ".",
                "timeout_seconds": 10,
                "max_output_bytes": 4096,
            }
        ],
    }
    profile = {
        "schema": PROFILE_SCHEMA,
        "repository": {"full_name": REPOSITORY, "repository_id": REPOSITORY_ID, "private": True},
        "stable_check_name": "contract",
        "verification_contract": ".github-delivery/ci-publication/local-verification.contract.json",
        "runtime_root": ".github-delivery/ci-publication/runtime",
        "entrypoints": {
            "local_verification": "skills/github-delivery-loop/scripts/local_verification.py",
            "github_snapshot": "skills/github-delivery-loop/scripts/github_actions_snapshot.py",
            "publication_gate": "skills/github-delivery-loop/scripts/ci_publish_gate.py",
        },
        "publication_intents": list(INTENTS),
        "billing_circuit": {"open_state": "billing-open", "decision": "BLOCK", "probe_by_push": False, "recovery_owner": "ed3c"},
        "evidence": {
            "local_receipt_schema": "github-delivery-local-verification/v1",
            "local_evidence_schema": "github-delivery-local-verification-evidence/v1",
            "github_snapshot_schema": "github-actions-publish-snapshot/v1",
            "sidecar_gate_binding": "NOT_IMPLEMENTED",
            "hosted_exact_head": "NOT_EXERCISED",
        },
    }
    (base / "local-verification.contract.json").write_text(json.dumps(contract, indent=2) + "\n")
    (base / "profile.json").write_text(json.dumps(profile, indent=2) + "\n")


def selftest() -> None:
    with tempfile.TemporaryDirectory(prefix="skills-shared-ci-profile.") as temp:
        root = Path(temp)
        fixture(root)
        validate(root)
        base = root / ".github-delivery" / "ci-publication"
        profile_path = base / "profile.json"
        contract_path = base / "local-verification.contract.json"
        original_profile = json.loads(profile_path.read_text())
        original_contract = json.loads(contract_path.read_text())

        profile_mutations = [
            lambda value: value["repository"].update(repository_id=1),
            lambda value: value.update(stable_check_name="${{ matrix.check }}"),
            lambda value: value["publication_intents"].append("checkpoint"),
            lambda value: value["billing_circuit"].update(probe_by_push=True),
            lambda value: value["evidence"].update(sidecar_gate_binding="PASS"),
        ]
        for index, mutate in enumerate(profile_mutations):
            value = json.loads(json.dumps(original_profile))
            mutate(value)
            profile_path.write_text(json.dumps(value))
            try:
                validate(root)
            except ProfileError:
                pass
            else:
                raise ProfileError(f"profile mutation {index} unexpectedly passed")
        profile_path.write_text(json.dumps(original_profile))

        contract_mutations = [
            lambda value: value.update(repository_id=1),
            lambda value: value.update(inherit_env=["GITHUB_TOKEN"]),
            lambda value: value["commands"][0].update(argv=["bash", "-c", "true"]),
            lambda value: value["commands"][0].update(cwd="/Users/example/project"),
            lambda value: value.update(commands=[]),
        ]
        for index, mutate in enumerate(contract_mutations):
            value = json.loads(json.dumps(original_contract))
            mutate(value)
            contract_path.write_text(json.dumps(value))
            try:
                validate(root)
            except ProfileError:
                pass
            else:
                raise ProfileError(f"contract mutation {index} unexpectedly passed")
        contract_path.write_text(json.dumps(original_contract))
        validate(root)
    print("SELFTEST GREEN: skills-shared CI publication profile (10 mutations killed)")


def default_root() -> Path:
    return Path(__file__).resolve().parents[3]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="check_profile.py")
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.selftest:
            selftest()
        else:
            validate(args.root.resolve())
            print("PASS skills-shared CI publication profile")
        return 0
    except ProfileError as exc:
        print(f"PROFILE RED: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"PROFILE FATAL: {exc}", file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
