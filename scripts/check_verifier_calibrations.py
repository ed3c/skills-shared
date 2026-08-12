#!/usr/bin/env python3
"""Calibrate deterministic gold-replay verifiers against good and hollow fixtures.

A verifier is not trusted merely because its file exists. For every gold-replay
case this gate executes the repository-owned script verifier against one positive
fixture (must exit 0) and one or more negative fixtures (must exit non-zero).
Only direct Python/Bash script commands are accepted; arbitrary shell pipelines
are intentionally outside this calibration runner.
"""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path

SHELL_CONTROL_TOKENS = {"&&", "||", ";", "|", ">", ">>", "<", "<<", "&"}


def load_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def inside(root: Path, raw: str, *, kind: str) -> Path:
    path = (root / raw).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"{kind} escapes repository: {raw}") from exc
    return path


def verifier_argv(root: Path, command: str) -> list[str]:
    words = shlex.split(command)
    if len(words) < 2:
        raise ValueError("calibrated verifier command must name an interpreter and script")
    if any(word in SHELL_CONTROL_TOKENS for word in words):
        raise ValueError("calibration permits only direct verifier commands; shell pipelines/control operators are forbidden")
    interpreter, script_raw, *args = words
    script = inside(root, script_raw, kind="verifier script")
    if not script.is_file():
        raise ValueError(f"verifier script does not exist: {script_raw}")
    if script.suffix == ".py" and interpreter in {"python", "python3"}:
        return [sys.executable, str(script), *args]
    if script.suffix == ".sh" and interpreter in {"bash", "sh"}:
        shell = "/bin/bash" if interpreter == "bash" else "/bin/sh"
        return [shell, str(script), *args]
    raise ValueError("calibration permits only direct `python[3] script.py` or `bash|sh script.sh` commands")


def run_fixture(argv: list[str], fixture: Path, timeout: int) -> subprocess.CompletedProcess[str]:
    if not fixture.is_dir():
        raise ValueError(f"calibration fixture directory does not exist: {fixture}")
    return subprocess.run(
        argv,
        cwd=fixture,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def calibrate_case(root: Path, case_path: Path, timeout: int) -> list[str]:
    case = load_object(case_path)
    if case.get("split") != "gold-replay":
        return []
    case_id = case.get("id", case_path.stem)
    verifier = case.get("verifier")
    if not isinstance(verifier, dict) or verifier.get("type") != "script":
        return [f"{case_id}: gold-replay requires a script verifier for deterministic calibration"]
    command = verifier.get("command")
    if not isinstance(command, str) or not command.strip():
        return [f"{case_id}: calibrated script verifier has no command"]
    calibration = case.get("calibration")
    if not isinstance(calibration, dict):
        return [f"{case_id}: gold-replay requires calibration metadata"]
    positive = calibration.get("positive_fixture")
    negatives = calibration.get("negative_fixtures")
    if not isinstance(positive, str) or not positive.strip():
        return [f"{case_id}: calibration.positive_fixture must be a non-empty path"]
    if not isinstance(negatives, list) or not negatives or any(not isinstance(x, str) or not x.strip() for x in negatives):
        return [f"{case_id}: calibration.negative_fixtures must be a non-empty string array"]
    if len(set(negatives)) != len(negatives):
        return [f"{case_id}: calibration.negative_fixtures contains duplicates"]

    errors: list[str] = []
    try:
        argv = verifier_argv(root, command)
        positive_path = inside(root, positive, kind="positive calibration fixture")
        result = run_fixture(argv, positive_path, timeout)
        if result.returncode != 0:
            errors.append(
                f"{case_id}: positive calibration failed with exit {result.returncode}: "
                f"{(result.stderr or result.stdout).strip()[:240]}"
            )
        for raw in negatives:
            negative_path = inside(root, raw, kind="negative calibration fixture")
            result = run_fixture(argv, negative_path, timeout)
            if result.returncode == 0:
                errors.append(
                    f"{case_id}: hollow calibration unexpectedly passed: {raw}; "
                    "verifier does not discriminate this invalid outcome"
                )
    except (OSError, ValueError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        errors.append(f"{case_id}: calibration error: {exc}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.timeout < 1 or args.timeout > 300:
        print("FAIL calibration timeout must be between 1 and 300 seconds", file=sys.stderr)
        return 2
    case_root = root / "evals" / "cases"
    case_paths = sorted(case_root.rglob("*.json")) if case_root.is_dir() else []
    errors: list[str] = []
    gold = 0
    for path in case_paths:
        try:
            value = load_object(path)
            if value.get("split") == "gold-replay":
                gold += 1
            errors.extend(calibrate_case(root, path, args.timeout))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: {exc}")
    if gold == 0:
        errors.append("no gold-replay cases found; calibration absence is not success")
    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        return 1
    print(f"PASS verifier calibration: {gold} gold-replay case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
