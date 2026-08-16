#!/usr/bin/env python3
"""Report which metrics can separate arms, and which are saturated.

Exit codes:
  0   the analysis ran; separability is reported per metric
  2   a metric declared primary is saturated, so the result cannot support a claim
  64  the result file is absent or unusable

Why this exists. The slice-1 record stopped a six-slice matrix after one slice
on the grounds that "these metrics are saturated ... so the remaining five
slices cannot change that conclusion". That was true of `task_success`,
`trigger_correct` and `material_defects_found`, each pinned at 1.00 with zero
variance. It was not true of `false_pass_count`, which varied both within and
between arms -- and was never analysed, because the saturated metrics were read
as if they spoke for all of them.

A count is also the wrong scale when its denominator moves: false-pass
opportunities ranged 19.6 to 23.8 across arms, so a raw count mixes "made more
mistakes" with "was offered more chances to". This reports the rate.

The distinction the checker enforces is the one that was collapsed: a metric
with zero within-arm variance is saturated and carries no information about the
treatment, whatever its mean; a metric with variance is a measurement, and a
null on it has to be earned rather than inherited from its neighbours.
"""
from __future__ import annotations

import argparse
import json
import statistics as stats
import sys
from pathlib import Path
from typing import Any

INVALID = 64
SATURATED_PRIMARY = 2

# Rates, not counts: each pairs a numerator with the denominator that bounds it.
RATES = {
    "false_pass_rate": ("false_pass_count", "false_pass_opportunities"),
    "defect_recall": ("material_defects_found", "material_defects_total"),
}


def cell_value(metrics: dict[str, Any], name: str) -> float | None:
    if name in RATES:
        numerator, denominator = RATES[name]
        top, bottom = metrics.get(numerator), metrics.get(denominator)
        if isinstance(top, (int, float)) and isinstance(bottom, (int, float)) and bottom > 0:
            return top / bottom
        return None
    value = metrics.get(name)
    # bool is an int subclass; admitted deliberately, since a binary metric
    # being saturated is exactly what this needs to be able to report.
    if isinstance(value, (int, float)):
        return float(value)
    return None


def analyze(cells: list[dict[str, Any]], metric: str) -> dict[str, Any]:
    by_arm: dict[str, list[float]] = {}
    for cell in cells:
        value = cell_value(cell.get("metrics") or {}, metric)
        if value is not None:
            by_arm.setdefault(str(cell.get("arm")), []).append(value)

    arms = {
        arm: {
            "n": len(values),
            "mean": round(stats.mean(values), 4),
            "sd": round(stats.pstdev(values), 4),
        }
        for arm, values in sorted(by_arm.items())
    }
    if not arms:
        return {"metric": metric, "measured": False, "arms": {}}

    means = [a["mean"] for a in arms.values()]
    within = [sd for a in arms.values() for sd in [a["sd"]]]
    spread = max(means) - min(means)
    pooled = stats.mean(within)
    saturated = all(a["sd"] == 0.0 for a in arms.values())
    return {
        "metric": metric,
        "measured": True,
        "arms": arms,
        "between_arm_spread": round(spread, 4),
        "mean_within_arm_sd": round(pooled, 4),
        # The ratio is descriptive, not a test: with four cells per arm it
        # cannot license a significance claim, and is not reported as one.
        "separability_ratio": round(spread / pooled, 2) if pooled > 0 else None,
        "saturated": saturated,
        "ranking": [arm for arm, _ in sorted(arms.items(), key=lambda kv: kv[1]["mean"])],
    }


def selftest() -> int:
    """Plant a saturated primary and require the red, then require the green back.

    A separability checker that only ever reports green on real data is
    indistinguishable from one that cannot go red -- which is the failure this
    whole analysis exists to correct.
    """
    def cell(arm: str, count: int, opportunities: int) -> dict[str, Any]:
        return {"arm": arm, "metrics": {"false_pass_count": count,
                                        "false_pass_opportunities": opportunities,
                                        "task_success": True}}

    # Saturated: every arm identical, zero within-arm variance.
    flat = [cell(a, 5, 20) for a in ("x", "y") for _ in range(3)]
    report = analyze(flat, "false_pass_rate")
    if not report["saturated"]:
        print("SELFTEST RED: a zero-variance metric was not called saturated", file=sys.stderr)
        return 2

    # Varying: the same checker must recover the signal rather than always red.
    varied = [cell("x", n, 20) for n in (4, 6, 5)] + [cell("y", n, 20) for n in (9, 11, 10)]
    report = analyze(varied, "false_pass_rate")
    if report["saturated"] or report["ranking"] != ["x", "y"]:
        print(f"SELFTEST RED: a varying metric was misread: {report}", file=sys.stderr)
        return 2

    # A moving denominator must change the verdict; that is the whole point of
    # rating rather than counting. Equal counts, unequal opportunities.
    denominators = [cell("x", 6, 12) for _ in range(3)] + [cell("y", 6, 24) for _ in range(3)]
    report = analyze(denominators, "false_pass_rate")
    if report["ranking"] != ["y", "x"]:
        print("SELFTEST RED: equal counts over unequal opportunities ranked as equal",
              file=sys.stderr)
        return 2

    print("SELFTEST GREEN: saturation is caught, real variance is recovered, "
          "and a moving denominator changes the ranking")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--primary", default="false_pass_rate",
                        help="metric the conclusion rests on; saturation here exits 2")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    if args.result is None:
        print("SEPARATION-INVALID --result is required", file=sys.stderr)
        return INVALID

    try:
        document = json.loads(args.result.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"SEPARATION-INVALID unreadable-result: {error}", file=sys.stderr)
        return INVALID
    cells = document.get("cells")
    if not isinstance(cells, list) or not cells:
        print("SEPARATION-INVALID result carries no cells", file=sys.stderr)
        return INVALID

    names = sorted({k for c in cells for k in (c.get("metrics") or {})})
    candidates = [n for n in names if n not in {c for pair in RATES.values() for c in pair}]
    reports = [analyze(cells, name) for name in [*RATES, *candidates]]
    measured = [r for r in reports if r["measured"]]

    saturated = [r["metric"] for r in measured if r["saturated"]]
    informative = [r for r in measured if not r["saturated"]]

    print(f"metrics measured: {len(measured)}  saturated: {len(saturated)}  "
          f"informative: {len(informative)}")
    print(f"\nSATURATED (zero within-arm variance -- carry no treatment signal):")
    for name in saturated:
        print(f"  {name}")
    print(f"\nINFORMATIVE (ranked by separability):")
    for report in sorted(informative, key=lambda r: -(r["separability_ratio"] or 0)):
        print(f"  {report['metric']:<26} spread={report['between_arm_spread']:<8} "
              f"within-sd={report['mean_within_arm_sd']:<8} ratio={report['separability_ratio']}")
        for arm, stat in report["arms"].items():
            print(f"      {arm:<28} n={stat['n']} mean={stat['mean']} sd={stat['sd']}")

    primary = next((r for r in measured if r["metric"] == args.primary), None)
    if args.output:
        args.output.write_text(json.dumps({
            "schema": "arm-separation-analysis/v1",
            "source": str(args.result),
            "primary_metric": args.primary,
            "reports": reports,
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if primary is None:
        print(f"\nSEPARATION-INVALID primary metric not measured: {args.primary}",
              file=sys.stderr)
        return INVALID
    if primary["saturated"]:
        print(f"\nSEPARATION-SATURATED {args.primary} has zero within-arm variance; "
              "a null on it is an artefact of the case set, not a treatment result",
              file=sys.stderr)
        return SATURATED_PRIMARY

    print(f"\nSEPARATION-GREEN primary metric {args.primary} varies within arms "
          f"(ratio {primary['separability_ratio']}); ranking {' < '.join(primary['ranking'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
