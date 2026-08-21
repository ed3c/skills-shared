#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path} must contain an object")
    return value


def _validate_timestamp(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SystemExit(f"observed-at must be RFC3339/date-time: {exc}") from None
    if parsed.tzinfo is None:
        raise SystemExit("observed-at must include timezone")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--binding-out", required=True, type=Path)
    parser.add_argument("--trace-out", required=True, type=Path)
    args = parser.parse_args()

    if len(args.sha) != 40 or any(character not in "0123456789abcdef" for character in args.sha):
        raise SystemExit("sha must be 40 lowercase hex chars")
    observed_at = _validate_timestamp(args.observed_at)

    binding = _read(FIXTURES / "valid-case-delivery-binding.json")
    trace = _read(FIXTURES / "delivery-trace-graph.json")

    binding["subject"] = {"repository": args.repository, "ref": args.ref, "sha": args.sha}
    for item in binding["case_bindings"]:
        number = item["issue"].rsplit("#", 1)[1]
        item["issue"] = f"issue:{args.repository}#{number}"
    for node in binding["stack_nodes"]:
        number = node["issue"].rsplit("#", 1)[1]
        node["issue"] = f"issue:{args.repository}#{number}"

    trace["subject"] = {"repository": args.repository, "ref": args.ref, "sha": args.sha}
    for artifact in trace["artifacts"]:
        observed = artifact["observed_subject"]
        observed["repository"] = args.repository
        observed["ref_or_identity"] = args.ref
        observed["sha"] = args.sha
        observed["observed_at"] = observed_at

        external = artifact["external_identity"]
        artifact_type = artifact["artifact_type"]
        if artifact_type == "PR":
            number = external.rsplit("#", 1)[1]
            artifact["external_identity"] = f"pr:{args.repository}#{number}"
        elif artifact_type in {"FILE", "AGENTS", "README", "SKILL", "SCHEMA", "SCRIPT", "TEST"}:
            path = external.split(":", 2)[2]
            artifact["external_identity"] = f"path:{args.repository}@{args.sha}:{path}"

    args.binding_out.parent.mkdir(parents=True, exist_ok=True)
    args.trace_out.parent.mkdir(parents=True, exist_ok=True)
    args.binding_out.write_text(json.dumps(binding, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.trace_out.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
