#!/usr/bin/env python3
"""Validate the admitted skills-shared private-Actions publication profile.

Zero network. Validates repository-owned configuration only; never produces
live evidence, pushes, reruns, transitions, recovers billing, merges, or changes
permissions. Exit: 0 valid, 2 contract RED, 64 missing/unreadable/tool failure.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
from typing import Any

PROFILE_SCHEMA = "skills-shared-ci-publication-profile/v1"
CONTRACT_SCHEMA = "github-delivery-local-verification-contract/v1"
REPOSITORY_ID = 1326262274
REPOSITORY = "ed3c/skills-shared"
INTENTS = ["initial-pr", "ready-for-review", "batched-repair"]
ENTRYPOINTS = {
    "local_verification": "skills/github-delivery-loop/scripts/local_verification.py",
    "github_snapshot": "skills/github-delivery-loop/scripts/github_actions_snapshot.py",
    "publication_gate": "skills/github-delivery-loop/scripts/ci_publish_admitted.py",
}
SAFE_ENV = {"PATH", "HOME", "TMPDIR"}
SECRET_MARKERS = ("TOKEN", "SECRET", "PASSWORD", "PASSWD", "KEY", "COOKIE", "AUTH")
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


def bounded_int(value: Any, label: str, maximum: int) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 1
        or value > maximum
    ):
        raise ProfileError(f"{label} must be an integer in 1..{maximum}")
    return value


def scan(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for pattern in MACHINE_PATHS:
        if pattern.search(text):
            raise ProfileError(f"machine-local path in {path}")
    for pattern in SECRET_VALUES:
        if pattern.search(text):
            raise ProfileError(f"credential-like value in {path}")


def validate_contract(root: Path, path: Path) -> None:
    value = load(path, "local verification contract")
    exact(value, {"schema", "repository_id", "inherit_env", "commands"}, "contract")
    if value["schema"] != CONTRACT_SCHEMA:
        raise ProfileError(f"contract.schema must be {CONTRACT_SCHEMA}")
    if value["repository_id"] != REPOSITORY_ID:
        raise ProfileError("contract.repository_id drifted")

    inherited = value["inherit_env"]
    if (
        not isinstance(inherited, list)
        or len(inherited) != len(set(inherited))
        or any(not isinstance(item, str) or not item for item in inherited)
    ):
        raise ProfileError("contract.inherit_env must be a unique string list")
    unsafe = sorted(set(inherited) - SAFE_ENV)
    if unsafe:
        raise ProfileError(f"unadmitted environment names: {unsafe}")
    for name in inherited:
        if any(marker in name.upper() for marker in SECRET_MARKERS):
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
            raise ProfileError(f"{label}.argv may not execute a shell string")
        for item in argv:
            if any(character in item for character in ("\n", "\r", "\x00")):
                raise ProfileError(f"{label}.argv contains a control character")
            if item.startswith(("/", "~/")) or any(
                pattern.search(item) for pattern in MACHINE_PATHS
            ):
                raise ProfileError(f"{label}.argv contains an absolute/machine path")
        relative(command["cwd"], f"{label}.cwd")
        bounded_int(command["timeout_seconds"], f"{label}.timeout_seconds", 600)
        bounded_int(command["max_output_bytes"], f"{label}.max_output_bytes", 1048576)


def validate(root: Path) -> None:
    base = root / ".github-delivery" / "ci-publication"
    profile_path = base / "profile.json"
    contract_path = base / "local-verification.contract.json"
    ignore_path = base / ".gitignore"
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
    if repository != {
        "full_name": REPOSITORY,
        "repository_id": REPOSITORY_ID,
        "private": True,
    }:
        raise ProfileError("profile repository identity drifted")
    if profile["stable_check_name"] != "contract":
        raise ProfileError("stable_check_name must be exact literal 'contract'")
    if any(token in profile["stable_check_name"] for token in ("*", "${{", "<", ">")):
        raise ProfileError("stable_check_name may not be dynamic")

    contract_ref = relative(profile["verification_contract"], "verification_contract")
    if contract_ref != ".github-delivery/ci-publication/local-verification.contract.json":
        raise ProfileError("verification contract path drifted")
    if not contract_path.is_file():
        raise ProfileError("verification contract is absent")
    validate_contract(root, contract_path)

    runtime_root = relative(profile["runtime_root"], "runtime_root")
    if runtime_root != ".github-delivery/ci-publication/runtime":
        raise ProfileError("runtime_root drifted")
    if not ignore_path.is_file() or "runtime/" not in ignore_path.read_text(encoding="utf-8").splitlines():
        raise ProfileError("runtime output root is not ignored")

    entrypoints = profile["entrypoints"]
    if entrypoints != ENTRYPOINTS:
        raise ProfileError("entrypoint mapping drifted or bypasses the strict gate")
    for name, path_text in entrypoints.items():
        path = relative(path_text, f"entrypoints.{name}")
        if not (root / path).is_file():
            raise ProfileError(f"entrypoint is absent: {name}={path}")

    if profile["publication_intents"] != INTENTS:
        raise ProfileError(f"publication_intents must equal {INTENTS}")
    if profile["billing_circuit"] != {
        "open_state": "billing-open",
        "decision": "BLOCK",
        "probe_by_push": False,
        "recovery_owner": "ed3c",
    }:
        raise ProfileError("billing circuit must fail closed")
    if profile["evidence"] != {
        "local_receipt_schema": "github-delivery-local-verification/v1",
        "local_evidence_schema": "github-delivery-local-verification-evidence/v1",
        "github_snapshot_schema": "github-actions-publish-snapshot/v1",
        "sidecar_gate_binding": "IMPLEMENTED",
        "hosted_exact_head": "NOT_EXERCISED",
    }:
        raise ProfileError("evidence boundary drifted or overclaimed")

    for path in (profile_path, contract_path, ignore_path):
        scan(path)


def write_fixture(root: Path) -> tuple[Path, Path]:
    base = root / ".github-delivery" / "ci-publication"
    (base / "scripts").mkdir(parents=True)
    scripts = root / "skills" / "github-delivery-loop" / "scripts"
    scripts.mkdir(parents=True)
    for path in ENTRYPOINTS.values():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# fixture\n", encoding="utf-8")
    (base / ".gitignore").write_text("runtime/\n", encoding="utf-8")
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
        "entrypoints": dict(ENTRYPOINTS),
        "publication_intents": list(INTENTS),
        "billing_circuit": {"open_state": "billing-open", "decision": "BLOCK", "probe_by_push": False, "recovery_owner": "ed3c"},
        "evidence": {
            "local_receipt_schema": "github-delivery-local-verification/v1",
            "local_evidence_schema": "github-delivery-local-verification-evidence/v1",
            "github_snapshot_schema": "github-actions-publish-snapshot/v1",
            "sidecar_gate_binding": "IMPLEMENTED",
            "hosted_exact_head": "NOT_EXERCISED",
        },
    }
    profile_path = base / "profile.json"
    contract_path = base / "local-verification.contract.json"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    return profile_path, contract_path


def selftest() -> None:
    with tempfile.TemporaryDirectory(prefix="ci-publication-profile.") as temp:
        root = Path(temp)
        profile_path, contract_path = write_fixture(root)
        validate(root)
        original_profile = json.loads(profile_path.read_text())
        original_contract = json.loads(contract_path.read_text())

        profile_mutations = [
            lambda value: value["repository"].update(repository_id=1),
            lambda value: value.update(stable_check_name="${{ matrix.check }}"),
            lambda value: value["entrypoints"].update(publication_gate="skills/github-delivery-loop/scripts/ci_publish_gate.py"),
            lambda value: value["publication_intents"].append("checkpoint"),
            lambda value: value["billing_circuit"].update(probe_by_push=True),
            lambda value: value["evidence"].update(sidecar_gate_binding="NOT_IMPLEMENTED"),
            lambda value: value["evidence"].update(hosted_exact_head="PASS"),
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
    print("SELFTEST GREEN: admitted skills-shared publication profile (12 mutations killed)")


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
            print("PASS admitted skills-shared CI publication profile")
        return 0
    except ProfileError as exc:
        print(f"PROFILE RED: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"PROFILE FATAL: {exc}", file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
