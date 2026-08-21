#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import assert_case_obligations as case_gate
import assert_task_contract_base as base

SCHEMA = base.SCHEMA
Failure = base.Failure
UsageError = base.UsageError


def validate(contract: dict) -> list:
    failures = list(base.validate(contract))
    failures.extend(case_gate.validate(contract))
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--contract", required=True)
    parser.add_argument("--receipt", required=True)
    try:
        args = parser.parse_args(argv)
        contract_path = Path(args.contract).resolve()
        receipt_path = Path(args.receipt).resolve()
        if not receipt_path.parent.is_dir():
            raise UsageError(f"receipt parent not found: {receipt_path.parent}")
        contract = base._read_json(contract_path)
        failures = validate(contract)
        implemented = [
            "required-fields",
            "immutable-subject",
            "safe-paths",
            "path-lease",
            "interface-locks",
            "dependency-policy",
            "provider-roles",
            "provider-exact-subject",
            "no-code-graph-rag",
            "no-double-graph",
            "branch-topology",
            "acceptance-oracles",
            "repair-worker-budgets",
            "automation-evidence-ceiling",
            "git-town-admission",
            "semantic-conflict-boundary",
            "human-admit",
        ]
        if "case_obligations" in contract:
            implemented.append("case-obligation-denominator-and-ownership")
        receipt = {
            "schema": "agentic-tech-lead/task-contract-receipt/v1",
            "contract": os.fspath(contract_path),
            "contract_sha256": base._canonical_digest(contract),
            "task_id": contract.get("task_id"),
            "mode": contract.get("mode"),
            "verdict": "PASS" if not failures else "FAIL",
            "assertions": {
                "implemented": implemented,
                "failures": [
                    {"assertion": failure.assertion, "detail": failure.detail}
                    for failure in failures
                ],
            },
            "claims_not_proven": [
                "provider installation or live health",
                "SCIP/Tree-sitter index execution",
                "truth or freshness of a referenced ICPG beyond its bound task packet",
                "Worker or Serena execution",
                "global case evidence closure",
                "Git Worktree/Git Town/forge state",
                "remote publication, mergeability, promotion, rollback, or Human Admit",
            ],
        }
        receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
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
