#!/usr/bin/env python3
"""Render/check a deterministic index of separated ecosystem and capability scorecards."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def build_index(root: Path) -> dict:
    directory = root / "evals" / "scorecards"
    entries = []
    for path in sorted(directory.glob("*.json")) if directory.is_dir() else []:
        if path.name == "index.json":
            continue
        value = load_object(path)
        if value.get("schema_version") != "skill-scorecard/v1":
            raise ValueError(f"{path.relative_to(root)}: unsupported scorecard schema")
        if "overall_score" in value:
            raise ValueError(f"{path.relative_to(root)}: overall_score is forbidden")
        ecosystem = value.get("ecosystem_quality")
        capability = value.get("verified_capability")
        if not isinstance(ecosystem, dict) or not isinstance(capability, dict):
            raise ValueError(f"{path.relative_to(root)}: scorecards must keep ecosystem and capability separate")
        gap = capability.get("generalization_gap")
        variance = capability.get("cross_harness_variance")
        if not isinstance(gap, (int, float)) or not isinstance(variance, (int, float)):
            raise ValueError(f"{path.relative_to(root)}: capability scorecard must expose gap and variance")
        entries.append({
            "skill": value.get("skill"),
            "skill_sha": value.get("skill_sha"),
            "path": path.relative_to(root).as_posix(),
            "ecosystem_quality": ecosystem,
            "verified_capability": capability,
            "generalization_gap": gap,
            "cross_harness_variance": variance,
        })
    entries.sort(key=lambda item: (str(item["skill"]), str(item["skill_sha"])))
    return {"schema_version": "skill-scorecard-index/v1", "scorecards": entries}


def canonical(value: dict) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        value = build_index(root)
        output = args.output or (root / "evals" / "scorecards" / "index.json")
        rendered = canonical(value)
        if args.check:
            if not output.is_file() or output.read_text(encoding="utf-8") != rendered:
                raise ValueError(f"scorecard index is stale: {output}")
            print(f"PASS scorecard index: {len(value['scorecards'])} scorecard(s)")
            return 0
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        print(f"WROTE {output}: {len(value['scorecards'])} scorecard(s)")
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
