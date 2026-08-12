#!/usr/bin/env python3
"""Build skill-eval-evidence/v1 from one normalized run and verifier receipt."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--run-trace", required=True)
    p.add_argument("--verifier-receipt", required=True)
    p.add_argument("--eval-suite-sha", required=True)
    p.add_argument("--raw-result")
    p.add_argument("--artifact", action="append", default=[])
    p.add_argument("--replay-command")
    p.add_argument("--output", required=True)
    args = p.parse_args()
    try:
        run_path = Path(args.run_trace)
        run = json.loads(run_path.read_text(encoding="utf-8"))
        receipt = Path(args.verifier_receipt)
        if not receipt.is_file():
            raise ValueError("verifier receipt does not exist")
        artifacts = {}
        for value in args.artifact:
            path = Path(value)
            if not path.is_file():
                raise ValueError(f"artifact does not exist: {value}")
            artifacts[value] = sha256(path)
        raw = Path(args.raw_result) if args.raw_result else None
        if raw is not None and not raw.is_file():
            raise ValueError("raw result does not exist")
        bundle = {
            "schema_version": "skill-eval-evidence/v1",
            "run_id": run["run_id"],
            "case_id": run["case_id"],
            "skill_sha": run.get("skill_sha"),
            "eval_suite_sha": args.eval_suite_sha,
            "run_trace": str(run_path),
            "verifier_receipt": str(receipt),
            "artifact_hashes": artifacts,
            "executor_raw_result": str(raw) if raw else None,
            "replay": {
                "offline_capable": bool(args.replay_command),
                "command": args.replay_command,
                "notes": None if args.replay_command else "Executor replay requires its original harness/runtime.",
            },
        }
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(bundle["run_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
