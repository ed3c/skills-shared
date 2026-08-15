#!/usr/bin/env python3
"""Controls for the two halves of the bootstrap contract.

A Skill's runtime requirements are abstract and secret-free; a consumer binding
resolves them onto an exact commit and host surfaces. Both are refused when they
declare something they cannot support, and both are refused at schema level for
the shapes that would make them unportable or leaky.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
SKILL_ROOT = TEST_DIR.parent.parent
CHECKER = SKILL_ROOT / "scripts" / "check_skill_requirements.py"
SCHEMA_ROOT = SKILL_ROOT / "references"
REQUIREMENTS = TEST_DIR / "fixtures" / "valid-requirements.json"
BINDING = TEST_DIR / "fixtures" / "valid-binding.json"


def run(document: dict) -> tuple[int, str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "document.json"
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        process = subprocess.run(
            [sys.executable, str(CHECKER), str(path), "--schema-root", str(SCHEMA_ROOT)],
            text=True,
            capture_output=True,
            check=False,
        )
        return process.returncode, process.stdout, process.stderr


def mutate_requirements(name: str, document: dict) -> None:
    if name == "allowlist-empty":
        document["network_policy"]["allowed_hosts"] = []
    elif name == "allowlist-ignored":
        document["network_policy"]["mode"] = "NONE"
    elif name == "unrestricted-without-boundary":
        document["network_policy"]["mode"] = "UNRESTRICTED"
        document["network_policy"]["allowed_hosts"] = []
        document["not_exercised_without_substrate"] = []
        document["secret_variable_names"] = []
    elif name == "capability-both-ways":
        document["optional_capabilities"].append("local-checkout")
    elif name == "writable-without-worktree":
        document["filesystem"]["needs_writable_worktree"] = False
    elif name == "read-only-sandbox-writes":
        document["isolation"]["sandbox"] = "READ_ONLY"
    elif name == "secrets-without-boundary":
        document["not_exercised_without_substrate"] = []
    elif name == "absolute-writable-path":
        document["filesystem"]["writable_subpaths"] = ["/etc/skills"]
    elif name == "escaping-writable-path":
        document["filesystem"]["writable_subpaths"] = ["../outside"]
    elif name == "executable-as-path":
        document["executables"][0]["name"] = "/usr/bin/git"
    elif name == "secret-value-field":
        document["secret_values"] = {"FORGEJO_TOKEN": "hunter2"}
    elif name == "shell-as-setup":
        document["setup_entrypoints"] = ["bash -c 'pip install -r req.txt'"]
    elif name == "runtime-env-pins-a-commit":
        document["runtime_env"]["commit_sha"] = "d" * 40
    else:
        raise AssertionError(f"unknown requirements mutation: {name}")


def mutate_binding(name: str, document: dict) -> None:
    if name == "connector-given-local-mode":
        document["allowed_access_modes"]["CHATGPT_GITHUB_CONNECTOR"] = [
            "LOCAL_CANONICAL_USER_SURFACE"
        ]
    elif name == "actions-given-user-surface":
        document["allowed_access_modes"]["GITHUB_ACTIONS"] = ["LOCAL_CANONICAL_USER_SURFACE"]
    elif name == "runtime-env-collapsed":
        document["runtime_env"]["repository_id"] = document["canonical"]["repository_id"]
    elif name == "duplicate-skill":
        document["selected_skills"].append(copy.deepcopy(document["selected_skills"][0]))
    elif name == "mutable-canonical-ref":
        document["canonical"]["commit_sha"] = "main"
    elif name == "local-canonical-url":
        document["canonical"]["url"] = "file:///Users/someone/skills-shared"
    elif name == "absolute-surface":
        document["routing"]["surfaces"]["claude"] = "/Users/someone/.claude/skills"
    elif name == "escaping-surface":
        document["routing"]["surfaces"]["claude"] = "../../.claude/skills"
    elif name == "empty-access-modes":
        document["allowed_access_modes"]["CLAUDE_CODE_LOCAL"] = []
    elif name == "token-field":
        document["canonical"]["token"] = "ghp_example"
    else:
        raise AssertionError(f"unknown binding mutation: {name}")


def main() -> int:
    requirements = json.loads(REQUIREMENTS.read_text(encoding="utf-8"))
    binding = json.loads(BINDING.read_text(encoding="utf-8"))
    failures: list[str] = []

    code, stdout, stderr = run(requirements)
    if code != 0 or "SKILL-REQUIREMENTS-GREEN" not in stdout or stderr:
        failures.append(f"positive requirements: code={code} stdout={stdout!r} stderr={stderr!r}")

    code, stdout, stderr = run(binding)
    if code != 0 or "CONSUMER-BINDING-GREEN" not in stdout or stderr:
        failures.append(f"positive binding: code={code} stdout={stdout!r} stderr={stderr!r}")

    # A Skill needing no secrets and no network may legitimately declare nothing
    # unproven -- the boundary requirement is conditional, not universal.
    minimal = copy.deepcopy(requirements)
    minimal["network_policy"] = {"mode": "NONE", "allowed_hosts": []}
    minimal["secret_variable_names"] = []
    minimal["not_exercised_without_substrate"] = []
    code, stdout, stderr = run(minimal)
    if code != 0 or stderr:
        failures.append(f"positive offline-requirements: code={code} stderr={stderr!r}")

    # A binding without runtime_env is valid: not every consumer resolves one.
    no_env = copy.deepcopy(binding)
    del no_env["runtime_env"]
    code, stdout, stderr = run(no_env)
    if code != 0 or stderr:
        failures.append(f"positive binding-without-runtime-env: code={code} stderr={stderr!r}")

    cases = [
        (mutate_requirements, requirements, "allowlist-empty", 2, "allowlist-empty"),
        (mutate_requirements, requirements, "allowlist-ignored", 2, "allowlist-ignored"),
        (mutate_requirements, requirements, "unrestricted-without-boundary", 2, "unrestricted-network-without-boundary"),
        (mutate_requirements, requirements, "capability-both-ways", 2, "capability-required-and-optional"),
        (mutate_requirements, requirements, "writable-without-worktree", 2, "writable-subpaths-without-writable-worktree"),
        (mutate_requirements, requirements, "read-only-sandbox-writes", 2, "read-only-sandbox-needs-writable-worktree"),
        (mutate_requirements, requirements, "secrets-without-boundary", 2, "secrets-without-boundary"),
        (mutate_requirements, requirements, "absolute-writable-path", 64, "schema-invalid"),
        (mutate_requirements, requirements, "escaping-writable-path", 64, "schema-invalid"),
        (mutate_requirements, requirements, "executable-as-path", 64, "schema-invalid"),
        (mutate_requirements, requirements, "secret-value-field", 64, "schema-invalid"),
        (mutate_requirements, requirements, "shell-as-setup", 64, "schema-invalid"),
        (mutate_requirements, requirements, "runtime-env-pins-a-commit", 64, "schema-invalid"),
        (mutate_binding, binding, "connector-given-local-mode", 2, "access-mode-not-observable"),
        (mutate_binding, binding, "actions-given-user-surface", 2, "access-mode-not-observable"),
        (mutate_binding, binding, "runtime-env-collapsed", 2, "runtime-env-collapsed-into-canonical"),
        (mutate_binding, binding, "duplicate-skill", 2, "duplicate-selected-skill"),
        (mutate_binding, binding, "mutable-canonical-ref", 64, "schema-invalid"),
        (mutate_binding, binding, "local-canonical-url", 64, "schema-invalid"),
        (mutate_binding, binding, "absolute-surface", 64, "schema-invalid"),
        (mutate_binding, binding, "escaping-surface", 64, "schema-invalid"),
        (mutate_binding, binding, "empty-access-modes", 64, "schema-invalid"),
        (mutate_binding, binding, "token-field", 64, "schema-invalid"),
    ]

    for mutator, base, name, expected_code, marker in cases:
        document = copy.deepcopy(base)
        mutator(name, document)
        code, stdout, stderr = run(document)
        if code != expected_code or marker not in stderr:
            failures.append(
                f"{name}: expected code={expected_code} marker={marker!r}; "
                f"got code={code} stdout={stdout!r} stderr={stderr!r}"
            )

    # A document that names no schema cannot be routed to a validator, and
    # guessing one would validate it against rules it never claimed.
    code, stdout, stderr = run({"skill_name": "nameless"})
    if code != 64 or "unidentified-document" not in stderr:
        failures.append(f"unidentified document: got code={code} stderr={stderr!r}")
    code, stdout, stderr = run({"schema": "some-other-thing/v9"})
    if code != 64 or "unknown-schema" not in stderr:
        failures.append(f"unknown schema: got code={code} stderr={stderr!r}")

    process = subprocess.run(
        [sys.executable, str(CHECKER), str(TEST_DIR / "fixtures" / "absent.json")],
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != 64 or "absent-input" not in process.stderr:
        failures.append(
            f"absent input: expected 64/absent-input, got {process.returncode} {process.stderr!r}"
        )

    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        return 1

    print(
        "PASS skill-requirements: abstract requirements, offline requirements, consumer "
        f"binding, and binding-without-runtime-env admitted; {len(cases)} planted network, "
        "capability, filesystem, secret-boundary, portability, and access-mode defects "
        "refused; unidentified, unknown-schema and absent inputs stayed distinct"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
