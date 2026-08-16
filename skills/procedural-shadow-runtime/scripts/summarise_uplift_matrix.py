#!/usr/bin/env python3
"""Aggregate arm-trial receipts into a #219 verdict, and refuse to overstate it.

Exit codes:
  0   the matrix qualifies against the preregistration and a verdict was emitted
  2   the matrix is PARTIAL, or a receipt disagrees with the preregistration
  64  a receipt, the preregistration, or the output path is absent

The preregistration in
`skills/repository-capability-audit/evals/uplift-preregistration.json` fixes the
arms, the primary metric, the contrasts, the multiplicity correction, and the
repetition count, before any five-arm result existed. This script's only job is
to hold the aggregation to that document.

Two refusals do the work.

An underpowered run cannot be reported as the matrix. Below the preregistered
repetitions the verdict is PARTIAL, the exit code is 2, and `qualifies` is
false in the artefact -- so a citation has to reach past a machine-readable
flag to misuse it.

A saturated metric cannot be reported as a null. If the primary metric has zero
within-arm variance, that is a fact about the case set: no treatment signal can
appear in a quantity that does not move. The preregistration states this as a
stop rule and the aggregator implements it as a distinct verdict rather than
folding it into "no significant difference", which is the sentence a reader
would take as evidence the arms do not differ.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

SKILL = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
PREREGISTRATION = ROOT / "skills" / "repository-capability-audit" / "evals" / "uplift-preregistration.json"

INVALID = 64
REFUSED = 2

REQUIRED_ARMS = ["A_NO_SKILL", "B_METADATA_ONLY", "C_FULL_SKILL",
                 "D_DELTA_CAPSULE", "E_DELTA_CAPSULE_PLUS_HARNESS"]
CONTRASTS = [("C_FULL_SKILL", "A_NO_SKILL"), ("B_METADATA_ONLY", "A_NO_SKILL"),
             ("D_DELTA_CAPSULE", "C_FULL_SKILL"), ("E_DELTA_CAPSULE_PLUS_HARNESS", "D_DELTA_CAPSULE")]


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def cells_by_arm(receipt: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for cell in receipt["trial_matrix"]["cells"]:
        if cell.get("cell_state") == "HOST_ERROR":
            continue
        grouped.setdefault(cell["arm"], []).append(cell)
    return grouped


def arm_summary(cells: list[dict[str, Any]]) -> dict[str, Any]:
    rates = [cell["score"]["false_pass_rate"] for cell in cells
             if cell["score"]["false_pass_rate"] is not None]
    return {
        "n": len(cells),
        "primary_false_pass_rate_mean": round(statistics.fmean(rates), 4) if rates else None,
        "primary_within_arm_sd": round(statistics.stdev(rates), 4) if len(rates) > 1 else None,
        "task_success_rate": round(
            sum(1 for cell in cells if cell["score"]["task_success"]) / len(cells), 4) if cells else None,
        # Recorded, never scored. Only one host reports spend, and ranking on a
        # quantity the other cannot observe makes silence look like thrift.
        "secondary_recorded": {
            "median_duration_ms": statistics.median(
                [cell["observation"]["duration_ms"] for cell in cells]) if cells else None,
            "cost_observed": any(cell["observation"].get("cost_observed") for cell in cells),
            "median_cited_paths": statistics.median(
                [cell["score"]["cited_paths"] for cell in cells]) if cells else None,
        },
    }


def summarise(receipts: dict[str, dict[str, Any]], prereg: dict[str, Any]) -> dict[str, Any]:
    required_reps = prereg["power"]["repetitions_per_arm_per_host"]
    per_host: dict[str, Any] = {}
    all_rates: list[float] = []
    missing_arms: dict[str, list[str]] = {}
    host_errors: dict[str, list[str]] = {}

    for host, receipt in receipts.items():
        grouped = cells_by_arm(receipt)
        missing = [arm for arm in REQUIRED_ARMS if arm not in grouped]
        if missing:
            missing_arms[host] = missing
        errors = receipt["trial_matrix"].get("host_error_arms") or []
        if errors:
            host_errors[host] = errors
        per_host[host] = {
            "runtime": receipt["trial_matrix"]["runtime"],
            "model": receipt["trial_matrix"]["bindings"]["model"],
            "host_version": receipt["trial_matrix"]["bindings"]["host_version"],
            "policy": receipt["trial_matrix"]["bindings"]["policy"],
            "repetitions_per_arm": receipt["trial_matrix"]["repetitions_per_arm"],
            "arms": {arm: arm_summary(cells) for arm, cells in sorted(grouped.items())},
        }
        for cells in grouped.values():
            all_rates.extend(cell["score"]["false_pass_rate"] for cell in cells
                             if cell["score"]["false_pass_rate"] is not None)

    observed_reps = min((receipt["trial_matrix"]["repetitions_per_arm"]
                         for receipt in receipts.values()), default=0)
    qualifies = (observed_reps >= required_reps and not missing_arms and not host_errors
                 and len(receipts) >= 2)
    saturated = bool(all_rates) and len(set(all_rates)) == 1

    underpowered = observed_reps < required_reps
    if saturated:
        # Both facts, when both hold. "SATURATED" alone reads as a full matrix
        # that happened to be flat, which is a stronger claim than one
        # repetition can support.
        verdict = ("PARTIAL_AND_PRIMARY_METRIC_SATURATED" if underpowered
                   else "PRIMARY_METRIC_SATURATED_ON_THIS_CASE_SET")
        interpretation = (
            f"Observed {observed_reps} repetitions per arm against a preregistered "
            f"{required_reps}. " if underpowered else ""
        ) + (
            "Every cell returned the same primary value, so no treatment signal could have "
            "appeared regardless of the arms. This bounds the case set, not the arms, and may "
            "not be reported as evidence that the treatments do not differ. The preregistration "
            "names this outcome in advance: adding repetitions cannot unsaturate a metric, only "
            "harder cases can, and a case set changed after seeing results is not a case set."
        )
    elif qualifies:
        verdict = "QUALIFYING_MATRIX"
        interpretation = "Preregistered contrasts may be reported against this matrix."
    else:
        verdict = "PARTIAL"
        interpretation = (
            f"Observed {observed_reps} repetitions per arm against a preregistered "
            f"{required_reps}. Mechanism is demonstrated -- every arm executed on the exact "
            "subject and the evaluator ran -- and no preregistered contrast may be reported "
            "from it."
        )

    return {
        "schema": "uplift-matrix-summary/v1",
        "preregistration_id": prereg["preregistration_id"],
        "primary_metric": prereg["metrics"]["primary"],
        "required_arms": REQUIRED_ARMS,
        "preregistered_contrasts": [f"{left} vs {right}" for left, right in CONTRASTS],
        "contrasts_reported": [],
        "_why_no_contrasts": (
            "Contrasts are reported only from a qualifying, unsaturated matrix. Emitting them "
            "from a PARTIAL run is how a pilot becomes a finding."
        ),
        "hosts": per_host,
        "gaps": {
            "observed_repetitions_per_arm": observed_reps,
            "required_repetitions_per_arm": required_reps,
            "missing_arms": missing_arms,
            "host_error_arms": host_errors,
            "hosts_contributing": sorted(receipts),
        },
        "primary_metric_saturated": saturated,
        "qualifies_for_219": qualifies and not saturated,
        "verdict": verdict,
        "interpretation": interpretation,
        "non_claims": prereg["non_claims"],
    }


def selftest() -> int:
    """The two refusals, on synthetic receipts. No host, no spend."""
    if not PREREGISTRATION.is_file():
        print(f"SELFTEST RED: preregistration absent at {PREREGISTRATION}", file=sys.stderr)
        return 1
    prereg = load(PREREGISTRATION)
    required = prereg["power"]["repetitions_per_arm_per_host"]

    def receipt(reps: int, rates: list[float], errors: list[str] | None = None) -> dict[str, Any]:
        return {"trial_matrix": {
            "runtime": "X", "repetitions_per_arm": reps, "host_error_arms": errors or [],
            "bindings": {"model": "m", "host_version": "v", "policy": {}},
            "cells": [
                {"arm": arm, "cell_state": "SCORED",
                 "score": {"false_pass_rate": rates[index % len(rates)], "task_success": True,
                           "cited_paths": 5},
                 "observation": {"duration_ms": 1000, "cost_observed": False}}
                for rep in range(reps) for index, arm in enumerate(REQUIRED_ARMS)
            ]}}

    partial = summarise({"h1": receipt(1, [0.1, 0.2, 0.3, 0.4, 0.5]),
                         "h2": receipt(1, [0.1, 0.2, 0.3, 0.4, 0.5])}, prereg)
    if partial["verdict"] != "PARTIAL" or partial["qualifies_for_219"]:
        print(f"SELFTEST RED: an underpowered matrix was not PARTIAL: {partial['verdict']}",
              file=sys.stderr)
        return 1

    saturated = summarise({"h1": receipt(required, [0.0]), "h2": receipt(required, [0.0])}, prereg)
    if saturated["verdict"] != "PRIMARY_METRIC_SATURATED_ON_THIS_CASE_SET":
        print(f"SELFTEST RED: a saturated matrix reported {saturated['verdict']}", file=sys.stderr)
        return 1
    if saturated["qualifies_for_219"]:
        print("SELFTEST RED: a saturated matrix qualified", file=sys.stderr)
        return 1

    # Underpowered and saturated is the run this repository actually has. The
    # verdict must carry both, or a one-repetition result reads as a full flat
    # matrix.
    both = summarise({"h1": receipt(1, [0.0]), "h2": receipt(1, [0.0])}, prereg)
    if both["verdict"] != "PARTIAL_AND_PRIMARY_METRIC_SATURATED":
        print(f"SELFTEST RED: underpowered+saturated reported {both['verdict']}", file=sys.stderr)
        return 1
    if str(required) not in both["interpretation"]:
        print("SELFTEST RED: the underpowered fact vanished from the saturated message",
              file=sys.stderr)
        return 1

    good = summarise({"h1": receipt(required, [0.1, 0.2, 0.3, 0.4, 0.5]),
                      "h2": receipt(required, [0.1, 0.2, 0.3, 0.4, 0.5])}, prereg)
    if good["verdict"] != "QUALIFYING_MATRIX" or not good["qualifies_for_219"]:
        print(f"SELFTEST RED: a full unsaturated matrix reported {good['verdict']}", file=sys.stderr)
        return 1

    one_host = summarise({"h1": receipt(required, [0.1, 0.2, 0.3, 0.4, 0.5])}, prereg)
    if one_host["qualifies_for_219"]:
        print("SELFTEST RED: a single-host matrix qualified", file=sys.stderr)
        return 1

    outaged = summarise({"h1": receipt(required, [0.1, 0.2, 0.3, 0.4, 0.5], errors=["C_FULL_SKILL"]),
                         "h2": receipt(required, [0.1, 0.2, 0.3, 0.4, 0.5])}, prereg)
    if outaged["qualifies_for_219"]:
        print("SELFTEST RED: a matrix with a host-error arm qualified", file=sys.stderr)
        return 1

    if good["contrasts_reported"] or saturated["contrasts_reported"]:
        print("SELFTEST RED: contrasts were emitted by the aggregator", file=sys.stderr)
        return 1

    print(
        f"SELFTEST GREEN: an underpowered matrix is PARTIAL; a saturated one is reported as a "
        f"case-set finding and never as a null; a single host and a host-error arm each fail to "
        f"qualify; only {required} repetitions on two clean hosts qualify; no contrast is ever "
        "emitted by the aggregator"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--receipt", action="append", default=[], metavar="HOST=PATH")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.selftest:
        return selftest()
    if not args.receipt or not args.output:
        print("UPLIFT-INVALID: --receipt HOST=PATH (repeatable) and --output are required",
              file=sys.stderr)
        return INVALID
    if not PREREGISTRATION.is_file():
        print(f"UPLIFT-INVALID absent-preregistration: {PREREGISTRATION}", file=sys.stderr)
        return INVALID

    receipts: dict[str, dict[str, Any]] = {}
    for item in args.receipt:
        host, _, path = item.partition("=")
        candidate = Path(path)
        if not candidate.is_file():
            print(f"UPLIFT-INVALID absent-receipt: {candidate}", file=sys.stderr)
            return INVALID
        receipts[host] = load(candidate)

    summary = summarise(receipts, load(PREREGISTRATION))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"UPLIFT {summary['verdict']} qualifies={summary['qualifies_for_219']} "
          f"hosts={summary['gaps']['hosts_contributing']} "
          f"reps={summary['gaps']['observed_repetitions_per_arm']}/"
          f"{summary['gaps']['required_repetitions_per_arm']} "
          f"saturated={summary['primary_metric_saturated']}")
    print(f"  {summary['interpretation']}")
    return 0 if summary["qualifies_for_219"] else REFUSED


if __name__ == "__main__":
    raise SystemExit(main())
