#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def _validate_timestamp(value: str) -> str:
    candidate = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise SystemExit(f"observed-at must be RFC3339/date-time: {exc}") from None
    if parsed.tzinfo is None:
        raise SystemExit("observed-at must include an explicit timezone")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--pr-number", required=True, type=int)
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--graph-out", required=True, type=Path)
    parser.add_argument("--authority-out", required=True, type=Path)
    args = parser.parse_args()

    if len(args.sha) != 40 or any(character not in "0123456789abcdef" for character in args.sha):
        raise SystemExit("sha must be 40 lowercase hex chars")
    observed_at = _validate_timestamp(args.observed_at)

    graph_digest = "sha256:" + "a" * 64
    intent = {
        "schema_version": "intent-projection/v1",
        "intent_id": "intent:knowledge-graph-v7.2",
        "desired_outcome": "bind semantic knowledge to exact ICPG, delivery, and evidence subjects",
        "non_goals": ["duplicate ICPG case truth"],
        "invariants": ["retrieval relevance does not grant execution authority"],
        "acceptance_criteria": ["projection remains bidirectionally traceable"],
        "authority_boundary": "Human/repository authority remains external",
        "icpg": {
            "graph_digest": graph_digest,
            "case_ids": ["CASE-KG-001"],
        },
    }

    def artifact(
        artifact_id: str,
        artifact_type: str,
        authority_class: str,
        external_identity: str,
        mutable: bool,
        evidence_ceiling: str,
    ) -> dict:
        return {
            "schema_version": "artifact-projection/v1",
            "artifact_id": artifact_id,
            "artifact_type": artifact_type,
            "authority_class": authority_class,
            "external_identity": external_identity,
            "mutable": mutable,
            "observed_subject": {
                "repository": args.repository,
                "ref_or_identity": args.ref,
                "sha": args.sha,
                "observed_at": observed_at,
                "freshness_policy": "REFRESH_BEFORE_DECISION" if mutable else "IMMUTABLE",
            },
            "evidence_ceiling": evidence_ceiling,
            "trace": {
                "intent_id": intent["intent_id"],
                "icpg_graph_digest": graph_digest,
                "case_ids": ["CASE-KG-001"],
            },
        }

    pr = artifact(
        "pr-current",
        "PR",
        "DELIVERY_ARTIFACT",
        f"pr:{args.repository}#{args.pr_number}",
        True,
        "L2",
    )
    readme = artifact(
        "readme-current",
        "README",
        "NAVIGATION",
        f"path:{args.repository}@{args.sha}:skills/intent-to-evidence-knowledge-graph/README.md",
        False,
        "L2",
    )
    receipt = artifact(
        "receipt-current",
        "RECEIPT",
        "EVIDENCE_RECEIPT",
        f"receipt:{args.repository}#exact-head",
        False,
        "L2",
    )

    graph = {
        "schema_version": "intent-to-evidence-trace-graph/v1",
        "subject": {
            "repository": args.repository,
            "ref": args.ref,
            "sha": args.sha,
        },
        "intents": [intent],
        "artifacts": [pr, readme, receipt],
        "edges": [
            {
                "from": intent["intent_id"],
                "relation": "TRACKED_BY",
                "to": pr["artifact_id"],
                "utility": "IMPLEMENTATION",
            },
            {
                "from": pr["artifact_id"],
                "relation": "TOUCHES",
                "to": readme["artifact_id"],
                "utility": "IMPLEMENTATION",
            },
            {
                "from": readme["artifact_id"],
                "relation": "VERIFIED_BY",
                "to": receipt["artifact_id"],
                "utility": "EVIDENCE",
            },
            {
                "from": pr["artifact_id"],
                "relation": "VERIFIED_BY",
                "to": receipt["artifact_id"],
                "utility": "EVIDENCE",
            },
        ],
        "required_traversals": ["WHY_TO_PROOF", "IMPLEMENTATION_TO_WHY"],
    }
    authority = {
        "schema_version": "authority-snapshot/v1",
        "observed_at": observed_at,
        "artifacts": {
            pr["artifact_id"]: {
                "external_identity": pr["external_identity"],
                "sha": args.sha,
                "state": "open",
                "observed_at": observed_at,
            }
        },
    }

    args.graph_out.parent.mkdir(parents=True, exist_ok=True)
    args.authority_out.parent.mkdir(parents=True, exist_ok=True)
    args.graph_out.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.authority_out.write_text(json.dumps(authority, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
