#!/usr/bin/env python3
"""Fail when external-source identifiers leak into files or directories."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

FORBIDDEN = (
    "skill" + "-bettor",
    "/Users/neon/" + "skill" + "-bettor",
)


def iter_files(target: Path) -> list[Path]:
    """Return regular files beneath a target, or the target itself."""
    if target.is_file():
        return [target]
    if target.is_dir():
        return sorted(path for path in target.rglob("*") if path.is_file())
    raise ValueError(f"target does not exist: {target}")


def scan(targets: list[Path], tokens: tuple[str, ...] = FORBIDDEN) -> list[str]:
    """Return human-readable leaks found in UTF-8-decodable files."""
    leaks: list[str] = []
    for target in targets:
        for path in iter_files(target):
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            lowered = text.lower()
            for token in tokens:
                if token.lower() in lowered:
                    leaks.append(f"{path}: forbidden external-source identifier")
    return leaks


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deny-token", action="append", default=[])
    parser.add_argument("targets", nargs="+", type=Path)
    args = parser.parse_args(argv)
    tokens = tuple(args.deny_token) if args.deny_token else FORBIDDEN
    try:
        leaks = scan(args.targets, tokens)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if leaks:
        for leak in leaks:
            print(f"FAIL: {leak}", file=sys.stderr)
        return 2
    print("PASS: external-source identifiers are redacted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
