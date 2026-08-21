#!/usr/bin/env python3
"""Replay every POL contract from the tree, not from a recorded result.

The wave that froze the four Stage-1 lane contracts verified their refusal
controls once, by hand, in a scratch validator — a one-time act, not a
standing gate. The Shadow readback on that wave named the gap: the next edit
to these schemas turns nothing red. This suite closes it the same way the
DTCR harness closed its own: every denominator is counted from the bytes at
run time, so a fifth lane schema joins the run without this file changing.

    schemas    every references/**/*.schema.json (core + lanes)
    positives  every in-schema `examples` entry
    controls   every in-schema `x-refusal-control`
    knockouts  one per control: remove exactly the keyword(s) its
               `refused_by` names, change nothing else, and require the
               instance to validate

Knockout granularity traps handled as in the DTCR suite: multi-keyword
`refused_by` ("A and B") removes every named path, and a guard reached via a
`not` key loses the whole not-clause, because `not: {}` refuses everything
and would falsely credit the guard.

Exit 0 green, 2 a control or count failed, 70 the validator is absent.
"""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - environment guard
    print(
        "POL-SELFTEST-UNUSABLE: jsonschema is required. This suite executes "
        "the committed schemas as deciding gates; skipping them would report "
        "the same green as running them.",
        file=sys.stderr,
    )
    raise SystemExit(70)

SKILL = Path(__file__).resolve().parents[1]
REFERENCES = SKILL / "references"


class Red(Exception):
    """A control failed. Carries the reason, never a bare status."""


def load_schemas() -> dict[str, tuple[Path, dict[str, Any]]]:
    files = sorted(REFERENCES.glob("**/*.schema.json"))
    if not files:
        raise Red(f"no schemas found under {REFERENCES}")
    schemas: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in files:
        document = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(document)
        identity = document.get("properties", {}).get("schema", {}).get("const")
        if not isinstance(identity, str):
            raise Red(f"{path.name}: no properties.schema.const, so nothing can name it")
        if identity in schemas:
            raise Red(f"two schemas claim the identity {identity}")
        schemas[identity] = (path, document)
    return schemas


def parse_keyword_path(path: str) -> list[str | int]:
    parts: list[str | int] = []
    for token in re.split(r"\.(?![^\[]*\])", path):
        while True:
            match = re.match(r"^([^\[]*)\[(\d+)\](.*)$", token)
            if not match:
                if token:
                    parts.append(token)
                break
            head, index, token = match.group(1), int(match.group(2)), match.group(3)
            if head:
                parts.append(head)
            parts.append(index)
    return parts


def remove_keyword(document: Any, path: str) -> None:
    parts = parse_keyword_path(path)
    node = document
    for part in parts[:-1]:
        node = node[part]
    leaf = parts[-1]
    # Removing `pattern` from inside a `not` leaves `not: {}`, which refuses
    # everything; the whole not-clause has to go for the knockout to mean
    # anything.
    if len(parts) >= 2 and parts[-2] == "not":
        grand = document
        for part in parts[:-2]:
            grand = grand[part]
        del grand["not"]
        return
    if isinstance(node, list):
        node.pop(leaf)
    else:
        del node[leaf]


def main() -> int:
    failures: list[str] = []
    schemas = load_schemas()
    positives = 0
    controls = 0
    knockouts = 0

    for identity, (path, document) in schemas.items():
        validator = Draft202012Validator(document)
        for index, example in enumerate(document.get("examples", [])):
            positives += 1
            errors = list(validator.iter_errors(example))
            if errors:
                failures.append(
                    f"positive {identity}#examples[{index}] rejected: {errors[0].message}"
                )
        for control in document.get("x-refusal-controls", []):
            controls += 1
            case = control.get("case_id", "<unnamed>")
            instance = control["instance"]
            if not list(validator.iter_errors(instance)):
                failures.append(f"control {case} is not refused by {identity} at all")
                continue
            mutated = copy.deepcopy(document)
            named = control["refused_by"]
            try:
                for keyword_path in re.split(r"\s+and\s+", named):
                    remove_keyword(mutated, keyword_path)
            except (KeyError, IndexError, TypeError):
                failures.append(f"control {case}: refused_by path {named!r} not found in schema")
                continue
            knockouts += 1
            if list(Draft202012Validator(mutated).iter_errors(instance)):
                failures.append(
                    f"control {case} is still refused after {named!r} was removed, "
                    f"so it does not discriminate the guard it names"
                )

    print(
        f"subject={REFERENCES} schemas={len(schemas)} positives={positives} "
        f"controls={controls} knockouts={knockouts}"
    )
    if failures:
        for item in failures:
            print(f"POL-SELFTEST-RED {item}", file=sys.stderr)
        return 2
    print(
        f"POL-SELFTEST-GREEN {positives} positive instances validate, "
        f"{controls} controls refused, {knockouts} of {controls} discriminating "
        f"under knockout of their own named keyword"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Red as red:
        print(f"POL-SELFTEST-RED {red}", file=sys.stderr)
        raise SystemExit(2)
