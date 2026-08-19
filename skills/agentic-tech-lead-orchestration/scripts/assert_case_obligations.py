#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

TASK_SCHEMA = "agentic-tech-lead/task-contract/v1"
CASE_SCHEMA = "spatial-loop-case-graph/v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REPO_ROOT = Path(__file__).resolve().parents[3]
MAX_BYTES = 4 * 1024 * 1024


class UsageError(Exception):
    pass


@dataclass(frozen=True)
class Failure:
    assertion: str
    detail: str


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise UsageError(f"contract not found: {path}")
    if path.stat().st_size > MAX_BYTES:
        raise UsageError("contract exceeds 4 MiB")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageError(f"invalid contract JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise UsageError("contract root must be an object")
    return value


def _canonical_digest(value: dict[str, Any]) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _safe_repo_path(value: Any) -> bool:
    if not isinstance(value, str) or not value or "\\" in value or value.startswith("/"):
        return False
    pure = PurePosixPath(value)
    return ".." not in pure.parts and pure.parts[:1] != (".git",)


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _read_case_graph(ref: str, failures: list[Failure]) -> tuple[dict[str, Any] | None, str | None]:
    path = (REPO_ROOT / ref).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError:
        failures.append(Failure("CASE_GRAPH_BINDING", "case_graph_ref escapes repository"))
        return None, None
    if not path.is_file():
        failures.append(Failure("CASE_GRAPH_ABSENT", f"case_graph_ref does not exist: {ref}"))
        return None, None
    try:
        raw = path.read_bytes()
    except OSError as exc:
        failures.append(Failure("CASE_GRAPH_READBACK", f"cannot read case graph: {exc}"))
        return None, None
    if len(raw) > MAX_BYTES:
        failures.append(Failure("CASE_GRAPH_READBACK", "case graph exceeds 4 MiB"))
        return None, None
    actual_digest = hashlib.sha256(raw).hexdigest()
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        failures.append(Failure("CASE_GRAPH_READBACK", f"case graph is invalid JSON: {exc}"))
        return None, actual_digest
    if not isinstance(doc, dict) or doc.get("schema") != CASE_SCHEMA:
        failures.append(Failure("CASE_GRAPH_READBACK", f"case graph must use {CASE_SCHEMA}"))
        return None, actual_digest
    return doc, actual_digest


def _required_cases_from_graph(doc: dict[str, Any], failures: list[Failure]) -> set[str]:
    raw_cases = doc.get("cases")
    if not isinstance(raw_cases, list):
        failures.append(Failure("CASE_GRAPH_READBACK", "case graph cases must be an array"))
        return set()
    required: set[str] = set()
    for index, item in enumerate(raw_cases):
        if not isinstance(item, dict):
            failures.append(Failure("CASE_GRAPH_READBACK", f"case graph cases[{index}] must be an object"))
            continue
        if item.get("classification") != "REQUIRED_CASE":
            continue
        case_id = item.get("id")
        if not isinstance(case_id, str) or not case_id:
            failures.append(Failure("CASE_GRAPH_READBACK", f"required case at index {index} lacks id"))
            continue
        if case_id in required:
            failures.append(Failure("CASE_GRAPH_READBACK", f"duplicate required case id in graph: {case_id}"))
        required.add(case_id)
    return required


def validate(contract: dict[str, Any]) -> list[Failure]:
    failures: list[Failure] = []

    def fail(assertion: str, detail: str) -> None:
        failures.append(Failure(assertion, detail))

    if contract.get("schema") != TASK_SCHEMA:
        fail("SCHEMA_ID", f"expected {TASK_SCHEMA}")

    if "case_obligations" not in contract:
        return failures

    sidecar = contract.get("case_obligations")
    if not isinstance(sidecar, dict):
        fail("CASE_OBLIGATIONS_SHAPE", "case_obligations must be an object when present")
        return failures

    ref = sidecar.get("case_graph_ref")
    ref_valid = _safe_repo_path(ref)
    if not ref_valid:
        fail("CASE_GRAPH_BINDING", "case_graph_ref must be a safe repo-relative path")

    digest = sidecar.get("case_graph_sha256")
    digest_valid = isinstance(digest, str) and bool(SHA256_RE.fullmatch(digest))
    if not digest_valid:
        fail("CASE_GRAPH_BINDING", "case_graph_sha256 must be immutable lowercase sha256")

    graph: dict[str, Any] | None = None
    actual_digest: str | None = None
    if ref_valid:
        graph, actual_digest = _read_case_graph(str(ref), failures)
    if digest_valid and actual_digest is not None and digest != actual_digest:
        fail("CASE_GRAPH_DIGEST_MISMATCH", f"case_graph_sha256 is stale for {ref}")

    branches = _list(contract.get("branches"))
    branch_names = {
        item.get("name")
        for item in branches
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }

    required_cases = _list(sidecar.get("required_case_ids"))
    denominator_valid = (
        bool(required_cases)
        and all(isinstance(case_id, str) and bool(case_id) for case_id in required_cases)
        and len(set(required_cases)) == len(required_cases)
    )
    if not denominator_valid:
        fail("CASE_DENOMINATOR", "required_case_ids must be non-empty, string, and unique")

    if graph is not None and denominator_valid:
        graph_required = _required_cases_from_graph(graph, failures)
        packet_required = set(required_cases)
        missing_from_packet = sorted(graph_required - packet_required)
        invented_by_packet = sorted(packet_required - graph_required)
        if missing_from_packet:
            fail(
                "CASE_DENOMINATOR_SHRINK",
                f"task packet omits required graph cases: {', '.join(missing_from_packet)}",
            )
        if invented_by_packet:
            fail(
                "CASE_DENOMINATOR_DRIFT",
                f"task packet invents required cases absent from graph: {', '.join(invented_by_packet)}",
            )

    convergence = sidecar.get("convergence_owner")
    if not isinstance(convergence, str) or convergence not in branch_names:
        fail("CASE_CONVERGENCE_OWNER", "convergence_owner must name a declared branch")

    owners = _list(sidecar.get("branch_case_owners"))
    if not owners:
        fail("CASE_OWNER", "branch_case_owners must be non-empty")

    seen_owner_branches: set[str] = set()
    observed_cases: list[str] = []
    for index, owner in enumerate(owners):
        if not isinstance(owner, dict):
            fail("CASE_OWNER", f"branch_case_owners[{index}] must be an object")
            continue
        branch = owner.get("branch")
        case_ids = _list(owner.get("case_ids"))
        if not isinstance(branch, str) or branch not in branch_names:
            fail("CASE_OWNER", f"case owner {branch!r} is not a declared branch")
        elif branch in seen_owner_branches:
            fail("CASE_OWNER", f"branch {branch!r} appears more than once")
        else:
            seen_owner_branches.add(branch)

        if (
            not case_ids
            or any(not isinstance(case_id, str) or not case_id for case_id in case_ids)
            or len(set(case_ids)) != len(case_ids)
        ):
            fail("CASE_OWNER", f"branch {branch!r} must own non-empty unique case_ids")
        observed_cases.extend(
            case_id for case_id in case_ids if isinstance(case_id, str) and case_id
        )

    duplicate_cases = sorted(
        {case_id for case_id in observed_cases if observed_cases.count(case_id) > 1}
    )
    if duplicate_cases:
        fail(
            "CASE_DUPLICATE_OWNER",
            f"required cases have multiple owners: {', '.join(duplicate_cases)}",
        )

    required_set = {case_id for case_id in required_cases if isinstance(case_id, str)}
    observed_set = set(observed_cases)
    missing = sorted(required_set - observed_set)
    extra = sorted(observed_set - required_set)
    if missing:
        fail("CASE_UNOWNED", f"required cases have no owner: {', '.join(missing)}")
    if extra:
        fail(
            "CASE_UNKNOWN_OWNER",
            f"ownership map contains cases outside denominator: {', '.join(extra)}",
        )

    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True)
    parser.add_argument("--receipt")
    try:
        args = parser.parse_args(argv)
        contract_path = Path(args.contract).resolve()
        contract = _read_json(contract_path)
        failures = validate(contract)
        sidecar_present = "case_obligations" in contract
        receipt = {
            "schema": "agentic-tech-lead/case-obligation-receipt/v1",
            "contract": os.fspath(contract_path),
            "contract_sha256": _canonical_digest(contract),
            "task_id": contract.get("task_id"),
            "case_obligations_state": "BOUND" if sidecar_present else "NOT_APPLICABLE_OR_LEGACY",
            "verdict": "PASS" if not failures else "FAIL",
            "failures": [failure.__dict__ for failure in failures],
            "claims_not_proven": [
                "semantic completeness of the referenced ICPG beyond its owning checker",
                "Worker execution",
                "global case evidence closure",
                "Git ancestry, publication, merge, release, promotion, or Human Admit",
            ],
        }
        if args.receipt:
            receipt_path = Path(args.receipt).resolve()
            if not receipt_path.parent.is_dir():
                raise UsageError(f"receipt parent not found: {receipt_path.parent}")
            receipt_path.write_text(
                json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        print(
            "CASE-OBLIGATIONS-GREEN"
            if not failures and sidecar_present
            else "CASE-OBLIGATIONS-NOT-APPLICABLE"
            if not failures
            else "CASE-OBLIGATIONS-RED"
        )
        return 0 if not failures else 2
    except UsageError as exc:
        print(str(exc), file=sys.stderr)
        return 64
    except SystemExit as exc:
        return 64 if int(exc.code or 0) != 0 else 0
    except Exception as exc:
        print(f"internal error: {exc}", file=sys.stderr)
        return 70


if __name__ == "__main__":
    raise SystemExit(main())
