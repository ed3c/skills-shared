#!/usr/bin/env python3
"""Run a public case's deterministic verifier over collected executor artifacts.

The executor's judge is not trusted for promotion. This script resolves the
reviewed public case, runs its script verifier from the collected workspace,
and emits a content-bound skill-eval-verifier-receipt/v1 even on verifier fail.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def resolve_case(case_id: str) -> tuple[Path, dict]:
    hits = list((ROOT / "evals" / "cases").rglob(f"{case_id}.json"))
    if len(hits) != 1:
        raise ValueError(f"expected one public case {case_id!r}, got {len(hits)}")
    case = load_object(hits[0])
    verifier = case.get("verifier")
    if not isinstance(verifier, dict) or verifier.get("type") != "script":
        raise ValueError("promotion replay requires a script verifier")
    return hits[0], case


def verifier_argv(command: str) -> tuple[list[str], Path]:
    argv = shlex.split(command)
    if len(argv) < 2 or argv[0] not in {"python", "python3"}:
        raise ValueError("only repository Python script verifiers are supported")
    script = Path(argv[1])
    if script.is_absolute() or ".." in script.parts:
        raise ValueError("verifier script must be repository-relative")
    resolved = (ROOT / script).resolve()
    if ROOT.resolve() not in resolved.parents or not resolved.is_file():
        raise ValueError("verifier script is outside repository or missing")
    argv[1] = str(resolved)
    return argv, resolved


def input_digest(case_path: Path, workspace: Path, expected: list[str]) -> str:
    h = hashlib.sha256()
    for path in [case_path, *[(workspace / rel) for rel in sorted(expected)]]:
        if not path.is_file():
            raise ValueError(f"required verifier input missing: {path}")
        h.update(str(path.name).encode())
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--case", required=True)
    p.add_argument("--workspace", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    try:
        workspace = Path(args.workspace).resolve()
        if not workspace.is_dir():
            raise ValueError("collected workspace does not exist")
        case_path, case = resolve_case(args.case)
        expected = case.get("task", {}).get("expected_artifacts", [])
        if not isinstance(expected, list) or not expected or not all(isinstance(x, str) and x for x in expected):
            raise ValueError("case must declare expected_artifacts for deterministic replay")
        digest = input_digest(case_path, workspace, expected)
        argv, verifier_path = verifier_argv(str(case["verifier"]["command"]))
        proc = subprocess.run(argv, cwd=workspace, text=True, capture_output=True, check=False)
        receipt = {
            "schema_version": "skill-eval-verifier-receipt/v1",
            "run_id": args.run_id,
            "case_id": args.case,
            "authority": "deterministic",
            "verifier": {
                "kind": "script",
                "implementation_sha256": sha256_file(verifier_path),
            },
            "passed": proc.returncode == 0,
            "input_digest": digest,
            "replay_command": " ".join(shlex.quote(x) for x in argv),
            "notes": None,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:],
        }
        # Keep the schema surface stable by storing execution logs separately.
        logs = {"stdout": receipt.pop("stdout"), "stderr": receipt.pop("stderr"), "exit_code": proc.returncode}
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        out.with_suffix(out.suffix + ".logs.json").write_text(json.dumps(logs, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"passed": receipt["passed"], "receipt": str(out)}, sort_keys=True))
        return 0 if proc.returncode == 0 else 1
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
