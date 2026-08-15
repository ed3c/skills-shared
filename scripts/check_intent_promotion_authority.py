#!/usr/bin/env python3
"""External authority readback for intent promotion.

#138 closed the substitutions a receipt can make about itself. One remained,
and it is the one a receipt cannot close alone:

    the receipt says an evaluator receipt exists, with this digest
    the receipt embeds forge readback fields
    the receipt labels an approval Human and names a readback source
    -> and the semantic checker believed all of it

Those fields are caller-supplied. A caller who can write `receipt_digest` can
write any value into it. So this layer requires the referenced bytes to be
present and to hash to what the receipt claimed — the digest stops being a
label and starts being a check.

It also *executes* the committed schemas. They were parsed with `json.tool`,
which proves they are JSON, not that anything validates against them:
`additionalProperties: false`, conditional branches and required nested fields
were never deciding gates. A schema nobody runs is the same shape of defect as
a test nobody runs.

What stays outside: whether the forge really said this, whether the merge
really happened, and whether a human really approved. Those are external
authority. This checker proves the bundle is internally consistent with bytes
that exist, which is a smaller claim, stated as such.

Exits: 0 admitted, 2 refused, 64 unusable input, 70 checker failure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

BUNDLE_SCHEMA = "intent-promotion-authority-bundle/v1"


class Refused(Exception):
    """The bundle was read and does not hold together."""


class Unusable(Exception):
    """The input could not be read at all."""


def digest_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def read_bytes(path: Path, label: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        raise Unusable(f"{label}: unreadable {path}: {error}") from error


def read_json(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    raw = read_bytes(path, label)
    try:
        body = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise Unusable(f"{label}: unparseable {path}: {error}") from error
    if not isinstance(body, dict):
        raise Unusable(f"{label}: {path} root must be an object")
    return body, raw


def load_validator(schema: dict[str, Any]) -> Any:
    """A pinned Draft 2020-12 validator, or a checker failure.

    Falling back to "skip validation" when the library is absent would make the
    strictest gate here the one most likely to be silently off.
    """
    try:
        from jsonschema import Draft202012Validator
    except ImportError as error:  # pragma: no cover - environment guard
        raise RuntimeError(
            "jsonschema is required: the committed schemas must be executed as "
            "deciding gates, not merely parsed"
        ) from error
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_against(schema: dict[str, Any], body: dict[str, Any], label: str) -> None:
    errors = sorted(load_validator(schema).iter_errors(body), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        location = "/".join(str(part) for part in first.path) or "<root>"
        raise Refused(f"{label} fails its schema at {location}: {first.message}")


def resolve(root: Path, relative: str, label: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as error:
        raise Refused(f"{label} path {relative!r} escapes the bundle root") from error
    return candidate


def check_artifact(root: Path, declared: dict[str, Any], label: str) -> dict[str, Any]:
    path = resolve(root, declared["path"], label)
    raw = read_bytes(path, label)
    actual = digest_bytes(raw)
    if actual != declared["artifact_digest"]:
        raise Refused(
            f"{label} digest {declared['artifact_digest']} does not match the "
            f"bytes at {declared['path']} ({actual}); a digest a caller writes "
            f"is a label until something hashes the file"
        )
    try:
        body = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise Refused(f"{label} is not valid JSON: {error}") from error
    if not isinstance(body, dict):
        raise Refused(f"{label} root must be an object")
    return body


def check_evaluator_evidence(
    root: Path, receipt: dict[str, Any], evidence: list[dict[str, Any]]
) -> set[str]:
    declared_runs = receipt.get("evaluator_receipts") or []
    by_ref: dict[str, dict[str, Any]] = {}
    for item in evidence:
        ref = item["receipt_ref"]
        if ref in by_ref:
            raise Refused(
                f"evaluator evidence for {ref!r} is supplied twice; a duplicated "
                f"artifact can stand in for a missing one"
            )
        by_ref[ref] = item

    consumed: set[str] = set()
    for run in declared_runs:
        ref = run["receipt_ref"]
        supplied = by_ref.get(ref)
        if supplied is None:
            raise Refused(
                f"evaluator {run['evaluator_id']!r} declares receipt_ref {ref!r} "
                f"with no evidence artifact; the reference was never read"
            )
        consumed.add(ref)
        label = f"evaluator evidence {ref!r}"
        body = check_artifact(root, supplied, label)
        if supplied["artifact_digest"] != run["receipt_digest"]:
            raise Refused(
                f"{label} digest differs from the digest the promotion receipt "
                f"declared for it"
            )
        for field, receipt_field in (
            ("evaluator_id", "evaluator_id"),
            ("evaluator_version", "evaluator_version"),
            ("evaluator_artifact_digest", "evaluator_artifact_digest"),
            ("subject_commit_sha", "subject_commit_sha"),
            ("subject_tree_sha", "subject_tree_sha"),
            ("status", "status"),
            ("output_digest", "output_digest"),
            ("execution_origin", "execution_origin"),
        ):
            if body.get(field) != run.get(receipt_field):
                raise Refused(
                    f"{label} reports {field}={body.get(field)!r} but the "
                    f"promotion receipt claims {run.get(receipt_field)!r}"
                )
    return consumed


def check_forge_evidence(
    root: Path, receipt: dict[str, Any], supplied: dict[str, Any] | None
) -> bool:
    merge = receipt.get("merge_subject")
    if merge is None:
        if supplied is not None:
            raise Refused("forge evidence supplied for a receipt with no merge subject")
        return False
    if supplied is None:
        raise Refused(
            "merge subject declares a forge readback with no evidence artifact; "
            "the readback fields were taken on the receipt's word"
        )
    label = "forge readback evidence"
    body = check_artifact(root, supplied, label)
    readback = merge["forge_readback"]
    if supplied["artifact_digest"] != readback["readback_digest"]:
        raise Refused(f"{label} digest differs from the readback digest the receipt declared")
    for field, expected in (
        ("source", readback["source"]),
        ("observed_at_commit_sha", readback["observed_at_commit_sha"]),
        ("repository", merge["repository"]),
        ("merge_commit_sha", merge["merge_commit_sha"]),
        ("merge_tree_sha", merge["merge_tree_sha"]),
        ("candidate_head_sha", merge["candidate_head_sha"]),
        ("candidate_tree_sha", merge["candidate_tree_sha"]),
    ):
        if body.get(field) != expected:
            raise Refused(
                f"{label} reports {field}={body.get(field)!r} but the receipt "
                f"claims {expected!r}"
            )
    return True


def check_approval_evidence(
    root: Path, receipt: dict[str, Any], supplied: dict[str, Any] | None
) -> bool:
    approval = receipt.get("approval")
    if approval is None:
        if supplied is not None:
            raise Refused("approval evidence supplied for a receipt with no approval")
        return False
    if supplied is None:
        raise Refused(
            "approval declares a readback source with no evidence artifact; the "
            "approval was taken on the receipt's word"
        )
    label = "approval readback evidence"
    body = check_artifact(root, supplied, label)
    if supplied["artifact_digest"] != approval["approval_receipt_digest"]:
        raise Refused(f"{label} digest differs from the digest the receipt declared")
    for field, expected in (
        ("approver_identity", approval["approver_identity"]),
        ("approver_kind", approval["approver_kind"]),
        ("review_ref", approval["review_ref"]),
        ("readback_source", approval["readback_source"]),
        ("approval_subject_commit_sha", approval["approval_subject_commit_sha"]),
    ):
        if body.get(field) != expected:
            raise Refused(
                f"{label} reports {field}={body.get(field)!r} but the receipt "
                f"claims {expected!r}"
            )
    if body.get("generated_by_agent") is not False:
        raise Refused(
            f"{label} declares it was generated by an agent; the receipt's own "
            f"claim to the contrary does not survive its evidence disagreeing"
        )
    if body.get("subject_tree_sha") != receipt["subject"]["tree_sha"]:
        raise Refused(f"{label} approves a different tree than the promoted subject")
    return True


def evaluate(bundle_path: Path) -> dict[str, Any]:
    root = bundle_path.parent.resolve()
    bundle, _ = read_json(bundle_path, "authority bundle")

    schema_ref = bundle.get("bundle_schema")
    if not isinstance(schema_ref, dict):
        raise Refused("bundle_schema is absent")
    bundle_schema = check_artifact(root, schema_ref, "bundle schema")
    validate_against(bundle_schema, bundle, "authority bundle")

    if bundle.get("schema_version") != BUNDLE_SCHEMA:
        raise Refused(f"schema_version is not {BUNDLE_SCHEMA}")

    contract_schema = check_artifact(root, bundle["contract_schema"], "contract schema")
    receipt_schema = check_artifact(root, bundle["receipt_schema"], "receipt schema")
    contract = check_artifact(root, bundle["contract"], "contract")
    receipt = check_artifact(root, bundle["receipt"], "receipt")

    # The committed schemas now decide, rather than merely being parseable.
    validate_against(contract_schema, contract, "contract")
    validate_against(receipt_schema, receipt, "receipt")

    if receipt.get("contract_digest") != bundle["contract"]["artifact_digest"]:
        raise Refused(
            "receipt contract_digest does not match the contract bytes in this bundle"
        )

    ledger_ref = bundle.get("ledger")
    declared_ledger_path = (contract.get("supersession_policy") or {}).get("ledger_ref")
    if ledger_ref is not None:
        ledger_schema = check_artifact(root, bundle["ledger_schema"], "ledger schema")
        ledger_path = resolve(root, ledger_ref["path"], "ledger")
        raw = read_bytes(ledger_path, "ledger")
        if digest_bytes(raw) != ledger_ref["artifact_digest"]:
            raise Refused("ledger digest does not match the ledger bytes")
        try:
            ledger = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise Refused(f"ledger is not valid JSON: {error}") from error
        validate_against(ledger_schema, {"entries": ledger}, "ledger")
        if declared_ledger_path and not str(declared_ledger_path).endswith(
            Path(ledger_ref["path"]).name
        ):
            raise Refused(
                f"bundle ledger {ledger_ref['path']!r} is not the ledger the "
                f"contract declares ({declared_ledger_path!r})"
            )
    elif receipt.get("supersedes") is not None:
        raise Refused("receipt supersedes a predecessor but the bundle supplies no ledger")

    evidence = bundle.get("evidence") or {}
    consumed = check_evaluator_evidence(root, receipt, evidence.get("evaluator_receipts") or [])
    forge_used = check_forge_evidence(root, receipt, evidence.get("forge_readback"))
    approval_used = check_approval_evidence(root, receipt, evidence.get("approval_readback"))

    # An artifact nobody referenced is either a mistake or a spare part left
    # where a reviewer will read it as coverage.
    supplied_refs = {item["receipt_ref"] for item in evidence.get("evaluator_receipts") or []}
    extra = sorted(supplied_refs - consumed)
    if extra:
        raise Refused(
            f"unreferenced evaluator evidence artifact(s): {', '.join(extra)}"
        )

    return {
        "schema_version": "intent-promotion-authority-receipt/v1",
        "bundle_digest": digest_bytes(bundle_path.read_bytes()),
        "receipt_id": receipt.get("receipt_id"),
        "intent_id": receipt.get("intent_id"),
        "to_state": receipt.get("to_state"),
        "schemas_executed": ["contract", "receipt"] + (["ledger"] if ledger_ref else []),
        "evaluator_evidence_read": sorted(consumed),
        "forge_readback_read": forge_used,
        "approval_readback_read": approval_used,
        "external_authenticity": "NOT_EXERCISED",
        "actual_merge_occurrence": "NOT_EXERCISED",
        "actual_human_identity": "EXTERNAL_AUTHORITY",
        "status": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        from intent_promotion_authority_selftest import run_selftest
        return run_selftest()

    if args.bundle is None:
        parser.error("--bundle or --selftest is required")

    try:
        result = evaluate(args.bundle)
    except Unusable as error:
        print(f"FATAL authority input: {error}", file=sys.stderr)
        return 64
    except Refused as error:
        print(f"AUTHORITY RED: {error}", file=sys.stderr)
        return 2
    except RuntimeError as error:
        print(f"CHECKER RED: {error}", file=sys.stderr)
        return 70

    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.receipt:
        args.receipt.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
