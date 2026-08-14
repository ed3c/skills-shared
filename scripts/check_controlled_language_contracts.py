#!/usr/bin/env python3
"""Validate controlled-language contracts. Exit 0 PASS, 2 FAIL, 64 input, 70 checker."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from controlled_language.common import load, result  # noqa: E402
from controlled_language.contracts import (  # noqa: E402
    validate_request,
    validate_standard_pack,
    validate_termbase_entry,
    validate_violation,
)
from controlled_language.receipt import validate_receipt  # noqa: E402


def load_terms(paths: list[Path]):
    terms = {}
    errors: list[str] = []
    for path in paths:
        value, raw = load(path)
        errors += [f"{path}: {error}" for error in validate_termbase_entry(value)]
        term_id = value.get("term_id")
        if term_id in terms:
            errors.append(f"duplicate loaded term_id {term_id}")
        terms[term_id] = (value, raw)
    return terms, errors


def build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command", required=True)
    pack = sub.add_parser("standard-pack"); pack.add_argument("path", type=Path)
    term = sub.add_parser("termbase"); term.add_argument("paths", nargs="+", type=Path)
    req = sub.add_parser("request"); req.add_argument("path", type=Path); req.add_argument("--standard-pack", required=True, type=Path); req.add_argument("--termbase", nargs="+", required=True, type=Path)
    vio = sub.add_parser("violation"); vio.add_argument("path", type=Path); vio.add_argument("--request", type=Path)
    rec = sub.add_parser("receipt"); rec.add_argument("path", type=Path); rec.add_argument("--request", required=True, type=Path); rec.add_argument("--standard-pack", required=True, type=Path); rec.add_argument("--termbase", nargs="+", required=True, type=Path)
    bundle = sub.add_parser("bundle"); bundle.add_argument("--request", required=True, type=Path); bundle.add_argument("--standard-pack", required=True, type=Path); bundle.add_argument("--termbase", nargs="+", required=True, type=Path); bundle.add_argument("--violation", type=Path); bundle.add_argument("--receipt", required=True, type=Path)
    return root


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "standard-pack":
            value, _ = load(args.path); return result(validate_standard_pack(value))
        if args.command == "termbase":
            _, errors = load_terms(args.paths); return result(errors)
        pack, pack_raw = load(args.standard_pack)
        errors = validate_standard_pack(pack)
        terms, term_errors = load_terms(args.termbase); errors += term_errors
        if args.command == "request":
            request, _ = load(args.path); errors += validate_request(request, pack, pack_raw, terms); return result(errors)
        request, request_raw = load(args.request); errors += validate_request(request, pack, pack_raw, terms)
        if args.command == "violation":
            violation, _ = load(args.path); errors += validate_violation(violation, request); return result(errors)
        if args.command == "receipt":
            receipt, _ = load(args.path); errors += validate_receipt(receipt, request, request_raw, pack, pack_raw, terms); return result(errors)
        if args.violation:
            violation, _ = load(args.violation); errors += validate_violation(violation, request)
        receipt, _ = load(args.receipt); errors += validate_receipt(receipt, request, request_raw, pack, pack_raw, terms)
        return result(errors)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"USAGE {exc}", file=sys.stderr); return 64
    except Exception as exc:  # pragma: no cover
        print(f"EVALUATOR {type(exc).__name__}: {exc}", file=sys.stderr); return 70


if __name__ == "__main__":
    raise SystemExit(main())
