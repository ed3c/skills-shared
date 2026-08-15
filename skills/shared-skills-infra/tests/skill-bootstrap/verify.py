#!/usr/bin/env python3
"""Controls for the Skill resolution and environment bootstrap gate.

Positive fixtures cover the three shapes that must be admitted: a local host that
reaches execution, a connector that legitimately stops at reasoning, and a pinned
Actions bundle. Planted defects cover the claims a prompt cannot establish --
which bytes, through which surface, and whether the environment actually exists.
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
CHECKER = SKILL_ROOT / "scripts" / "check_skill_bootstrap.py"
SCHEMA_ROOT = SKILL_ROOT / "references"
GOOD = TEST_DIR / "fixtures" / "valid-local.json"

SEQUENCE_BEFORE_ENVIRONMENT = [
    "RUNTIME_BOUND",
    "REPOSITORY_POLICY_BOUND",
    "SKILL_REQUIREMENTS_DISCOVERED",
    "MINIMAL_SKILL_SET_RESOLVED",
    "CANONICAL_SKILL_SUBJECTS_BOUND",
    "SKILL_SURFACES_AVAILABLE",
]


def run(document: dict) -> tuple[int, str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "receipt.json"
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        process = subprocess.run(
            [sys.executable, str(CHECKER), str(path), "--schema-root", str(SCHEMA_ROOT)],
            text=True,
            capture_output=True,
            check=False,
        )
        return process.returncode, process.stdout, process.stderr


def mutate(name: str, document: dict) -> None:
    skills = document["selected_skills"]
    if name == "skipped-state":
        document["bootstrap_states"].remove("SKILL_SURFACES_AVAILABLE")
    elif name == "reordered-state":
        states = document["bootstrap_states"]
        states[2], states[3] = states[3], states[2]
    elif name == "admitted-while-blocked":
        document["bootstrap_states"].insert(-1, "SKILL_SHADOWED")
    elif name == "blocked-not-terminal":
        document["bootstrap_states"] = SEQUENCE_BEFORE_ENVIRONMENT + [
            "SKILL_SURFACE_ABSENT",
            "SKILL_RUNTIME_REQUIREMENTS_BOUND",
        ]
    elif name == "connector-claims-local-surface":
        document["runtime_identity"] = "CHATGPT_GITHUB_CONNECTOR"
    elif name == "connector-claims-execution":
        document["runtime_identity"] = "CHATGPT_GITHUB_CONNECTOR"
        for skill in skills:
            skill["access_mode"] = "CONNECTOR_EXACT_COMMIT_READ_ONLY"
            skill["surface_readback_state"] = "NOT_EXERCISED"
    elif name == "unknown-runtime-admitted":
        document["runtime_identity"] = "UNKNOWN"
        for skill in skills:
            skill["access_mode"] = "ABSENT"
            skill["surface_readback_state"] = "ABSENT"
    elif name == "surface-readback-missing":
        skills[0]["surface_readback_state"] = "NOT_EXERCISED"
    elif name == "absent-skill-admitted":
        skills[0]["access_mode"] = "ABSENT"
        skills[0]["surface_readback_state"] = "ABSENT"
    elif name == "open-dependency-closure":
        skills[0]["transitive_dependencies"] = ["shared-skills-infra", "runtime-env"]
    elif name == "orphan-dependency-selection":
        skills[0]["transitive_dependencies"] = []
    elif name == "registry-wide-selection":
        skills[0]["selection_reason"] = "REGISTRY_WIDE"
    elif name == "shadowed-admission":
        document["shadowing_scan"]["state"] = "SHADOWED"
        document["shadowing_scan"]["findings"] = [
            {"name": "dual-forge-repository-loop", "surface": ".claude/skills"}
        ]
    elif name == "unscanned-admission":
        document["shadowing_scan"]["state"] = "NOT_EXERCISED"
    elif name == "shadowing-scan-contradiction":
        document["shadowing_scan"]["findings"] = [
            {"name": "dual-forge-repository-loop", "surface": ".claude/skills"}
        ]
    elif name == "public-consumer-private-import":
        # A project-level projection puts the private canonical body inside the
        # public consumer. A preinstalled user surface would be legitimate here,
        # which is why the positive control below keeps that lane open.
        document["consumer"]["visibility"] = "PUBLIC"
        skills[0]["access_mode"] = "PROJECT_CANONICAL_PROJECTION"
    elif name == "mutable-canonical-ref":
        document["canonical"]["commit_sha"] = "main"
    elif name == "secret-value-leaked":
        document["environment"]["secret_values"] = {"FORGEJO_TOKEN": "hunter2"}
    elif name == "shell-as-entrypoint":
        document["environment"]["setup_entrypoints"] = ["bash -c 'pip install -r req.txt'"]
    elif name == "admitted-with-absent-secret":
        document["environment"]["absent_secret_names"] = ["FORGEJO_TOKEN"]
    elif name == "absent-secret-not-required":
        document["environment"]["absent_secret_names"] = ["UNDECLARED_TOKEN"]
        document["environment"]["required_secret_names"] = ["FORGEJO_TOKEN"]
    elif name == "probe-not-pass":
        document["environment"]["capability_probes"][1]["state"] = "FAIL"
    elif name == "prepared-without-probe":
        document["environment"]["capability_probes"] = []
    elif name == "admitted-without-environment":
        document["environment"]["state"] = "NOT_PREPARED"
    elif name == "runtime-requirements-absent":
        skills[1]["runtime_requirements_digest"] = "ABSENT"
    else:
        raise AssertionError(f"unknown mutation: {name}")


def main() -> int:
    good = json.loads(GOOD.read_text(encoding="utf-8"))
    failures: list[str] = []

    code, stdout, stderr = run(good)
    if code != 0 or "SKILL-BOOTSTRAP-GREEN" not in stdout or stderr:
        failures.append(f"positive local fixture: code={code} stdout={stdout!r} stderr={stderr!r}")

    # A connector may resolve exact Skill bytes for reasoning. Stopping before the
    # environment lanes is the correct outcome, not a failure -- the receipt must
    # be admitted precisely because it claims nothing it cannot observe.
    connector = copy.deepcopy(good)
    connector["runtime_identity"] = "CHATGPT_GITHUB_CONNECTOR"
    for skill in connector["selected_skills"]:
        skill["access_mode"] = "CONNECTOR_EXACT_COMMIT_READ_ONLY"
        skill["surface_readback_state"] = "NOT_EXERCISED"
    connector["environment"] = {
        "state": "NOT_REQUIRED",
        "plan_digest": "ABSENT",
        "required_secret_names": [],
        "absent_secret_names": [],
        "setup_entrypoints": [],
        "capability_probes": [],
    }
    connector["bootstrap_states"] = SEQUENCE_BEFORE_ENVIRONMENT
    code, stdout, stderr = run(connector)
    if code != 0 or stderr:
        failures.append(f"positive connector fixture: code={code} stderr={stderr!r}")

    # A runner consumes a pinned bundle and may reach execution.
    actions = copy.deepcopy(good)
    actions["runtime_identity"] = "GITHUB_ACTIONS"
    for skill in actions["selected_skills"]:
        skill["access_mode"] = "GITHUB_ACTIONS_PINNED_BUNDLE"
        skill["surface_readback_state"] = "VERIFIED"
    code, stdout, stderr = run(actions)
    if code != 0 or stderr:
        failures.append(f"positive actions fixture: code={code} stderr={stderr!r}")

    # A public consumer reaching a private canonical through a preinstalled local
    # user surface is admitted; what is refused is importing the private body into
    # the public repository, which the planted control below covers.
    public_local = copy.deepcopy(good)
    public_local["consumer"]["visibility"] = "PUBLIC"
    code, stdout, stderr = run(public_local)
    if code != 0 or stderr:
        failures.append(f"positive public-consumer-local-surface fixture: code={code} stderr={stderr!r}")

    # A blocked lane is a terminal, admitted-as-honest receipt: it records why
    # execution was refused rather than claiming a success it did not have.
    blocked = copy.deepcopy(good)
    blocked["shadowing_scan"]["state"] = "SHADOWED"
    blocked["shadowing_scan"]["findings"] = [
        {"name": "dual-forge-repository-loop", "surface": ".claude/skills"}
    ]
    blocked["environment"] = {
        "state": "NOT_PREPARED",
        "plan_digest": "ABSENT",
        "required_secret_names": [],
        "absent_secret_names": [],
        "setup_entrypoints": [],
        "capability_probes": [],
    }
    blocked["bootstrap_states"] = SEQUENCE_BEFORE_ENVIRONMENT + ["SKILL_SHADOWED"]
    code, stdout, stderr = run(blocked)
    if code != 0 or stderr:
        failures.append(f"positive blocked-lane fixture: code={code} stderr={stderr!r}")

    cases = [
        ("skipped-state", 2, "bootstrap-sequence-violation"),
        ("reordered-state", 2, "bootstrap-sequence-violation"),
        ("admitted-while-blocked", 2, "admitted-while-blocked"),
        ("blocked-not-terminal", 2, "blocked-state-not-terminal"),
        ("connector-claims-local-surface", 2, "access-mode-not-observable"),
        ("connector-claims-execution", 2, "execution-claim-on-reasoning-only-access"),
        ("unknown-runtime-admitted", 2, "unknown-runtime-admitted"),
        ("surface-readback-missing", 2, "surface-readback-missing"),
        ("absent-skill-admitted", 2, "absent-skill-admitted"),
        ("open-dependency-closure", 2, "dependency-closure-open"),
        ("orphan-dependency-selection", 2, "orphan-dependency-selection"),
        ("registry-wide-selection", 64, "schema-invalid"),
        ("shadowed-admission", 2, "shadowed-or-unscanned-admission"),
        ("unscanned-admission", 2, "shadowed-or-unscanned-admission"),
        ("shadowing-scan-contradiction", 2, "shadowing-scan-contradiction"),
        ("public-consumer-private-import", 2, "public-consumer-private-import"),
        ("mutable-canonical-ref", 64, "schema-invalid"),
        ("secret-value-leaked", 64, "schema-invalid"),
        ("shell-as-entrypoint", 64, "schema-invalid"),
        ("admitted-with-absent-secret", 2, "admitted-with-absent-secrets"),
        ("absent-secret-not-required", 2, "absent-secret-not-required"),
        ("probe-not-pass", 2, "capability-probe-not-pass"),
        ("prepared-without-probe", 2, "prepared-without-probe"),
        ("admitted-without-environment", 2, "admitted-without-prepared-environment"),
        ("runtime-requirements-absent", 2, "runtime-requirements-absent"),
    ]

    for name, expected_code, marker in cases:
        document = copy.deepcopy(good)
        mutate(name, document)
        code, stdout, stderr = run(document)
        if code != expected_code or marker not in stderr:
            failures.append(
                f"{name}: expected code={expected_code} marker={marker!r}; "
                f"got code={code} stdout={stdout!r} stderr={stderr!r}"
            )

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
        "PASS skill-bootstrap: local execution, connector reasoning-only, pinned Actions "
        f"bundle, and blocked-lane fixtures admitted; {len(cases)} planted sequence, "
        "access-mode, closure, shadowing, visibility, secret-boundary, and capability "
        "defects refused; absent input stayed distinct"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
