#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator, FormatChecker
except Exception as exc:
    print(json.dumps({
        "status": "INPUT_ERROR",
        "exit_code": 64,
        "errors": [{"code": "JSONSCHEMA_UNAVAILABLE", "subject": "runtime", "message": str(exc)}],
    }, sort_keys=True))
    raise SystemExit(64)

EXIT_PASS = 0
EXIT_BLOCK = 2
EXIT_INPUT = 64

EVIDENCE_LEVELS = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5}
DOC_TYPES = {"README", "AGENTS", "SKILL"}
PROOF_AUTHORITY_CLASSES = {"VERIFIER", "TEST", "EVIDENCE_RECEIPT", "HUMAN_AUTHORITY"}

AUTHORITY_COMPAT = {
    "README": {"NAVIGATION"},
    "AGENTS": {"PROCEDURE"},
    "SKILL": {"PORTABLE_METHOD"},
    "SCHEMA": {"CONTRACT"},
    "TEST": {"TEST"},
    "RECEIPT": {"EVIDENCE_RECEIPT"},
    "HUMAN_ADMIT": {"HUMAN_AUTHORITY"},
    "PR": {"DELIVERY_ARTIFACT"},
    "WORKFLOW": {"EXECUTION_ARTIFACT"},
    "COMMIT": {"EXECUTION_ARTIFACT", "DELIVERY_ARTIFACT"},
    "SCRIPT": {"IMPLEMENTATION", "VERIFIER"},
    "FILE": {"IMPLEMENTATION", "NAVIGATION", "PROCEDURE", "PORTABLE_METHOD", "CONTRACT"},
    "ISSUE": {"EXECUTION_ARTIFACT", "DELIVERY_ARTIFACT"},
    "TASK": {"EXECUTION_ARTIFACT"},
    "BRANCH": {"EXECUTION_ARTIFACT", "DELIVERY_ARTIFACT"},
}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"missing file: {path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from None
    if not isinstance(value, dict):
        raise ValueError(f"expected object in {path}")
    return value


def _schema_errors(instance: Any, schema: dict[str, Any], label: str) -> list[dict[str, str]]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[dict[str, str]] = []
    for err in sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path)):
        path = ".".join(str(p) for p in err.absolute_path) or "$"
        errors.append({
            "code": "SCHEMA_INVALID",
            "subject": f"{label}:{path}",
            "message": err.message,
        })
    return errors


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _id_ok(artifact: dict[str, Any]) -> tuple[bool, str]:
    artifact_type = artifact["artifact_type"]
    external = artifact["external_identity"]
    observed = artifact["observed_subject"]
    repository = observed["repository"]
    sha = observed.get("sha")
    ref = observed["ref_or_identity"]

    if artifact_type == "PR":
        prefix = f"pr:{repository}#"
        return external.startswith(prefix) and external[len(prefix):].isdigit(), "pr:<repo>#<number>"
    if artifact_type == "ISSUE":
        prefix = f"issue:{repository}#"
        return external.startswith(prefix) and external[len(prefix):].isdigit(), "issue:<repo>#<number>"
    if artifact_type == "COMMIT":
        return bool(sha) and external == f"git:{repository}@{sha}", "git:<repo>@<sha>"
    if artifact_type == "BRANCH":
        return external == f"branch:{repository}@{ref}", "branch:<repo>@<ref>"
    if artifact_type in {"FILE", "README", "AGENTS", "SKILL", "SCHEMA", "SCRIPT", "TEST"}:
        prefix = f"path:{repository}@{sha or ref}:"
        return external.startswith(prefix) and len(external) > len(prefix), "path:<repo>@<sha-or-ref>:<path>"
    if artifact_type == "WORKFLOW":
        return external.startswith(f"workflow:{repository}#"), "workflow:<repo>#<identity>"
    if artifact_type == "RECEIPT":
        return external.startswith(f"receipt:{repository}#"), "receipt:<repo>#<identity>"
    if artifact_type == "HUMAN_ADMIT":
        return external.startswith(f"admit:{repository}#"), "admit:<repo>#<identity>"
    if artifact_type == "TASK":
        return external.startswith(f"task:{repository}#"), "task:<repo>#<identity>"
    return bool(external), "non-empty"


def _validate_trace_shell(graph: dict[str, Any], trace_schema: dict[str, Any]) -> list[dict[str, str]]:
    shell = json.loads(json.dumps(trace_schema))
    shell["properties"]["intents"]["items"] = {"type": "object"}
    shell["properties"]["artifacts"]["items"] = {"type": "object"}
    return _schema_errors(graph, shell, "trace")


def _semantic_errors(
    graph: dict[str, Any], authority: dict[str, Any] | None, expected_sha: str | None
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    intents = graph.get("intents", [])
    artifacts = graph.get("artifacts", [])
    edges = graph.get("edges", [])

    if expected_sha and graph.get("subject", {}).get("sha") != expected_sha:
        errors.append({
            "code": "EXACT_SUBJECT_MISMATCH",
            "subject": "trace.subject.sha",
            "message": f"expected {expected_sha}, observed {graph.get('subject', {}).get('sha')}",
        })

    intent_by_id: dict[str, dict[str, Any]] = {}
    for intent in intents:
        intent_id = intent.get("intent_id")
        if intent_id in intent_by_id:
            errors.append({
                "code": "DUPLICATE_INTENT_ID",
                "subject": str(intent_id),
                "message": "intent_id must be unique",
            })
        intent_by_id[intent_id] = intent

    artifact_by_id: dict[str, dict[str, Any]] = {}
    for artifact in artifacts:
        artifact_id = artifact.get("artifact_id")
        if artifact_id in artifact_by_id:
            errors.append({
                "code": "DUPLICATE_ARTIFACT_ID",
                "subject": str(artifact_id),
                "message": "artifact_id must be unique",
            })
        artifact_by_id[artifact_id] = artifact

        expected_classes = AUTHORITY_COMPAT.get(artifact.get("artifact_type"))
        if expected_classes and artifact.get("authority_class") not in expected_classes:
            errors.append({
                "code": "AUTHORITY_CLASS_MISMATCH",
                "subject": str(artifact_id),
                "message": f"{artifact.get('artifact_type')} requires one of {sorted(expected_classes)}",
            })

        identity_ok, expected_format = _id_ok(artifact)
        if not identity_ok:
            errors.append({
                "code": "FABRICATED_ARTIFACT_IDENTITY",
                "subject": str(artifact_id),
                "message": f"external_identity must match {expected_format} and observed subject",
            })

        trace = artifact.get("trace", {})
        intent_id = trace.get("intent_id")
        intent = intent_by_id.get(intent_id)
        if not intent:
            errors.append({
                "code": "ORPHAN_IMPLEMENTATION",
                "subject": str(artifact_id),
                "message": f"trace.intent_id {intent_id!r} is not present",
            })
        else:
            digest = intent["icpg"]["graph_digest"]
            if trace.get("icpg_graph_digest") != digest:
                errors.append({
                    "code": "ICPG_DIGEST_MISMATCH",
                    "subject": str(artifact_id),
                    "message": "artifact ICPG digest differs from linked Intent projection",
                })
            allowed_cases = set(intent["icpg"]["case_ids"])
            projected_cases = set(trace.get("case_ids", []))
            if not projected_cases.issubset(allowed_cases):
                errors.append({
                    "code": "UNKNOWN_ICPG_CASE",
                    "subject": str(artifact_id),
                    "message": f"artifact references cases outside Intent projection: {sorted(projected_cases - allowed_cases)}",
                })

        mutable = artifact.get("mutable")
        policy = artifact.get("observed_subject", {}).get("freshness_policy")
        if mutable and policy == "IMMUTABLE":
            errors.append({
                "code": "FRESHNESS_POLICY_INVALID",
                "subject": str(artifact_id),
                "message": "mutable artifacts cannot use IMMUTABLE freshness policy",
            })
        if (not mutable) and policy and policy != "IMMUTABLE":
            errors.append({
                "code": "FRESHNESS_POLICY_INVALID",
                "subject": str(artifact_id),
                "message": "immutable projection with freshness_policy must use IMMUTABLE",
            })
        if artifact.get("artifact_type") == "COMMIT" and mutable:
            errors.append({
                "code": "IMMUTABLE_IDENTITY_VIOLATION",
                "subject": str(artifact_id),
                "message": "COMMIT projections must be immutable",
            })

    node_ids = set(intent_by_id) | set(artifact_by_id)
    outgoing_verified: dict[str, list[str]] = {}
    for index, edge in enumerate(edges):
        source, target = edge.get("from"), edge.get("to")
        if source not in node_ids:
            errors.append({
                "code": "EDGE_ORPHAN_SOURCE",
                "subject": f"edges[{index}]",
                "message": f"unknown from node {source!r}",
            })
        if target not in node_ids:
            errors.append({
                "code": "EDGE_ORPHAN_TARGET",
                "subject": f"edges[{index}]",
                "message": f"unknown to node {target!r}",
            })
        if edge.get("relation") == "TRUE_CHILD":
            consumed = edge.get("consumed_artifact")
            if consumed not in artifact_by_id:
                errors.append({
                    "code": "FALSE_GIT_ANCESTRY",
                    "subject": f"edges[{index}]",
                    "message": "TRUE_CHILD consumed_artifact must reference a projected artifact",
                })
        if edge.get("relation") == "VERIFIED_BY":
            outgoing_verified.setdefault(source, []).append(target)

    # Prose may describe higher evidence, but it cannot self-promote above linked proof authority.
    for artifact in artifacts:
        if artifact.get("artifact_type") not in DOC_TYPES:
            continue
        level = EVIDENCE_LEVELS[artifact["evidence_ceiling"]]
        if level <= 1:
            continue
        verifier_ids = outgoing_verified.get(artifact["artifact_id"], [])
        proof_levels: list[int] = []
        for verifier_id in verifier_ids:
            verifier = artifact_by_id.get(verifier_id)
            if verifier and verifier.get("authority_class") in PROOF_AUTHORITY_CLASSES:
                proof_levels.append(EVIDENCE_LEVELS[verifier["evidence_ceiling"]])
        if not proof_levels or max(proof_levels) < level:
            errors.append({
                "code": "PROSE_OVER_RECEIPT",
                "subject": artifact["artifact_id"],
                "message": f"{artifact['artifact_type']} ceiling {artifact['evidence_ceiling']} exceeds linked proof authority",
            })

    # L4/L5 claims must be backed by proof at the same layer; L5 additionally needs Human Admit.
    for artifact in artifacts:
        level = EVIDENCE_LEVELS[artifact["evidence_ceiling"]]
        if level < 4:
            continue
        verifier_ids = outgoing_verified.get(artifact["artifact_id"], [])
        proof = [artifact_by_id.get(verifier_id) for verifier_id in verifier_ids]
        proof = [item for item in proof if item]
        if not any(
            item["authority_class"] in PROOF_AUTHORITY_CLASSES
            and EVIDENCE_LEVELS[item["evidence_ceiling"]] >= level
            for item in proof
        ):
            errors.append({
                "code": "EVIDENCE_LAUNDERING",
                "subject": artifact["artifact_id"],
                "message": f"{artifact['evidence_ceiling']} requires linked proof at the same or higher layer",
            })
        if level == 5 and not any(
            item["artifact_type"] == "HUMAN_ADMIT" and item["evidence_ceiling"] == "L5"
            for item in proof
        ):
            errors.append({
                "code": "HUMAN_ADMIT_MISSING",
                "subject": artifact["artifact_id"],
                "message": "L5 requires a linked HUMAN_ADMIT projection",
            })

    if authority is not None:
        if authority.get("schema_version") != "authority-snapshot/v1":
            errors.append({
                "code": "AUTHORITY_SNAPSHOT_INVALID",
                "subject": "authority_snapshot",
                "message": "schema_version must be authority-snapshot/v1",
            })
        snapshot = authority.get("artifacts", {})
        if not isinstance(snapshot, dict):
            errors.append({
                "code": "AUTHORITY_SNAPSHOT_INVALID",
                "subject": "authority_snapshot.artifacts",
                "message": "must be an object",
            })
            snapshot = {}
        for artifact in artifacts:
            if not artifact.get("mutable"):
                continue
            artifact_id = artifact["artifact_id"]
            current = snapshot.get(artifact_id)
            if not isinstance(current, dict):
                errors.append({
                    "code": "STALE_MUTABLE_SUBJECT",
                    "subject": artifact_id,
                    "message": "mutable artifact has no refreshed authority snapshot",
                })
                continue
            if current.get("external_identity") != artifact.get("external_identity"):
                errors.append({
                    "code": "FABRICATED_ARTIFACT_IDENTITY",
                    "subject": artifact_id,
                    "message": "authority snapshot external identity differs from projection",
                })
            observed_sha = artifact.get("observed_subject", {}).get("sha")
            current_sha = current.get("sha")
            if current_sha and observed_sha != current_sha:
                errors.append({
                    "code": "STALE_MUTABLE_SUBJECT",
                    "subject": artifact_id,
                    "message": f"projected sha {observed_sha!r} != authority sha {current_sha!r}",
                })
    else:
        for artifact in artifacts:
            if artifact.get("mutable"):
                errors.append({
                    "code": "AUTHORITY_SNAPSHOT_REQUIRED",
                    "subject": artifact["artifact_id"],
                    "message": "mutable artifact requires --authority-snapshot",
                })

    return errors


def check(
    graph: dict[str, Any],
    reference_dir: Path,
    authority: dict[str, Any] | None,
    expected_sha: str | None,
) -> dict[str, Any]:
    errors: list[dict[str, str]] = []

    # Emit the decision-relevant reason before generic additionalProperties schema failure.
    for intent in graph.get("intents", []):
        copied = sorted({"case_denominator", "cases", "case_truth", "semantic_axes"}.intersection(intent.keys()))
        if copied:
            errors.append({
                "code": "DUPLICATE_ICPG_AUTHORITY",
                "subject": str(intent.get("intent_id", "<missing>")),
                "message": f"forbidden copied ICPG fields: {copied}",
            })

    try:
        intent_schema = _read_json(reference_dir / "intent-projection.schema.json")
        artifact_schema = _read_json(reference_dir / "artifact-projection.schema.json")
        trace_schema = _read_json(reference_dir / "trace-graph.schema.json")
    except ValueError as exc:
        return {
            "status": "INPUT_ERROR",
            "exit_code": EXIT_INPUT,
            "errors": [{"code": "SCHEMA_LOAD_ERROR", "subject": str(reference_dir), "message": str(exc)}],
        }

    errors.extend(_validate_trace_shell(graph, trace_schema))
    for index, intent in enumerate(graph.get("intents", [])):
        errors.extend(_schema_errors(intent, intent_schema, f"intents[{index}]"))
    for index, artifact in enumerate(graph.get("artifacts", [])):
        errors.extend(_schema_errors(artifact, artifact_schema, f"artifacts[{index}]"))

    if not any(error["code"] == "SCHEMA_INVALID" for error in errors):
        errors.extend(_semantic_errors(graph, authority, expected_sha))

    errors = sorted(errors, key=lambda item: (item["code"], item["subject"], item["message"]))
    status = "PASS" if not errors else "BLOCK"
    return {
        "status": status,
        "exit_code": EXIT_PASS if not errors else EXIT_BLOCK,
        "subject": graph.get("subject"),
        "graph_digest": _sha256_json(graph),
        "authority_snapshot_digest": _sha256_json(authority) if authority is not None else None,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Intent-to-Evidence projection graph contracts.")
    parser.add_argument("graph", type=Path)
    parser.add_argument("--authority-snapshot", type=Path)
    parser.add_argument("--reference-dir", type=Path)
    parser.add_argument("--expected-sha")
    parser.add_argument("--receipt-out", type=Path)
    args = parser.parse_args(argv)

    try:
        graph = _read_json(args.graph)
        authority = _read_json(args.authority_snapshot) if args.authority_snapshot else None
    except ValueError as exc:
        report = {
            "status": "INPUT_ERROR",
            "exit_code": EXIT_INPUT,
            "errors": [{"code": "INPUT_JSON_ERROR", "subject": str(args.graph), "message": str(exc)}],
        }
        print(json.dumps(report, sort_keys=True))
        return EXIT_INPUT

    reference_dir = args.reference_dir or Path(__file__).resolve().parents[1] / "references"
    report = check(graph, reference_dir, authority, args.expected_sha)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.receipt_out:
        args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
        args.receipt_out.write_text(rendered + "\n", encoding="utf-8")
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
