#!/usr/bin/env python3
"""Build skill-eval-evidence/v1 from one normalized run and verifier receipt.

Executor/LLM judge output is analysis evidence only. A deterministic verifier
PASS or FAIL may be bundled so the denominator is preserved; only PASS bundles
are promotion-eligible.
"""
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


def load_object(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return value


def validate_receipt(run: dict, receipt: dict) -> None:
    if receipt.get("schema_version") != "skill-eval-verifier-receipt/v1": raise ValueError("unsupported verifier receipt schema")
    if receipt.get("run_id") != run.get("run_id"): raise ValueError("verifier receipt run_id does not match run trace")
    if receipt.get("case_id") != run.get("case_id"): raise ValueError("verifier receipt case_id does not match run trace")
    if receipt.get("authority") != "deterministic": raise ValueError("evidence bundle requires deterministic verifier authority")
    if not isinstance(receipt.get("passed"), bool): raise ValueError("verifier receipt passed must be boolean")
    verifier = receipt.get("verifier")
    if not isinstance(verifier, dict): raise ValueError("verifier receipt missing verifier identity")
    digest = verifier.get("implementation_sha256")
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest): raise ValueError("verifier implementation digest must be lowercase sha256")
    input_digest = receipt.get("input_digest")
    if not isinstance(input_digest, str) or len(input_digest) != 64 or any(c not in "0123456789abcdef" for c in input_digest): raise ValueError("verifier input_digest must be lowercase sha256")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--run-trace", required=True); p.add_argument("--verifier-receipt", required=True)
    p.add_argument("--eval-suite-sha", required=True); p.add_argument("--raw-result")
    p.add_argument("--artifact", action="append", default=[]); p.add_argument("--replay-command"); p.add_argument("--output", required=True)
    args = p.parse_args()
    try:
        run_path = Path(args.run_trace); run = load_object(run_path, "run trace")
        receipt_path = Path(args.verifier_receipt); receipt = load_object(receipt_path, "verifier receipt"); validate_receipt(run, receipt)
        artifacts = {}
        for value in args.artifact:
            path = Path(value)
            if not path.is_file(): raise ValueError(f"artifact does not exist: {value}")
            artifacts[value] = sha256(path)
        raw = Path(args.raw_result) if args.raw_result else None
        if raw is not None and not raw.is_file(): raise ValueError("raw result does not exist")
        bundle = {
            "schema_version": "skill-eval-evidence/v1", "run_id": run["run_id"], "case_id": run["case_id"],
            "skill_sha": run.get("skill_sha"), "eval_suite_sha": args.eval_suite_sha, "run_trace": str(run_path),
            "verifier_receipt": str(receipt_path), "verifier_receipt_sha256": sha256(receipt_path),
            "promotion_eligible": receipt["passed"], "artifact_hashes": artifacts,
            "executor_raw_result": str(raw) if raw else None,
            "replay": {"offline_capable": bool(args.replay_command), "command": args.replay_command, "notes": None if args.replay_command else "Executor replay requires its original harness/runtime."},
        }
        out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (KeyError, TypeError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr); return 1
    print(bundle["run_id"]); return 0


if __name__ == "__main__": raise SystemExit(main())
