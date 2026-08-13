#!/usr/bin/env python3
"""Compare the portable contract shape of current and candidate repo-agent-native Skills."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = "skills/repo-agent-native"
SKILL_PATH = f"{SKILL_ROOT}/SKILL.md"
PORTABLE_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
REQUIRED_SUPPORT = {
    f"{SKILL_ROOT}/README.md",
    f"{SKILL_ROOT}/agents/openai.yaml",
    f"{SKILL_ROOT}/modules/README.md",
    f"{SKILL_ROOT}/scripts/check_repo_agent_native.py",
    f"{SKILL_ROOT}/tests/verify.sh",
    f"{SKILL_ROOT}/evals.json",
    "evals/verifiers/verify_repo_agent_native_output.py",
}
REQUIRED_HEADINGS = {
    "## Trigger",
    "## Non-trigger",
    "## Inputs",
    "## Outputs",
    "## Core laws",
    "## State machine",
    "## S0 — Scope",
    "## S1 — Route",
    "## S2 — Discover",
    "## S3 — Retrieve",
    "## S4 — Verify",
    "## S5 — Infer",
    "## S6 — Write",
    "## S7 — Assert",
    "## S8 — Handoff",
    "## Module law",
}
FORBIDDEN = {
    "absolute-user-path": re.compile(r"(?:/Users|/home)/[^/\s`]+/"),
    "consumer-skill-bettor": re.compile(r"\bskill-bettor\b", re.IGNORECASE),
    "consumer-bettor-arena": re.compile(r"\bbettor-arena\b", re.IGNORECASE),
    "consumer-antigravity": re.compile(r"\bantigravity\b", re.IGNORECASE),
    "consumer-ix-agy": re.compile(r"\bix-agy\b", re.IGNORECASE),
}
TOP_KEY = re.compile(r"^([A-Za-z0-9_-]+):(?:\s|$)")


class CompareError(Exception):
    pass


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        raise CompareError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result


def show(root: Path, ref: str, path: str) -> str:
    return git(root, "show", f"{ref}:{path}").stdout


def exists(root: Path, ref: str, path: str) -> bool:
    return git(root, "cat-file", "-e", f"{ref}:{path}", check=False).returncode == 0


def list_paths(root: Path, ref: str, prefix: str) -> list[str]:
    result = git(root, "ls-tree", "-r", "--name-only", ref, "--", prefix, check=False)
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def frontmatter_keys(text: str) -> set[str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return set()
    keys: set[str] = set()
    for line in lines[1:]:
        if line.strip() == "---":
            return keys
        if not line or line.startswith((" ", "\t")):
            continue
        match = TOP_KEY.match(line)
        if match:
            keys.add(match.group(1))
    return keys


def portable_markdown(root: Path, ref: str) -> dict[str, str]:
    paths = [SKILL_PATH]
    paths.extend(
        path
        for path in list_paths(root, ref, f"{SKILL_ROOT}/modules")
        if path.endswith(".md")
    )
    result: dict[str, str] = {}
    for path in paths:
        if exists(root, ref, path):
            result[path] = show(root, ref, path)
    return result


def measure(root: Path, ref: str) -> dict:
    skill = show(root, ref, SKILL_PATH)
    markdown = portable_markdown(root, ref)
    hits: list[dict[str, str]] = []
    for path, text in markdown.items():
        for label, pattern in FORBIDDEN.items():
            for match in pattern.finditer(text):
                hits.append({"path": path, "rule": label, "match": match.group(0)[:120]})
    keys = frontmatter_keys(skill)
    support = sorted(path for path in REQUIRED_SUPPORT if exists(root, ref, path))
    cases = [
        path
        for path in list_paths(root, ref, "evals/cases/repo-agent-native")
        if path.endswith(".json")
    ]
    headings = set(skill.splitlines())
    return {
        "ref": ref,
        "skill_bytes": len(skill.encode("utf-8")),
        "skill_lines": len(skill.splitlines()),
        "frontmatter_fields": sorted(keys),
        "nonportable_frontmatter_fields": sorted(keys - PORTABLE_FIELDS),
        "required_headings_present": len(REQUIRED_HEADINGS & headings),
        "required_headings_total": len(REQUIRED_HEADINGS),
        "support_files_present": support,
        "support_files_total": len(REQUIRED_SUPPORT),
        "behavior_case_count": len(cases),
        "forbidden_portable_hits": hits,
    }


def compare(baseline: dict, candidate: dict) -> dict:
    hard_gates = {
        "portable_frontmatter": not candidate["nonportable_frontmatter_fields"],
        "portable_body": not candidate["forbidden_portable_hits"],
        "progressive_disclosure": candidate["skill_lines"] <= 500,
        "procedure_complete": candidate["required_headings_present"] == candidate["required_headings_total"],
        "executable_assertions": {
            f"{SKILL_ROOT}/scripts/check_repo_agent_native.py",
            f"{SKILL_ROOT}/tests/verify.sh",
        }.issubset(candidate["support_files_present"]),
        "codex_metadata": f"{SKILL_ROOT}/agents/openai.yaml" in candidate["support_files_present"],
        "eval_closure": (
            f"{SKILL_ROOT}/evals.json" in candidate["support_files_present"]
            and "evals/verifiers/verify_repo_agent_native_output.py" in candidate["support_files_present"]
            and candidate["behavior_case_count"] >= 4
        ),
        "context_reduction": candidate["skill_lines"] < baseline["skill_lines"],
        "consumer_leakage_reduced": (
            len(candidate["forbidden_portable_hits"]) < len(baseline["forbidden_portable_hits"])
        ),
    }
    improvements = {
        "skill_lines_delta": candidate["skill_lines"] - baseline["skill_lines"],
        "skill_bytes_delta": candidate["skill_bytes"] - baseline["skill_bytes"],
        "support_files_delta": len(candidate["support_files_present"]) - len(baseline["support_files_present"]),
        "behavior_cases_delta": candidate["behavior_case_count"] - baseline["behavior_case_count"],
        "forbidden_hits_delta": len(candidate["forbidden_portable_hits"]) - len(baseline["forbidden_portable_hits"]),
    }
    return {
        "hard_gates": hard_gates,
        "improvements": improvements,
        "static_contract_state": "PASS" if all(hard_gates.values()) else "FAIL",
        "physical_model_output_state": "NOT_EXERCISED",
        "physical_evidence_required": (
            "Run no_skill/current_skill/candidate_skill/wrong_skill in fresh workspaces, "
            "zero retries, at least three seeds, with deterministic output verification."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--baseline-ref", default="d277e56870c0cc18455c9dd5e572a43ca08b444b")
    parser.add_argument("--candidate-ref", default="HEAD")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        baseline = measure(root, args.baseline_ref)
        candidate = measure(root, args.candidate_ref)
        comparison = compare(baseline, candidate)
        report = {
            "schema_version": "repo-agent-native-static-ab/v1",
            "baseline": baseline,
            "candidate": candidate,
            "comparison": comparison,
        }
    except (CompareError, OSError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 2
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    stream = sys.stdout if comparison["static_contract_state"] == "PASS" else sys.stderr
    print(text, end="", file=stream)
    return 0 if comparison["static_contract_state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
