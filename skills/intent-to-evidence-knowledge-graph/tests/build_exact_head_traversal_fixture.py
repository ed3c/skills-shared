#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def read(name: str) -> dict:
    value = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{name} must contain an object")
    return value


def timestamp(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SystemExit(f"observed-at must be RFC3339/date-time: {exc}") from None
    if parsed.tzinfo is None:
        raise SystemExit("observed-at must include timezone")
    return value


def rewrite_external(artifact: dict, repository: str, sha: str) -> None:
    kind = artifact["artifact_type"]
    external = artifact["external_identity"]
    if kind == "PR":
        artifact["external_identity"] = f"pr:{repository}#{external.rsplit('#', 1)[1]}"
    elif kind == "ISSUE":
        artifact["external_identity"] = f"issue:{repository}#{external.rsplit('#', 1)[1]}"
    elif kind in {"FILE", "README", "AGENTS", "SKILL", "SCHEMA", "SCRIPT", "TEST"}:
        artifact["external_identity"] = f"path:{repository}@{sha}:{external.split(':', 2)[2]}"
    elif kind == "RECEIPT":
        artifact["external_identity"] = f"receipt:{repository}#{external.rsplit('#', 1)[1]}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    if len(args.sha) != 40 or any(character not in "0123456789abcdef" for character in args.sha):
        raise SystemExit("sha must be 40 lowercase hex chars")
    observed_at = timestamp(args.observed_at)

    plan = read("traversal-plan.json")
    trace = read("traversal-trace-graph.json")
    binding = read("valid-traversal-binding.json")

    plan["subject"] = {"repository": args.repository, "ref": args.ref, "sha": args.sha}
    trace["subject"] = {"repository": args.repository, "ref": args.ref, "sha": args.sha}
    binding["subject"] = {"repository": args.repository, "ref": args.ref, "sha": args.sha}

    for item in binding["case_bindings"]:
        item["issue"] = f"issue:{args.repository}#{item['issue'].rsplit('#', 1)[1]}"
    for node in binding["stack_nodes"]:
        node["issue"] = f"issue:{args.repository}#{node['issue'].rsplit('#', 1)[1]}"

    for artifact in trace["artifacts"]:
        rewrite_external(artifact, args.repository, args.sha)
        observed = artifact["observed_subject"]
        observed["repository"] = args.repository
        observed["ref_or_identity"] = args.ref
        observed["sha"] = args.sha
        observed["observed_at"] = observed_at

    authority = {
        "schema_version": "authority-snapshot/v1",
        "observed_at": observed_at,
        "artifacts": {},
    }
    for artifact in trace["artifacts"]:
        if not artifact["mutable"]:
            continue
        authority["artifacts"][artifact["artifact_id"]] = {
            "external_identity": artifact["external_identity"],
            "sha": args.sha,
            "state": "open",
            "observed_at": observed_at,
        }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for name, value in [
        ("traversal-plan.json", plan),
        ("traversal-trace-graph.json", trace),
        ("traversal-binding.json", binding),
        ("traversal-authority.json", authority),
    ]:
        (args.out_dir / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
