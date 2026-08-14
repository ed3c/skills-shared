#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

BEGIN = "<!-- BEGIN SKILLS-SHARED INSTRUCTION PROJECTION -->"
END = "<!-- END SKILLS-SHARED INSTRUCTION PROJECTION -->"
BINDING_REL = Path(".skill-bindings/instruction-projection.json")
GLOBAL_RECEIPT_NAME = ".skills-shared-projection-receipt.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_module(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    data = json.loads(raw)
    if data.get("schema_version") != "instruction-projection/v1":
        raise ValueError("unsupported instruction projection schema")
    return data, sha256_bytes(raw)


def git_commit(repo: Path) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    return out if SHA40.fullmatch(out) else None


def replace_block(text: str, block: str) -> str:
    start = text.find(BEGIN)
    end = text.find(END)
    if start == -1 and end == -1:
        if text and not text.endswith("\n"):
            text += "\n"
        return text + ("\n" if text else "") + block + "\n"
    if start == -1 or end == -1 or end < start:
        raise ValueError("managed block markers are malformed")
    tail = end + len(END)
    return text[:start] + block + text[tail:]


def render(module: dict, module_sha: str, canonical_commit: str, role: str) -> str:
    role_text = module["projection_roles"][role]
    runtime_lines = "\n".join(f"{i}. {x}" for i, x in enumerate(module["runtime_order"], 1))
    law_lines = "\n".join(f"- {x}" for x in module["hard_laws"])
    return f"""{BEGIN}
## Shared runtime / delivery projection

Canonical source: `ed3c/skills-shared@{canonical_commit}` → `skills/dual-forge-repository-loop/references/instruction-projection.json`
Canonical module SHA-256: `{module_sha}`
Projection role: `{role}` — {role_text}

Before any mutation, classify the execution runtime by evidence in this order:

{runtime_lines}

Mandatory laws:

{law_lines}

Do not edit this managed block manually. Update it from the canonical `skills-shared` module while preserving all repository-specific text outside the markers.
{END}"""


def ensure_file(path: Path, initial_header: str) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return initial_header.rstrip() + "\n"


def canonical_commit_arg(args, module_path: Path) -> str:
    if args.canonical_commit:
        if not SHA40.fullmatch(args.canonical_commit):
            raise ValueError("--canonical-commit must be a lowercase 40-hex SHA")
        return args.canonical_commit
    inferred = git_commit(module_path.parents[3])
    if inferred:
        return inferred
    raise ValueError("canonical commit is required when it cannot be inferred from a skills-shared checkout")


def binding_payload(commit: str, module_sha: str, agents: str, claude: str) -> dict:
    return {
        "schema_version": "instruction-projection-binding/v1",
        "canonical": {
            "repository": "ed3c/skills-shared",
            "commit": commit,
            "module": "skills/dual-forge-repository-loop/references/instruction-projection.json",
            "module_sha256": module_sha,
        },
        "repository_projection": {
            "AGENTS.md": {"sha256": sha256_bytes(agents.encode())},
            "CLAUDE.md": {"sha256": sha256_bytes(claude.encode())},
        },
        "global_claude": {
            "state": "NOT_EXERCISED",
            "receipt": "host-owned ~/.claude/.skills-shared-projection-receipt.json",
        },
    }


def sync_repo(args, module: dict, module_sha: str, commit: str) -> int:
    root = Path(args.repo_root).resolve()
    agents_path = root / "AGENTS.md"
    claude_path = root / "CLAUDE.md"
    agents_original = ensure_file(agents_path, "# Repository Agent Instructions")
    claude_original = ensure_file(claude_path, "# Claude repository adapter\n\nRead `AGENTS.md` before making repository changes.")
    agents_next = replace_block(agents_original, render(module, module_sha, commit, "AGENTS.md"))
    claude_next = replace_block(claude_original, render(module, module_sha, commit, "CLAUDE.md"))
    binding = binding_payload(commit, module_sha, agents_next, claude_next)
    binding_text = json.dumps(binding, indent=2, sort_keys=True) + "\n"
    binding_path = root / BINDING_REL

    if args.mode == "check":
        problems: list[str] = []
        if not agents_path.exists() or agents_path.read_text(encoding="utf-8") != agents_next:
            problems.append("AGENTS.md projection stale or absent")
        if not claude_path.exists() or claude_path.read_text(encoding="utf-8") != claude_next:
            problems.append("CLAUDE.md projection stale or absent")
        if not binding_path.exists() or binding_path.read_text(encoding="utf-8") != binding_text:
            problems.append("instruction projection binding stale or absent")
        if problems:
            for problem in problems:
                print(f"FAIL {problem}", file=sys.stderr)
            return 2
        print("PASS repository instruction projections current")
        return 0

    agents_path.write_text(agents_next, encoding="utf-8")
    claude_path.write_text(claude_next, encoding="utf-8")
    binding_path.parent.mkdir(parents=True, exist_ok=True)
    binding_path.write_text(binding_text, encoding="utf-8")
    print(f"WROTE {agents_path}")
    print(f"WROTE {claude_path}")
    print(f"WROTE {binding_path}")
    return 0


def sync_global(args, module: dict, module_sha: str, commit: str) -> int:
    path = Path(args.global_claude).expanduser().resolve()
    original = ensure_file(path, "# Global Claude host instructions")
    next_text = replace_block(original, render(module, module_sha, commit, "GLOBAL_CLAUDE.md"))
    receipt_path = path.parent / GLOBAL_RECEIPT_NAME
    receipt = {
        "schema_version": "instruction-projection-global-receipt/v1",
        "canonical_commit": commit,
        "module_sha256": module_sha,
        "global_claude_sha256": sha256_bytes(next_text.encode()),
        "runtime": os.environ.get("AGENT_RUNTIME", "UNKNOWN"),
        "host": os.environ.get("AGENT_HOST", "UNKNOWN"),
    }
    receipt_text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.mode == "check":
        problems = []
        if not path.exists() or path.read_text(encoding="utf-8") != next_text:
            problems.append("global CLAUDE.md projection stale or absent")
        if not receipt_path.exists() or receipt_path.read_text(encoding="utf-8") != receipt_text:
            problems.append("global projection receipt stale or absent")
        if problems:
            for problem in problems:
                print(f"FAIL {problem}", file=sys.stderr)
            return 2
        print("PASS global Claude projection current")
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(next_text, encoding="utf-8")
    receipt_path.write_text(receipt_text, encoding="utf-8")
    print(f"WROTE {path}")
    print(f"WROTE {receipt_path}")
    return 0


def parse_args(argv: list[str]):
    p = argparse.ArgumentParser()
    p.add_argument("--module", required=True)
    p.add_argument("--canonical-commit")
    p.add_argument("--mode", choices=("write", "check"), default="check")
    p.add_argument("--repo-root")
    p.add_argument("--global-claude", default="~/.claude/CLAUDE.md")
    p.add_argument("--include-global", action="store_true")
    args = p.parse_args(argv)
    if not args.repo_root and not args.include_global:
        p.error("provide --repo-root and/or --include-global")
    return args


def main(argv: list[str]) -> int:
    try:
        args = parse_args(argv)
        module_path = Path(args.module).resolve()
        module, module_sha = load_module(module_path)
        commit = canonical_commit_arg(args, module_path)
        rc = 0
        if args.repo_root:
            rc = max(rc, sync_repo(args, module, module_sha, commit))
        if args.include_global:
            rc = max(rc, sync_global(args, module, module_sha, commit))
        return rc
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR {exc}", file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
