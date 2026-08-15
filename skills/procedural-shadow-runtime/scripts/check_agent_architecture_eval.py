#!/usr/bin/env python3
"""Deterministic checker for agent-architecture-eval/v1."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from agent_architecture_common import (
    ArchitectureContractError,
    parse,
    validate_architecture_receipt,
)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: check_agent_architecture_eval.py <receipt.json>", file=sys.stderr)
        return 64
    try:
        data = parse(Path(argv[1]))
    except RuntimeError as exc:
        print(f"INPUT FAIL: {exc}", file=sys.stderr)
        return 64
    try:
        result = validate_architecture_receipt(data)
    except ArchitectureContractError as exc:
        print(f"CONTRACT FAIL: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
