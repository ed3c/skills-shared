#!/usr/bin/env python3
"""Normalize a repo-agent-native physical receipt into skill-eval-run/v1.

This adapter translates; it never decides semantic correctness. The passed bit
must come from a content-bound deterministic verifier receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def load(path: Path, label: str) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def nonnegative_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be an observed non-negative integer")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--verifier-receipt", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        receipt_path = Path(args.receipt)
        receipt = load(receipt_path, "physical receipt")
        verifier = load(Path(args.verifier_receipt), "verifier receipt")
        if receipt.get("schema") != "repo-agent-native/ab-run-receipt/v1":
            raise ValueError("unsupported physical receipt")
        if verifier.get("schema_version") != "skill-eval-verifier-receipt/v1" or verifier.get("authority") != "deterministic":
            raise ValueError("deterministic verifier receipt required")
        if verifier.get("run_id") != receipt.get("run_id") or verifier.get("case_id") != receipt.get("scenario"):
            raise ValueError("physical/verifier identity mismatch")
        model, carrier = receipt.get("model"), receipt.get("carrier")
        operational, execution = receipt.get("operational"), receipt.get("execution")
        skill = receipt.get("skill")
        if not all(isinstance(item, dict) for item in (model, carrier, operational, execution, skill)):
            raise ValueError("receipt identity or telemetry object absent")
        input_tokens = nonnegative_int(operational.get("input_tokens"), "input_tokens")
        output_tokens = nonnegative_int(operational.get("output_tokens"), "output_tokens")
        tool_calls = nonnegative_int(operational.get("tool_calls"), "tool_calls")
        duration_ms = execution.get("duration_ms")
        if isinstance(duration_ms, bool) or not isinstance(duration_ms, int) or duration_ms < 0:
            raise ValueError("duration_ms must be observed")
        condition = receipt.get("condition")
        instruction_digest = skill.get("instruction_digest")
        if condition == "no_skill":
            if skill.get("name") is not None or instruction_digest is not None:
                raise ValueError("no_skill installed a Skill")
        elif not isinstance(instruction_digest, str) or len(instruction_digest) != 64:
            raise ValueError("treated condition lacks a content digest")
        identity = "|".join([
            str(receipt.get("run_id")), str(receipt.get("fixture_commit")),
            str(receipt.get("subject_bundle", {}).get("sha256")),
            str(verifier.get("input_digest")),
        ])
        run_id = hashlib.sha256(identity.encode()).hexdigest()[:24]
        passed = verifier.get("passed")
        if not isinstance(passed, bool):
            raise ValueError("verifier passed must be boolean")
        trace = {
            "schema_version": "skill-eval-run/v1",
            "run_id": run_id,
            "case_id": receipt["scenario"],
            "condition": condition,
            "skill_sha": instruction_digest,
            "model": {"provider": model.get("provider"), "name": model.get("name")},
            "harness": {"name": carrier.get("id"), "version": carrier.get("version")},
            "environment": {"runtime": "bun+native-carrier", "fresh_workspace": True, "network_policy": "deny"},
            "sampling": {"kind": "repetition", "index": receipt["repetition"], "seed": None},
            "outcome": {
                "passed": passed,
                "verifier": "repo-agent-native-deterministic",
                "failure_class": None if passed else "weak-verification",
            },
            "metrics": {
                "wall_seconds": duration_ms / 1000,
                "tool_calls": tool_calls,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "retries": nonnegative_int(receipt.get("limits", {}).get("retries"), "retries"),
            },
            "artifacts": [str(receipt_path)],
        }
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
