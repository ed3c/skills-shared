"""Shared constants, input handling, and exact identity helpers."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

STATES = (
    "HYPOTHESIS",
    "CANDIDATE",
    "PROPOSED",
    "VERIFIED",
    "ADMITTED",
    "CANONICAL",
    "SUPERSEDED",
    "REVOKED",
)
ACTIVE_STATES = STATES[:6]
NON_DURABLE_STATES = ("HYPOTHESIS", "CANDIDATE", "PROPOSED", "VERIFIED")
TERMINAL_STATES = ("SUPERSEDED", "REVOKED")

EXPECTED_TRANSITIONS: dict[tuple[str, str], frozenset[str]] = {
    ("HYPOTHESIS", "CANDIDATE"): frozenset({"LOCAL_EVALUATOR_RECEIPT"}),
    ("CANDIDATE", "PROPOSED"): frozenset(
        {"LOCAL_EVALUATOR_RECEIPT", "EXACT_PR_SUBJECT"}
    ),
    ("PROPOSED", "VERIFIED"): frozenset(
        {
            "LOCAL_EVALUATOR_RECEIPT",
            "EXACT_PR_SUBJECT",
            "OWNING_EXACT_HEAD_RECEIPT",
        }
    ),
    ("VERIFIED", "ADMITTED"): frozenset(
        {
            "LOCAL_EVALUATOR_RECEIPT",
            "EXACT_PR_SUBJECT",
            "OWNING_EXACT_HEAD_RECEIPT",
            "ADMITTED_SUBJECT",
        }
    ),
    ("ADMITTED", "CANONICAL"): frozenset(
        {
            "LOCAL_EVALUATOR_RECEIPT",
            "OWNING_EXACT_HEAD_RECEIPT",
            "ADMITTED_SUBJECT",
            "HUMAN_APPROVAL",
        }
    ),
    ("ADMITTED", "SUPERSEDED"): frozenset(
        {"ADMITTED_SUBJECT", "SUPERSESSION_TARGET"}
    ),
    ("CANONICAL", "SUPERSEDED"): frozenset(
        {"ADMITTED_SUBJECT", "SUPERSESSION_TARGET"}
    ),
    ("ADMITTED", "REVOKED"): frozenset(
        {"ADMITTED_SUBJECT", "HUMAN_APPROVAL", "REVOCATION_REASON"}
    ),
    ("CANONICAL", "REVOKED"): frozenset(
        {"ADMITTED_SUBJECT", "HUMAN_APPROVAL", "REVOCATION_REASON"}
    ),
}

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
GIT_SHA1 = re.compile(r"^git-sha1:[0-9a-f]{40}$")
SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
REPOSITORY = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")
PRIVATE_REASONING_KEYS = {
    "chain_of_thought",
    "reasoning_trace",
    "hidden_reasoning",
    "private_reasoning",
}


class PolicyRefusal(Exception):
    """The input is readable but violates the promotion policy."""


class InputFailure(Exception):
    """The caller did not supply a readable, parseable input."""


class CliUsage(Exception):
    """The command line is incomplete or invalid."""


class StableArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # pragma: no cover - exercised by CLI
        raise CliUsage(message)


def load_object(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise InputFailure(f"unreadable input {path}: {error}") from error
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise InputFailure(f"unparseable JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise InputFailure(f"{path}: top level must be a JSON object")
    return value, raw


def canonical_sha256(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PolicyRefusal(f"{label} must be an object")
    return value


def require_array(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise PolicyRefusal(f"{label} must be an array")
    return value


def require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PolicyRefusal(f"{label} must be a non-empty string")
    return value


def require_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise PolicyRefusal(f"{label} must be boolean")
    return value


def require_sha40(value: Any, label: str) -> str:
    text = require_text(value, label)
    if not SHA40.fullmatch(text):
        raise PolicyRefusal(f"{label} must be a 40-character lowercase Git SHA")
    return text


def require_digest(value: Any, label: str) -> str:
    text = require_text(value, label)
    if not (SHA256.fullmatch(text) or GIT_SHA1.fullmatch(text)):
        raise PolicyRefusal(f"{label} must be sha256:<64hex> or git-sha1:<40hex>")
    return text


def require_sha256(value: Any, label: str) -> str:
    text = require_text(value, label)
    if not SHA256.fullmatch(text):
        raise PolicyRefusal(f"{label} must be sha256:<64hex>")
    return text


def reject_unknown_keys(
    value: dict[str, Any], allowed: set[str], label: str
) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise PolicyRefusal(f"{label} has unknown fields: {', '.join(unknown)}")


def reject_private_reasoning(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in PRIVATE_REASONING_KEYS:
                raise PolicyRefusal(
                    f"{path}.{key}: private reasoning persistence is forbidden"
                )
            reject_private_reasoning(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_private_reasoning(child, f"{path}[{index}]")


def rank(state: str) -> int:
    try:
        return ACTIVE_STATES.index(state)
    except ValueError:
        return -1


def verify_file_digest(
    repository_root: Path,
    path: str,
    expected_digest: str,
    label: str,
) -> None:
    relative = Path(path)
    if relative.is_absolute() or ".." in relative.parts:
        raise PolicyRefusal(f"{label}.path must be a repository-relative path")
    subject = repository_root / relative
    try:
        raw = subject.read_bytes()
    except OSError as error:
        raise PolicyRefusal(f"{label} implementation is unreadable: {subject}: {error}") from error
    if expected_digest.startswith("sha256:"):
        observed = canonical_sha256(raw)
    else:
        observed = "git-sha1:" + git_blob_sha(raw)
    if observed != expected_digest:
        raise PolicyRefusal(
            f"{label} implementation digest is stale: expected {expected_digest}, "
            f"observed {observed}"
        )


