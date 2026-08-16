#!/usr/bin/env python3
"""Merge the sliced #228 matrix into one result and report separability.

Exit codes:
  0   every expected slice was present and merged
  2   slices are missing; the merged result records which, and stays a partial
  64  the input directory is absent or holds no slice

The question five repetitions exist to answer is not "which arm scored higher" --
one repetition already produces that number. It is whether the difference between
arms is larger than the spread within an arm. This computes both and says which,
so a difference inside the noise cannot be read as an effect.
"""
from __future__ import annotations

import argparse
import collections
import json
import statistics
import sys
from pathlib import Path
from typing import Any

INVALID = 64
PARTIAL = 2

EXPECTED_SLICES = 6
EXPECTED_CELLS = 90


def load_slices(root: Path) -> list[dict[str, Any]]:
    found = []
    for path in sorted(root.rglob("*result.json")):
        if path.name not in {"pilot-result.json", "matrix-result.json"}:
            continue
        found.append(json.loads(path.read_text(encoding="utf-8")))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if not args.input.is_dir():
        print(f"MATRIX-MERGE-INVALID absent-input: {args.input}", file=sys.stderr)
        return INVALID
    slices = load_slices(args.input)
    if not slices:
        print(f"MATRIX-MERGE-INVALID no-slices-found: {args.input}", file=sys.stderr)
        return INVALID

    cells: list[dict[str, Any]] = []
    for payload in slices:
        cells.extend(payload.get("cells", []))
    scored = [c for c in cells if c.get("metrics")]

    per = collections.defaultdict(lambda: collections.defaultdict(list))
    for cell in scored:
        m = cell["metrics"]
        key = (cell["host_family"], cell["arm"])
        per[key]["found"].append(m["material_defects_found"])
        per[key]["trigger"].append(int(m["trigger_correct"]))
        per[key]["false_pass"].append(m["false_pass_count"])
        if m["cost_observed"]:
            per[key]["cost"].append(m["cost_usd"])

    aggregate = {}
    for key in sorted(per):
        v = per[key]
        n = len(v["found"])
        aggregate["|".join(key)] = {
            "n": n,
            "found_mean": round(statistics.mean(v["found"]), 4),
            "found_sd": round(statistics.pstdev(v["found"]), 4) if n > 1 else 0.0,
            "trigger_mean": round(statistics.mean(v["trigger"]), 4),
            "trigger_sd": round(statistics.pstdev(v["trigger"]), 4) if n > 1 else 0.0,
            "false_pass_mean": round(statistics.mean(v["false_pass"]), 4),
            "cost_observed_cells": len(v["cost"]),
            "cost_total_usd": round(sum(v["cost"]), 6) if v["cost"] else None,
        }

    separability = []
    for host in sorted({k[0] for k in per}):
        arms = {k[1]: per[k] for k in per if k[0] == host}
        for metric in ("found", "trigger"):
            means = {a: statistics.mean(v[metric]) for a, v in arms.items()}
            sds = {a: statistics.pstdev(v[metric]) if len(v[metric]) > 1 else 0.0
                   for a, v in arms.items()}
            spread = max(means.values()) - min(means.values()) if means else 0.0
            noise = max(sds.values()) if sds else 0.0
            separability.append({
                "host": host,
                "metric": metric,
                "between_arm_spread": round(spread, 4),
                "largest_within_arm_sd": round(noise, 4),
                "separable": bool(spread > noise and spread > 0),
                "reading": ("arm difference exceeds within-arm spread"
                            if spread > noise and spread > 0
                            else "arm difference is within run-to-run noise"),
            })

    complete = len(slices) == EXPECTED_SLICES and len(cells) == EXPECTED_CELLS
    report = {
        "schema": "rca-matrix-result/v1",
        "status": "MATRIX" if complete else "PARTIAL_MATRIX",
        "slices_found": len(slices),
        "slices_expected": EXPECTED_SLICES,
        "cell_count": len(cells),
        "cells_expected": EXPECTED_CELLS,
        "scored_cells": len(scored),
        "cells": cells,
        "aggregate": aggregate,
        "separability": separability,
        "non_claims": [
            "a difference inside within-arm spread is not an effect",
            "cost is observed on one host only and is excluded from scoring",
            "no production, cross-repository, or promotion claim follows",
        ],
    }
    out = args.output or (args.input / "matrix-merged.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"{'host':<13} {'arm':<26} {'n':>3} {'found':>14} {'trigger':>14} {'cost':>9}")
    for key, row in aggregate.items():
        host, arm = key.split("|")
        cost = f"${row['cost_total_usd']:.2f}" if row["cost_total_usd"] is not None else "n/a"
        print(f"{host:<13} {arm:<26} {row['n']:>3} "
              f"{row['found_mean']:>6.2f}±{row['found_sd']:<6.2f} "
              f"{row['trigger_mean']:>6.2f}±{row['trigger_sd']:<6.2f} {cost:>9}")
    print("\nseparability")
    for item in separability:
        print(f"  {item['host']:<13} {item['metric']:<9} "
              f"spread={item['between_arm_spread']:.2f} sd={item['largest_within_arm_sd']:.2f} "
              f"-> {item['reading']}")
    print(f"\nstatus={report['status']} cells={len(cells)}/{EXPECTED_CELLS}")
    print(f"wrote {out}")
    return 0 if complete else PARTIAL


if __name__ == "__main__":
    raise SystemExit(main())
