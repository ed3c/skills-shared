#!/usr/bin/env python3
"""Prove that each declared guard has a control that catches its removal.

This closes shape D of #122: an assertion that runs but cannot fail. A guard
with no control is indistinguishable from a guard that works, and the whole
suite stays green either way.

Doing it by hand across this session found the defect repeatedly -- four
calibration ceilings with no control, a digest check nothing could observe, a
claim ceiling made redundant by the check after it. It also produced eight
*false* findings, every one the same way: the mutation reported "this guard has
no control" while having changed nothing. A wrong field name, a regex that
matched zero times, and `if not X or Y` rewritten as `if False and not X or Y`,
which and/or precedence turns straight back into `if Y`.

So the load-bearing rule here is not "mutate and observe". It is:

    a mutation that cannot prove it changed the bytes is not a mutation,
    and reporting it as a finding is worse than not running it

The flow per guard:

    1. baseline verify must pass    -- an assertion behind an always-failing
                                       step is unreachable, which is shape C;
                                       a red baseline is reported as such
    2. the anchor must be present exactly once
    3. neutralising it must change the file
    4. verify must then fail        -- otherwise the guard has no control
    5. restore, and baseline must pass again

Exits: 0 every guard controlled, 2 a guard has no control, 64 unusable input.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

SCHEMA = "guard-control-manifest/v1"


class Unusable(Exception):
    """The manifest or a declared file could not be read."""


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise Unusable(f"unreadable manifest: {error}") from error
    except json.JSONDecodeError as error:
        raise Unusable(f"unparseable manifest: {error}") from error
    if body.get("schema") != SCHEMA:
        raise Unusable(f"manifest schema must be {SCHEMA}")
    entries = body.get("guards")
    if not isinstance(entries, list) or not entries:
        raise Unusable("manifest declares no guards")
    return body


def neutralise(anchor: str) -> str:
    """Replace the whole condition, never prefix it.

    `if False and <original>` is the obvious rewrite and it is wrong on any
    compound condition: `if False and not X or Y` evaluates as `if Y`, leaving
    the guard live while the test reports it removed.
    """
    stripped = anchor.strip()
    indent = anchor[: len(anchor) - len(anchor.lstrip())]
    for keyword in ("elif", "if", "while"):
        if stripped.startswith(keyword + " ") or stripped.startswith(keyword + "("):
            return f"{indent}{keyword} False:"
    return f"{indent}pass"


def run(argv: list[str], cwd: Path, timeout: int) -> tuple[int, str]:
    try:
        result = subprocess.run(
            argv, cwd=cwd, capture_output=True, text=True, check=False, timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        output = "\n".join(
            part.decode(errors="replace") if isinstance(part, bytes) else (part or "")
            for part in (error.stdout, error.stderr)
        ).strip()
        return 124, output[-2000:]
    except OSError as error:
        raise Unusable(f"cannot execute {argv[0]!r}: {error}") from error
    output = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    return result.returncode, output[-2000:]


def check_guard(repo_root: Path, guard: dict[str, Any], timeout: int) -> list[str]:
    problems: list[str] = []
    label = guard.get("id", "<unnamed>")
    target_rel = guard["file"]
    anchor = guard["anchor"]
    verify = guard["verify"]

    source_path = repo_root / target_rel
    try:
        original = source_path.read_text(encoding="utf-8")
    except OSError as error:
        raise Unusable(f"{label}: unreadable {target_rel}: {error}") from error

    occurrences = original.count(anchor)
    if occurrences == 0:
        return [f"{label}: anchor is absent from {target_rel}; it has drifted"]
    if occurrences > 1:
        return [
            f"{label}: anchor appears {occurrences} times in {target_rel}; a "
            f"mutation would not identify which guard it removed"
        ]

    mutated = original.replace(anchor, neutralise(anchor), 1)
    if mutated == original:
        return [f"{label}: neutralising the anchor changed nothing"]

    with tempfile.TemporaryDirectory(prefix="guard-control.") as raw:
        work = Path(raw) / "repo"
        shutil.copytree(repo_root, work, symlinks=True, ignore=shutil.ignore_patterns(
            ".git", "__pycache__", "node_modules", ".claude"))

        baseline, baseline_output = run(verify, work, timeout)
        if baseline != 0:
            detail = f"; verifier output: {baseline_output}" if baseline_output else ""
            return [
                f"{label}: baseline verify exits {baseline} before any mutation; "
                f"its assertions are unreachable, so this guard is unproven "
                f"rather than uncontrolled{detail}"
            ]

        (work / target_rel).write_text(mutated, encoding="utf-8")
        if (work / target_rel).read_text(encoding="utf-8") == original:
            return [f"{label}: the mutation did not reach the file under test"]

        mutated_code, _ = run(verify, work, timeout)
        if mutated_code == 0:
            problems.append(
                f"{label}: removing the guard in {target_rel} left the verify "
                f"green; this assertion runs but cannot fail"
            )
        elif mutated_code == 124:
            problems.append(f"{label}: verify timed out under mutation")

        (work / target_rel).write_text(original, encoding="utf-8")
        restored, restored_output = run(verify, work, timeout)
        if restored != 0:
            detail = f"; verifier output: {restored_output}" if restored_output else ""
            problems.append(
                f"{label}: verify does not return to green after restoring the "
                f"guard, so the mutation result is not attributable to it{detail}"
            )

    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--only", action="append", default=[],
                        help="check only these guard ids")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    if args.selftest:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from guard_control_selftest import run_selftest
        return run_selftest(repo_root)

    manifest_path = args.manifest or (repo_root / "evals" / "guard-controls.json")
    try:
        manifest = load_manifest(manifest_path)
        guards = manifest["guards"]
        if args.only:
            guards = [g for g in guards if g.get("id") in set(args.only)]
            if not guards:
                raise Unusable(f"no guard matches {args.only}")
        timeout = int(manifest.get("timeout_seconds", 300))
        problems: list[str] = []
        for guard in guards:
            problems.extend(check_guard(repo_root, guard, timeout))
    except Unusable as error:
        print(f"FATAL guard-controls: {error}", file=sys.stderr)
        return 64

    if problems:
        for item in problems:
            print(f"GUARD CONTROL RED: {item}", file=sys.stderr)
        return 2

    print(f"GUARD CONTROL GREEN: {len(guards)} guard(s) each caught by a control")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
