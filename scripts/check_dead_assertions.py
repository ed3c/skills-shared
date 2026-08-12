#!/usr/bin/env python3
"""Fail on shell assertions whose exit status cannot enforce the intended guard.

Scope is intentionally narrow and zero-network: tests/**/verify.sh and
*/tests/run-all.sh. The linter reports line numbers and a concrete rewrite.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

LEADING_BANG = re.compile(r"^\s*!\s+(.+)$")
TEST_AND_TEST = re.compile(r"^\s*test\b.+&&\s*test\b")
OR_TRUE = re.compile(r"\|\|\s*(?:true|:)\s*(?:#.*)?$")
GREP_DEVNULL = re.compile(r"^\s*grep\b(?![^#\n]*\s-q(?:\s|$))[^#\n]*(?:>|1>)\s*/dev/null\s*(?:#.*)?$")
CONDITION_PREFIX = re.compile(r"^\s*(?:if|while|until)\b")


def is_target(path: Path) -> bool:
    parts = path.parts
    if path.name == "verify.sh" and "tests" in parts:
        return True
    return path.name == "run-all.sh" and "tests" in parts


def lint_line(path: Path, number: int, line: str) -> list[str]:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return []
    if CONDITION_PREFIX.match(line):
        return []

    findings: list[str] = []
    if LEADING_BANG.match(line):
        findings.append(
            f"{path}:{number}: dead-leading-bang: leading `!` is exempt from set -e/ERR; "
            "rewrite as `if <command>; then echo ... >&2; exit 1; fi`"
        )
    if TEST_AND_TEST.match(line):
        findings.append(
            f"{path}:{number}: dead-and-chain: the left side of `test ... && test ...` is exempt from set -e; "
            "split assertions onto separate lines or use an explicit `if`"
        )
    if OR_TRUE.search(line):
        findings.append(
            f"{path}:{number}: swallowed-status: `|| true`/`|| :` replaces the command status; "
            "capture it directly with `|| rc=$?` and assert rc explicitly"
        )
    if GREP_DEVNULL.match(line):
        findings.append(
            f"{path}:{number}: discarded-grep-status: use `grep -q ...` inside an explicit assertion instead of redirecting unused output"
        )
    return findings


def lint_file(path: Path) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        return [f"{path}: unreadable: {exc}"]
    findings: list[str] = []
    for index, line in enumerate(lines):
        findings.extend(lint_line(path, index + 1, line))
    return findings


def discover(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.sh") if path.is_file() and is_target(path))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", help="files/directories; default: repository root")
    args = parser.parse_args()
    roots = [Path(value) for value in args.paths] if args.paths else [Path(__file__).resolve().parents[1]]
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            files.append(root)
        elif root.is_dir():
            files.extend(discover(root))
        else:
            print(f"FAIL: path does not exist: {root}", file=sys.stderr)
            return 2
    files = sorted(dict.fromkeys(path.resolve() for path in files))
    findings: list[str] = []
    for path in files:
        findings.extend(lint_file(path))
    if findings:
        for finding in findings:
            print(f"FAIL: {finding}", file=sys.stderr)
        return 1
    print(f"PASS dead-assertion lint: {len(files)} shell test files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
