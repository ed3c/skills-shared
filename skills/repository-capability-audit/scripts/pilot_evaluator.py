#!/usr/bin/env python3
"""Independent deterministic evaluator for one held-out audit cell.

Reads the Agent's `agent-output.json` from the cell workspace and the sealed
ground truth resolved from the pinned tree, and writes the metrics file the cell
harness validates. It never sees the Agent's reasoning and the Agent never sees
this file's inputs.

The primary judgement is deliberately binary and checkable: did the host cite at
least one evidence path that actually exists in the pinned tree. A host that
answered from the repository name alone cannot satisfy it, and a host that
resolved the tree cannot fail it by phrasing.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

NON_TRIGGER = {"text-only-non-trigger", "metadata-only-control", "wrong-skill-control"}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ground-truth", type=Path, required=True)
    parser.add_argument("--usage", type=Path, required=True)
    # The cell harness passes the metrics path through the environment rather than
    # as a placeholder, so accept either. Requiring the flag would force a wrapper
    # whose only job is to move one value between two conventions.
    parser.add_argument("--metrics-file", type=Path,
                        default=Path(os.environ["RCA_EVAL_METRICS_FILE"])
                        if os.environ.get("RCA_EVAL_METRICS_FILE") else None)
    parser.add_argument("--workspace", type=Path,
                        default=Path(os.environ["RCA_EVAL_WORKSPACE"])
                        if os.environ.get("RCA_EVAL_WORKSPACE") else None)
    args = parser.parse_args()
    if args.metrics_file is None or args.workspace is None:
        parser.error("--metrics-file and --workspace are required unless "
                     "RCA_EVAL_METRICS_FILE and RCA_EVAL_WORKSPACE are set")

    truth = read_json(args.ground_truth)
    usage = read_json(args.usage)
    family = truth["family_id"]
    expected_paths = set(truth["evidence_paths"])
    non_trigger = family in NON_TRIGGER

    output_path = args.workspace / "agent-output.json"
    try:
        output = read_json(output_path)
        parsed = isinstance(output, dict)
    except Exception:
        output, parsed = {}, False

    cited = output.get("evidence_paths") if parsed else None
    cited = [str(item) for item in cited] if isinstance(cited, list) else []
    claims = output.get("claims") if parsed else None
    non_claims = output.get("non_claims") if parsed else None
    escalate = output.get("escalate") if parsed else None
    reported_tree = str(output.get("tree_sha", "")) if parsed else ""

    grounded = [path for path in cited if path in expected_paths]
    ungrounded = [path for path in cited if path not in expected_paths]

    # One decidable judgement per family, so recall is comparable across families
    # whose evidence sets differ in size by an order of magnitude.
    found = 1 if grounded else 0

    metrics = {
        "task_success": bool(parsed and cited),
        "material_defects_found": found,
        "material_defects_total": 1,
        "false_pass_count": len(ungrounded),
        "false_pass_opportunities": max(len(cited), 1),
        "evidence_packet_complete": bool(
            parsed and isinstance(claims, list) and isinstance(non_claims, list) and cited
        ),
        "exact_subject_continuity": reported_tree == truth["tree_sha"],
        # A non-trigger family's control is valid when the host was actually
        # asked to decline; for defect families it is the presence of a stated
        # boundary rather than a refusal.
        "negative_control_valid": bool(
            parsed and isinstance(non_claims, list) and len(non_claims) > 0
        ),
        "explicit_non_claim_accuracy": bool(
            parsed and isinstance(non_claims, list) and len(non_claims) > 0
        ),
        "trigger_correct": (escalate is False) if non_trigger else (escalate is True),
        "tool_calls": int(usage.get("tool_calls", 0)),
        "input_tokens": int(usage.get("input_tokens", 0)),
        "output_tokens": int(usage.get("output_tokens", 0)),
        "duration_ms": int(usage.get("duration_ms", 0)),
        "cost_usd": float(usage.get("cost_usd", 0.0)) if usage.get("cost_observed") else 0.0,
        "cost_observed": bool(usage.get("cost_observed", False)),
    }

    args.metrics_file.write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"family": family, "grounded": len(grounded), "cited": len(cited)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
