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
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class UsageError(Exception):
    pass


@dataclass(frozen=True)
class Failure:
    assertion: str
    detail: str


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise UsageError(f"contract not found: {path}")
    if path.stat().st_size > 4 * 1024 * 1024:
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
    return ".." not in PurePosixPath(value).parts


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


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
    if not _safe_repo_path(ref):
        fail("CASE_GRAPH_BINDING", "case_graph_ref must be a safe repo-relative path")

    digest = sidecar.get("case_graph_sha256")
    if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
        fail("CASE_GRAPH_BINDING", "case_graph_sha256 must be immutable lowercase sha256")

    branches = _list(contract.get("branches"))
    branch_names = {
        item.get("name")
        for item in branches
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }

    required_cases = _list(sidecar.get("required_case_ids"))
    if (
        not required_cases
        or any(not isinstance(case_id, str) or not case_id for case_id in required_cases)
        or len(set(required_cases)) != len(required_cases)
    ):
        fail("CASE_DENOMINATOR", "required_case_ids must be non-empty, string, and unique")

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
                "truth or freshness of the referenced case-graph bytes",
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
