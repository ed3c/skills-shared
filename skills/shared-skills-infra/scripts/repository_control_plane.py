#!/usr/bin/env python3
"""Deterministic repository control-plane profile/attachment CLI.

This tool is zero-network. It composes already-canonical Skills and delegates
consumer binding rendering to shared_skills.py. It never installs host tools,
changes repository visibility, resolves semantic conflicts, or merges.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
REPO = SKILL_ROOT.parent.parent
DEFAULT_PROFILE = SKILL_ROOT / "references" / "repository-control-plane-profile.default.json"
REGISTRY = REPO / "registry.json"
SHARED_SKILLS = HERE / "shared_skills.py"
REQUIRED_ORDER = [
    "shared-skills-infra",
    "procedural-shadow-runtime",
    "agentic-tech-lead-orchestration",
    "spatial-loop-systems-engineering",
    "git-town-stacked-pr-worker",
    "dual-forge-repository-loop",
]
PHASES = [
    ("BOOTSTRAP", "skill-resolution", "REQUIRED"),
    ("SHADOW_ADMISSION", "shadow-admission", "REQUIRED"),
    ("TECH_LEAD_PLAN", "task-dag", "REQUIRED"),
    ("SPATIAL_INVARIANTS", "spatial-invariants", "MONITOR"),
    ("STACK_DELIVERY", "git-town-stack", "NOT_APPLICABLE_WITH_EVIDENCE"),
    ("FORGE_RECONCILIATION", "dual-forge-reconciliation", "NOT_APPLICABLE_WITH_EVIDENCE"),
]
PHASE_NAMES = {phase for phase, _, _ in PHASES}


class ControlPlaneError(ValueError):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ControlPlaneError(f"unreadable JSON {path}: {exc}") from exc


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def validate_profile(profile: dict[str, Any]) -> None:
    if not isinstance(profile, dict):
        raise ControlPlaneError("profile root must be an object")
    if profile.get("schema") != "repository-control-plane-profile/v1":
        raise ControlPlaneError("unsupported profile schema")
    if profile.get("skills") != REQUIRED_ORDER:
        raise ControlPlaneError("profile Skill closure/order drifted")
    caps = profile.get("runtime_capabilities")
    if not isinstance(caps, dict):
        raise ControlPlaneError("runtime_capabilities missing")
    git_town = caps.get("git_town", {})
    forgejo = caps.get("forgejo", {})
    if git_town.get("scope") != "user":
        raise ControlPlaneError("Git Town must remain user-scoped")
    if git_town.get("installer_state") != "NOT_IMPLEMENTED":
        raise ControlPlaneError(
            "Git Town installer must remain NOT_IMPLEMENTED until runtime-env owns a pinned receipt-producing installer"
        )
    if forgejo.get("scope") != "host":
        raise ControlPlaneError("Forgejo must remain host-scoped")
    if forgejo.get("service_state") not in {"NOT_EXERCISED", "ABSENT", "PASS"}:
        raise ControlPlaneError("invalid Forgejo service state")
    authority = profile.get("authority")
    required_false = {
        "automatic_merge",
        "automatic_conflict_resolution",
        "visibility_change",
        "credential_values",
    }
    if not isinstance(authority, dict) or set(authority) != required_false:
        raise ControlPlaneError("authority object drifted")
    if any(authority[key] is not False for key in required_false):
        raise ControlPlaneError("control-plane profile attempted authority widening")

    registry = load_json(REGISTRY)
    admitted = {row["name"] for row in registry.get("shared", [])}
    missing = [name for name in REQUIRED_ORDER if name not in admitted]
    if missing:
        raise ControlPlaneError(f"profile references unregistered shared Skills: {', '.join(missing)}")
    for name in REQUIRED_ORDER:
        if not (REPO / "skills" / name / "SKILL.md").is_file():
            raise ControlPlaneError(f"canonical Skill body missing: {name}")


def requirements_for(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "shared-skills/consumer-requirements/v1",
        "binding": "repository-control-plane",
        "shared": list(profile["skills"]),
        "repo_owned": [],
        "surfaces": {"claude": ".claude/skills", "codex": ".agents/skills"},
    }


def binding_paths(consumer: Path) -> tuple[Path, Path]:
    base = consumer / ".agents" / "control-plane"
    return base / "profile.json", base / "requirements.json"


def reject_local_bodies(consumer: Path, profile: dict[str, Any]) -> None:
    for surface in (consumer / ".agents" / "skills", consumer / ".claude" / "skills"):
        for name in profile["skills"]:
            candidate = surface / name
            if not candidate.exists() or candidate.is_symlink():
                continue
            if candidate.is_dir():
                files = [p for p in candidate.rglob("*") if p.is_file()]
                # A one-file forwarder is thin; any additional canonical-looking body is shadowing.
                if len(files) == 1 and files[0].name == "SKILL.md":
                    continue
                raise ControlPlaneError(f"project-local Skill body shadows canonical {name}: {candidate}")


def run_shared_sync(requirements: Path, consumer: Path, *, check: bool) -> None:
    args = [
        sys.executable,
        str(SHARED_SKILLS),
        "sync",
        "--requirements",
        str(requirements),
        "--target-root",
        str(consumer),
        "--check" if check else "--apply",
    ]
    result = subprocess.run(args, text=True, capture_output=True, check=False)
    if result.stdout:
        print(result.stdout, end="")
    if result.returncode:
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        raise ControlPlaneError(f"shared_skills.py sync exited {result.returncode}")


def attach(profile_path: Path, consumer: Path, *, check: bool) -> None:
    profile = load_json(profile_path)
    validate_profile(profile)
    consumer = consumer.resolve()
    reject_local_bodies(consumer, profile)
    profile_dest, requirements_dest = binding_paths(consumer)
    requirements = requirements_for(profile)
    expected_profile = {
        "schema": "repository-control-plane-binding/v1",
        "profile": profile["profile"],
        "profile_sha256": digest(profile),
        "skills": profile["skills"],
        "runtime_capabilities": profile["runtime_capabilities"],
        "authority": profile["authority"],
    }
    expected_profile_text = json.dumps(expected_profile, indent=2, sort_keys=True) + "\n"
    expected_requirements_text = json.dumps(requirements, indent=2, sort_keys=True) + "\n"
    if check:
        if not profile_dest.is_file() or profile_dest.read_text(encoding="utf-8") != expected_profile_text:
            raise ControlPlaneError("control-plane profile binding missing or drifted")
        if not requirements_dest.is_file() or requirements_dest.read_text(encoding="utf-8") != expected_requirements_text:
            raise ControlPlaneError("control-plane requirements missing or drifted")
        run_shared_sync(requirements_dest, consumer, check=True)
        print("CONTROL-PLANE-GREEN attachment verified")
        return
    profile_dest.parent.mkdir(parents=True, exist_ok=True)
    profile_dest.write_text(expected_profile_text, encoding="utf-8")
    requirements_dest.write_text(expected_requirements_text, encoding="utf-8")
    run_shared_sync(requirements_dest, consumer, check=False)
    print("CONTROL-PLANE-ATTACHED thin binding rendered")


def _required_phases(item: dict[str, Any], identity: str) -> set[str]:
    raw = item.get("required_phases", [])
    if not isinstance(raw, list) or any(not isinstance(phase, str) for phase in raw):
        raise ControlPlaneError(f"invalid required_phases for {identity}")
    requested = set(raw)
    unknown = sorted(requested - PHASE_NAMES)
    if unknown:
        raise ControlPlaneError(
            f"unknown required_phases for {identity}: {', '.join(unknown)}"
        )
    return requested


def _phase_plan(required: set[str]) -> tuple[list[dict[str, str]], list[str]]:
    dispositions: list[dict[str, str]] = []
    required_receipts: list[str] = []
    for phase, receipt, default in PHASES:
        disposition = "REQUIRED" if phase in required else default
        dispositions.append(
            {
                "phase": phase,
                "receipt": receipt,
                "disposition": disposition,
            }
        )
        if disposition == "REQUIRED":
            required_receipts.append(receipt)
    return dispositions, required_receipts


def monitor_plan(issue_packet: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(issue_packet, list):
        raise ControlPlaneError("issue packet must be an array")
    by_id: dict[str, dict[str, Any]] = {}
    for item in issue_packet:
        if not isinstance(item, dict):
            raise ControlPlaneError("issue item must be an object")
        repository = item.get("repository")
        number = item.get("number")
        if not isinstance(repository, str) or not isinstance(number, int) or number <= 0:
            raise ControlPlaneError("issue identity requires repository and positive number")
        identity = f"{repository}#{number}"
        if identity in by_id:
            raise ControlPlaneError(f"duplicate issue identity: {identity}")
        deps = item.get("depends_on", [])
        if not isinstance(deps, list) or any(not isinstance(dep, str) for dep in deps):
            raise ControlPlaneError(f"invalid depends_on for {identity}")
        required = _required_phases(item, identity)
        by_id[identity] = {**item, "_required_phases": required}

    # Dependency closure is part of the exact input subject. This planner is
    # intentionally zero-network, so an absent dependency cannot be inferred as
    # closed from provider state. Without this check, "absent" and "included +
    # closed" collapse to the same scheduling result and a blocker can vanish
    # from the packet without turning the plan red.
    for identity, item in by_id.items():
        for dep in item.get("depends_on", []):
            if dep == identity:
                raise ControlPlaneError(f"self dependency: {identity} -> {dep}")
            if dep not in by_id:
                raise ControlPlaneError(f"missing dependency closure: {identity} -> {dep}")

    open_ids = {
        identity
        for identity, item in by_id.items()
        if item.get("state", "open") == "open"
    }
    unresolved = set(open_ids)
    waves: list[list[str]] = []
    while unresolved:
        ready = sorted(
            identity for identity in unresolved
            if all(dep not in unresolved for dep in by_id[identity].get("depends_on", []))
        )
        if not ready:
            raise ControlPlaneError("unfinished-issue dependency cycle")
        waves.append(ready)
        unresolved.difference_update(ready)

    issue_plans: dict[str, dict[str, Any]] = {}
    for identity in sorted(open_ids):
        dispositions, required_receipts = _phase_plan(by_id[identity]["_required_phases"])
        issue_plans[identity] = {
            "phase_dispositions": dispositions,
            "required_receipts": required_receipts,
            "execution_state": "NOT_EXERCISED",
        }

    return {
        "schema": "repository-control-plane-monitor-plan/v1",
        "issues": sorted(open_ids),
        "waves": waves,
        "issue_plans": issue_plans,
        "automatic_merge": False,
        "automatic_conflict_resolution": False,
    }


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    commands = p.add_subparsers(dest="command", required=True)
    pc = commands.add_parser("profile-check")
    pc.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    at = commands.add_parser("attach")
    at.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    at.add_argument("--consumer", required=True, type=Path)
    vr = commands.add_parser("verify")
    vr.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    vr.add_argument("--consumer", required=True, type=Path)
    mp = commands.add_parser("monitor-plan")
    mp.add_argument("--issues", required=True, type=Path)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "profile-check":
            profile = load_json(args.profile)
            validate_profile(profile)
            print(f"CONTROL-PLANE-GREEN profile={profile['profile']} sha256={digest(profile)}")
        elif args.command == "attach":
            attach(args.profile, args.consumer, check=False)
        elif args.command == "verify":
            attach(args.profile, args.consumer, check=True)
        else:
            packet = load_json(args.issues)
            print(json.dumps(monitor_plan(packet), indent=2, sort_keys=True))
        return 0
    except ControlPlaneError as exc:
        print(f"CONTROL-PLANE-RED {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
