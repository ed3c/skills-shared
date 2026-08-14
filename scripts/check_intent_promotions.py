#!/usr/bin/env python3
"""Validate intent-promotion contracts and exact transition receipts.

Exit codes:
  0   declared subject passed
  2   readable subject violated contract or policy
  64  usage, unreadable input, or malformed JSON
  70  evaluator implementation failure
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from intent_promotion.common import (  # noqa: E402
    CliUsage,
    InputFailure,
    PolicyRefusal,
    StableArgumentParser,
    load_object,
)
from intent_promotion.contract import validate_contract  # noqa: E402
from intent_promotion.receipt import validate_receipt  # noqa: E402
from intent_promotion.selftest import selftest  # noqa: E402


def build_parser() -> StableArgumentParser:
    parser = StableArgumentParser()
    sub = parser.add_subparsers(
        dest="command", required=True, parser_class=StableArgumentParser
    )

    contract = sub.add_parser("contract")
    contract.add_argument("path", type=Path)
    contract.add_argument("--repo-root", type=Path, default=Path.cwd())
    contract.add_argument("--verify-bindings", action="store_true")

    receipt = sub.add_parser("receipt")
    receipt.add_argument("path", type=Path)
    receipt.add_argument("--contract", type=Path, required=True)
    receipt.add_argument("--repo-root", type=Path, default=Path.cwd())
    receipt.add_argument("--verify-bindings", action="store_true")

    sub.add_parser("selftest")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        if args.command == "selftest":
            return selftest(Path(__file__))

        contract, contract_raw = load_object(
            args.path if args.command == "contract" else args.contract
        )
        validate_contract(
            contract,
            repository_root=args.repo_root,
            verify_external_bindings=args.verify_bindings,
        )
        if args.command == "receipt":
            receipt, _ = load_object(args.path)
            validate_receipt(receipt, contract, contract_raw)
    except CliUsage as error:
        print(f"INTENT PROMOTION USAGE: {error}", file=sys.stderr)
        return 64
    except InputFailure as error:
        print(f"INTENT PROMOTION INPUT: {error}", file=sys.stderr)
        return 64
    except PolicyRefusal as error:
        print(f"INTENT PROMOTION RED: {error}", file=sys.stderr)
        return 2
    except Exception as error:  # pragma: no cover
        print(
            f"INTENT PROMOTION EVALUATOR: {type(error).__name__}: {error}",
            file=sys.stderr,
        )
        return 70

    print(f"INTENT PROMOTION GREEN: {args.command} verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
