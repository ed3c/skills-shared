#!/usr/bin/env python3
"""Build canonical skill-eval-run/v1 from executor evidence + deterministic receipt."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict): raise ValueError(f"{path} must contain object")
    return value


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--executor-evidence", required=True); p.add_argument("--verifier-receipt", required=True)
    p.add_argument("--routing-evidence", required=True); p.add_argument("--output", required=True)
    # Both fields were hardcoded to skill-up's environment, so any second
    # harness's trace claimed it had run under skill-up, and every physical run
    # claimed no-network while its agent was talking to a model API. The
    # defaults keep existing skill-up callers byte-identical; a caller that
    # knows better must say so.
    p.add_argument("--runtime", default="skill-up:none")
    p.add_argument("--network-policy", default="no-network")
    args = p.parse_args()
    try:
        executor = load(Path(args.executor_evidence)); receipt = load(Path(args.verifier_receipt)); routing = load(Path(args.routing_evidence))
        if executor.get("schema_version") != "skill-eval-executor-evidence/v1": raise ValueError("unsupported executor evidence")
        if receipt.get("schema_version") != "skill-eval-verifier-receipt/v1" or receipt.get("authority") != "deterministic": raise ValueError("deterministic verifier receipt required")
        if receipt.get("run_id") != executor.get("run_id") or receipt.get("case_id") != executor.get("case_id"): raise ValueError("executor/verifier identity mismatch")
        sampling = executor.get("sampling")
        if not isinstance(sampling, dict): raise ValueError("executor sampling metadata missing")
        if sampling.get("seed_controlled") is True:
            seed = sampling.get("model_seed")
            if not isinstance(seed, int): raise ValueError("controlled model seed missing")
            canonical_sampling = {"kind": "controlled_seed", "index": int(sampling.get("repetition_index", 1) or 1), "seed": seed}
        else:
            if sampling.get("model_seed") is not None: raise ValueError("uncontrolled executor cannot claim seed")
            repetition = sampling.get("repetition_index")
            if not isinstance(repetition, int) or repetition < 1: raise ValueError("repetition index missing")
            canonical_sampling = {"kind": "repetition", "index": repetition, "seed": None}
        if routing.get("case_id") != executor.get("case_id"): raise ValueError("routing evidence case mismatch")
        condition = executor.get("condition")
        expected_decision = "invoke" if condition != "no_skill" else routing.get("decision")
        metrics = executor.get("outcome", {})
        trace = {
            "schema_version": "skill-eval-run/v1",
            "run_id": executor["run_id"], "case_id": executor["case_id"], "condition": condition,
            "skill_sha": executor.get("skill_sha"), "model": executor["model"],
            "harness": {"name": executor["harness"]["name"], "version": executor["harness"]["version"]},
            "environment": {"runtime": args.runtime, "fresh_workspace": True, "network_policy": args.network_policy},
            "sampling": canonical_sampling,
            "outcome": {"passed": bool(receipt.get("passed")), "verifier": "deterministic-script", "failure_class": None if receipt.get("passed") else "weak-verification"},
            "routing": {"should_invoke": condition != "no_skill", "did_invoke": routing.get("decision") == "invoke", "selected_skill": routing.get("selected_skill")},
            "metrics": {"wall_seconds": float(metrics.get("duration_ms", 0) or 0) / 1000.0, "tool_calls": 0, "input_tokens": int(metrics.get("input_tokens", 0) or 0), "output_tokens": int(metrics.get("output_tokens", 0) or 0), "retries": 0},
            "artifacts": ["evidence/run.json", "artifacts/iteration-contract.json"],
        }
        out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n")
        print(trace["run_id"]); return 0
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr); return 1


if __name__ == "__main__": raise SystemExit(main())
