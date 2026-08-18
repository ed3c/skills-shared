#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CHECKER = ROOT / "scripts" / "check_case_graph.py"
GOOD = HERE / "fixtures" / "good.json"

spec = importlib.util.spec_from_file_location("case_graph_checker", CHECKER)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

base = json.loads(GOOD.read_text(encoding="utf-8"))


def expect_green(name: str, doc: dict) -> None:
    errors = mod.validate(doc)
    if errors:
        raise AssertionError(f"{name}: expected green, got {errors}")


def expect_red(name: str, doc: dict, needle: str) -> None:
    errors = mod.validate(doc)
    if not errors:
        raise AssertionError(f"{name}: expected red")
    joined = "\n".join(errors)
    if needle not in joined:
        raise AssertionError(f"{name}: expected {needle!r}; got {joined}")


expect_green("positive migration-copy graph", base)

# Orphan required case / missing implementation binding.
m = copy.deepcopy(base)
m["cases"][1]["implementation_ids"] = []
m["coverage"]["required_case"] = 0.5
m["coverage"]["implementation_binding"] = 0.5
m["gate"]["status"] = "READY_FOR_PROTOTYPE"
expect_red("orphan required case", m, "requires implementation_ids")

# Silent source-logic drop: compatibility remains modeled but source branch becomes unmapped.
m = copy.deepcopy(base)
m["source_behaviors"][1]["disposition"] = "UNMAPPED"
m["coverage"]["source_behavior_disposition"] = 0.5
m["gate"]["status"] = "READY_FOR_PROTOTYPE"
expect_red("silent semantic loss", m, "invalid/unmapped disposition")

# Intentional drop without authority decision.
m = copy.deepcopy(base)
m["source_behaviors"][1]["disposition"] = "DROP_EXPLICIT"
m["source_behaviors"][1]["decision_id"] = None
m["gate"]["status"] = "READY_FOR_PROTOTYPE"
expect_red("unauthorized drop", m, "requires decision_id")

# Missing semantic-parity oracle while compatibility lane remains green.
m = copy.deepcopy(base)
m["cases"][1]["oracle_ids"] = []
m["coverage"]["required_case"] = 0.5
m["coverage"]["oracle"] = 0.5
m["gate"]["status"] = "READY_FOR_PROTOTYPE"
expect_red("compatibility-only migration", m, "requires oracle_ids")

# Provenance cycle is forbidden even though runtime state machines may cycle.
m = copy.deepcopy(base)
m["edges"].append({"from": "EVID-002", "to": "INT-002", "kind": "INVALID_BACKEDGE"})
expect_red("provenance cycle", m, "contains a cycle")

# Unknown blocking case cannot be promoted by prose/coverage.
m = copy.deepcopy(base)
m["cases"].append({
    "id": "CASE-003",
    "classification": "UNKNOWN_BLOCKING",
    "intent_ids": ["INT-002"],
    "axis_ids": ["AXIS-002"],
    "invariant_or_state_refs": [],
    "implementation_ids": [],
    "oracle_ids": [],
    "decision_id": None,
    "evidence_state": "ABSENT"
})
m["coverage"]["unknown_blocking_count"] = 1
expect_red("unknown blocking promotion", m, "require gate BLOCKED")

# Coverage is recomputed; hidden denominator members cannot be ignored.
m = copy.deepcopy(base)
m["intent_atoms"].append({"id": "INT-003", "statement": "Preserve recovery semantics."})
expect_red("hidden intent denominator", m, "coverage.intent must be recomputed")

print("CASE-GRAPH-MUTATIONS-GREEN")
