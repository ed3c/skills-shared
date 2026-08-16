#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "evals" / "migrations" / "issue-255" / "bundle-reconciliation.json"
ALLOWED = {"discard_duplicate", "route_to_consumer", "preserve_reference"}
EXPECTED_BUNDLE = "d4f431ba2843d98d4bd4e9bb4ce770c1facc705263ea698897afda5fbb96c035"
EXPECTED_BASE = "fc8daf1a301dc293941e76cd5220664e47193880"


class Refused(Exception):
    pass


def validate(data: dict) -> None:
    if data.get("schema") != "staged-bundle-reconciliation/v1":
        raise Refused("schema")
    if data.get("issue") != 255:
        raise Refused("issue")
    if data.get("source_bundle", {}).get("sha256") != EXPECTED_BUNDLE:
        raise Refused("bundle digest")
    if data.get("repository_base", {}).get("commit") != EXPECTED_BASE:
        raise Refused("base commit")

    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        raise Refused("entries")
    paths = [entry.get("path") for entry in entries]
    if len(paths) != len(set(paths)):
        raise Refused("duplicate path")
    if any(entry.get("decision") not in ALLOWED for entry in entries):
        raise Refused("unadmitted decision")

    for entry in entries:
        path = entry.get("path", "")
        decision = entry.get("decision")
        if path.startswith("skills-shared/parallel-tech-lead-loop/") and decision != "discard_duplicate":
            raise Refused("standalone skill import admitted")
        if path.startswith("bettor-arena/") and decision != "route_to_consumer":
            raise Refused("consumer bytes imported into shared core")

    summary = data.get("summary", {})
    for decision in ALLOWED:
        expected = sum(entry["decision"] == decision for entry in entries)
        if summary.get(decision) != expected:
            raise Refused(f"summary {decision}")
    if summary.get("integrate") != 0 or summary.get("rewrite") != 0:
        raise Refused("unexpected import")

    expected_policy = "ZIP is migration input only and is not committed or required at runtime."
    if data.get("artifact_policy") != expected_policy:
        raise Refused("artifact policy")


def selftest(data: dict) -> None:
    mutants = []

    mutant = copy.deepcopy(data)
    mutant["source_bundle"]["sha256"] = "0" * 64
    mutants.append(mutant)

    mutant = copy.deepcopy(data)
    next(entry for entry in mutant["entries"] if entry["path"].startswith("skills-shared/parallel-tech-lead-loop/"))["decision"] = "integrate"
    mutants.append(mutant)

    mutant = copy.deepcopy(data)
    mutant["entries"].append(copy.deepcopy(mutant["entries"][0]))
    mutants.append(mutant)

    mutant = copy.deepcopy(data)
    next(entry for entry in mutant["entries"] if entry["path"].startswith("bettor-arena/"))["decision"] = "discard_duplicate"
    mutants.append(mutant)

    mutant = copy.deepcopy(data)
    mutant["summary"]["discard_duplicate"] += 1
    mutants.append(mutant)

    killed = 0
    for mutant in mutants:
        try:
            validate(mutant)
        except Refused:
            killed += 1
    if killed != len(mutants):
        raise Refused(f"mutation controls {killed}/{len(mutants)}")
    print(f"bundle reconciliation controls: PASS ({killed}/{len(mutants)} mutations refused)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        validate(data)
        if args.selftest:
            selftest(data)
        else:
            print("bundle reconciliation: PASS")
        return 0
    except (OSError, json.JSONDecodeError) as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return 64
    except Refused as exc:
        print(f"reconciliation refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
