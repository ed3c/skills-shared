#!/usr/bin/env python3
"""Validate the canonical repository portfolio prompt pack and Codex agent templates."""
from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

from repository_portfolio_common import digest_object, file_sha256, load_json, validate_schema

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = SKILL_ROOT / "references" / "repository-portfolio-control" / "prompt-manifest.json"
SCHEMA = SKILL_ROOT / "references" / "repository-portfolio-control" / "contracts" / "prompt-manifest.schema.json"
REQUIRED_PROMPT_IDS = {
    "repository-portfolio-controller-v3",
    "common-system-envelope-v1",
    "shadow-architect-monitor-v1",
    "tech-lead-controller-v1",
    "portfolio-explorer-v1",
    "acceptance-adversary-v1",
    "dependency-auditor-v1",
    "runtime-admission-auditor-v1",
    "implementation-worker-v1",
    "consolidation-verifier-v1",
    "release-auditor-v1",
    "skills-shared-overlay-v1",
}
REQUIRED_AGENT_NAMES = {
    "portfolio-explorer",
    "acceptance-adversary",
    "dependency-auditor",
    "runtime-admission-auditor",
    "implementation-worker",
    "consolidation-verifier",
    "release-auditor",
}
COORDINATOR = "Use subagents. Wait for all agents and consolidate their findings."


def validate(manifest: dict[str, Any]) -> list[str]:
    errors = validate_schema(manifest, SCHEMA)
    prompt_ids: set[str] = set()
    for index, entry in enumerate(manifest.get("prompts", [])):
        prompt_id = str(entry.get("id", ""))
        if prompt_id in prompt_ids:
            errors.append(f"duplicate prompt id: {prompt_id}")
        prompt_ids.add(prompt_id)
        path = SKILL_ROOT / str(entry.get("path", ""))
        if not path.is_file():
            errors.append(f"prompt missing: {entry.get('path')}")
            continue
        if file_sha256(path) != entry.get("sha256"):
            errors.append(f"prompt digest drift: {prompt_id}")
        text = path.read_text(encoding="utf-8")
        if entry.get("must_contain_coordinator_instruction") and COORDINATOR not in text:
            errors.append(f"coordinator instruction absent: {prompt_id}")
        if "/Users/neon/" in text and prompt_id != "skills-shared-overlay-v1":
            errors.append(f"machine-local path leaked into portable prompt: {prompt_id}")
        inherits_common = "Read and obey `common-system-envelope.md`" in text
        if (
            "private chain of thought" not in text.lower()
            and prompt_id != "repository-portfolio-controller-v3"
            and not inherits_common
        ):
            errors.append(f"private-reasoning boundary absent: {prompt_id}")
    missing_prompts = REQUIRED_PROMPT_IDS - prompt_ids
    if missing_prompts:
        errors.append(f"required prompts absent: {sorted(missing_prompts)}")

    agent_names: set[str] = set()
    for entry in manifest.get("codex_agents", []):
        name = str(entry.get("name", ""))
        if name in agent_names:
            errors.append(f"duplicate Codex agent: {name}")
        agent_names.add(name)
        path = SKILL_ROOT / str(entry.get("path", ""))
        if not path.is_file():
            errors.append(f"Codex agent template missing: {entry.get('path')}")
            continue
        if file_sha256(path) != entry.get("sha256"):
            errors.append(f"Codex agent digest drift: {name}")
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"Codex agent TOML invalid ({name}): {exc}")
            continue
        for field in ("name", "description", "developer_instructions"):
            if not data.get(field):
                errors.append(f"Codex agent {name} missing {field}")
        if data.get("name") != name:
            errors.append(f"Codex agent name mismatch: {name}")
        if data.get("sandbox_mode") != entry.get("sandbox_mode"):
            errors.append(f"Codex agent sandbox mismatch: {name}")
        if name == "implementation-worker":
            if data.get("sandbox_mode") != "workspace-write":
                errors.append("implementation-worker must be workspace-write")
        elif data.get("sandbox_mode") != "read-only":
            errors.append(f"read-only agent widened sandbox: {name}")
    missing_agents = REQUIRED_AGENT_NAMES - agent_names
    if missing_agents:
        errors.append(f"required Codex agents absent: {sorted(missing_agents)}")

    if manifest.get("required_coordinator_instruction") != COORDINATOR:
        errors.append("coordinator instruction drifted")
    if digest_object(manifest, "manifest_digest") != manifest.get("manifest_digest"):
        errors.append("manifest digest drifted")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    try:
        manifest = load_json(args.manifest)
    except Exception as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 64
    errors = validate(manifest)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 2
    print(f"PASS: prompt pack ({len(manifest['prompts'])} prompts, {len(manifest['codex_agents'])} Codex agents)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
